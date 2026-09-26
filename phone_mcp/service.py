"""Plan and execute exact payloads with single-use confirmation capabilities."""

import hashlib
import json
import re
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from twilio.twiml.voice_response import VoiceResponse

from .config import Settings
from .guards import GuardError, validate
from .provider import PhoneProvider, TwilioProvider
from .storage import Audit, RateLimit


@dataclass(frozen=True)
class Pending:
    payload: str
    digest: str
    expires: datetime


class PhoneService:
    def __init__(self, settings: Settings, provider: PhoneProvider | None = None,
                 clock: Callable[[], datetime] | None = None):
        self.settings = settings
        self._provider = provider
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.pending: dict[str, Pending] = {}
        self.lock = threading.RLock()
        self.audit = Audit(settings.audit_file)
        self.rate = RateLimit(settings.state_file, settings.max_per_hour)

    def provider(self) -> PhoneProvider:
        if self.settings.dry_run:
            raise GuardError("Provider unavailable in dry-run mode")
        if self._provider is None:
            s = self.settings
            if not (s.twilio_account_sid.get_secret_value() and s.twilio_auth_token.get_secret_value() and s.twilio_from_number):
                raise GuardError("Live mode requires Twilio credentials and sender number")
            self._provider = TwilioProvider(s)
        return self._provider

    def plan(self, kind: str, to: str, message: str, voice: str = "alice") -> dict:
        with self.lock:
            now = self.clock()
            try:
                spoken = f"This is an automated call from {self.settings.caller_name}. {message}" if kind == "call" else message
                if not message.strip():
                    raise GuardError("Message cannot be empty")
                validate(self.settings, kind, to, spoken, now, voice)
                self.rate.check(now)
                self.pending = {k: v for k, v in self.pending.items() if v.expires > now}
                if len(self.pending) >= 1000:
                    raise GuardError("Too many pending plans; wait for expiry")
                payload = json.dumps({"kind": kind, "to": to, "text": spoken, "voice": voice,
                                      "dry_run": self.settings.dry_run}, sort_keys=True)
                digest = hashlib.sha256(payload.encode()).hexdigest()
                code = secrets.token_hex(5).upper()
                while code in self.pending:
                    code = secrets.token_hex(5).upper()
                expires = now + timedelta(minutes=5)
                self.audit.write("plan", "accepted", now, to, kind)
                self.pending[code] = Pending(payload, digest, expires)
                return {"plan": f"{'DRY RUN' if self.settings.dry_run else 'LIVE'} {kind} to {to}: {spoken}",
                        "confirmation_code": code, "expires_at": expires.isoformat(), "payload_hash": digest,
                        "instruction": "Show the exact plan to the human. Execute only after explicit approval."}
            except GuardError:
                self.audit.write("plan", "rejected", now, to, kind)
                raise

    def execute(self, kind: str, code: str) -> dict:
        with self.lock:
            now, to = self.clock(), ""
            try:
                # Pop before validation: failed, expired, or wrong-tool attempts also consume codes.
                pending = self.pending.pop(code, None)
                if not pending or pending.expires <= now:
                    raise GuardError("Confirmation code invalid, expired, or already used")
                if not secrets.compare_digest(hashlib.sha256(pending.payload.encode()).hexdigest(), pending.digest):
                    raise GuardError("Confirmation payload hash mismatch")
                payload = json.loads(pending.payload)
                to = payload["to"]
                if payload["kind"] != kind or payload["dry_run"] != self.settings.dry_run:
                    raise GuardError("Confirmation is bound to a different action or mode")
                validate(self.settings, kind, to, payload["text"], now, payload["voice"])
                self.audit.write("execute", "attempt", now, to, kind)
                self.rate.check(now, reserve=True)
                response = VoiceResponse()
                if kind == "call":
                    response.say(payload["text"], voice=payload["voice"])
                if self.settings.dry_run:
                    result = {"dry_run": True, "to": to, "action": kind,
                              "twiml" if kind == "call" else "body": str(response) if kind == "call" else payload["text"]}
                else:
                    try:
                        sid = (self.provider().call(to, str(response)) if kind == "call"
                               else self.provider().sms(to, payload["text"]))
                    except GuardError:
                        raise
                    except Exception:
                        raise GuardError("Provider request failed; delivery may be unknown. Check Twilio before retrying.") from None
                    result = {"dry_run": False, "call_sid" if kind == "call" else "message_sid": sid}
                self.audit.write("execute", "dry_run" if self.settings.dry_run else "submitted", now, to, kind)
                return result
            except GuardError:
                self.audit.write("execute", "rejected_or_failed", now, to, kind)
                raise

    def read(self, kind: str, limit: int = 10, sid: str = "") -> dict:
        if not 1 <= limit <= 100:
            raise GuardError("Limit must be between 1 and 100")
        if kind == "status" and not re.fullmatch(r"CA[0-9a-fA-F]{32}", sid):
            raise GuardError("Invalid call SID")
        if self.settings.dry_run:
            return {"dry_run": True, "items": [], "note": "No Twilio request in dry-run mode"}
        try:
            provider = self.provider()
            return {"dry_run": False, "items": provider.status(sid) if kind == "status" else
                    provider.calls(limit) if kind == "calls" else provider.messages(limit)}
        except GuardError:
            raise
        except Exception:
            raise GuardError("Provider read failed; check credentials and connectivity") from None

    def policy(self) -> dict:
        return {"dry_run": self.settings.dry_run, "allowed_numbers": list(self.settings.allowed_numbers),
                "blocklist_file": str(self.settings.blocklist_file) if self.settings.blocklist_file else None,
                "max_per_hour": self.settings.max_per_hour, "max_message_length": self.settings.max_message_length,
                "calling_window": "08:00 inclusive to 21:00 exclusive in EVERY mapped recipient timezone",
                "unknown_area_codes": "Calls denied; map covers selected US geographic area codes",
                "sms_window": "No calling-window restriction for SMS",
                "disclosure": f"This is an automated call from {self.settings.caller_name}.",
                "confirmation": "Exact payload, single use, expires after 5 minutes; human approval required",
                "rate_scope": "Shared call/SMS attempts, including dry-run and provider failures; persistent SQLite",
                "audit": "Masked destinations; no bodies, codes, or credentials",
                "deployment": "Single owner; one server process; not a consent or legal compliance service"}
