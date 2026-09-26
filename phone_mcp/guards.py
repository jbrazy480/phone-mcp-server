"""Pure outbound guards and bundled conservative timezone lookup."""

import json
from datetime import datetime
from importlib.resources import files
from zoneinfo import ZoneInfo

from .config import E164, Settings, patterns

AREA_CODES = json.loads(files("phone_mcp").joinpath("area_codes.json").read_text())


class GuardError(ValueError):
    """A safe, user-facing policy rejection."""


def matches(number: str, entries: tuple[str, ...] | list[str]) -> bool:
    return any(number.startswith(p[:-1]) if p.endswith('*') else number == p for p in entries)


def blocked(settings: Settings) -> list[str]:
    if settings.blocklist_file is None:
        return []
    try:
        entries = [line.split('#', 1)[0].strip() for line in settings.blocklist_file.read_text().splitlines()]
        return patterns([x for x in entries if x])
    except (OSError, ValueError):
        raise GuardError("Blocklist missing, unreadable, or invalid; outbound actions denied") from None


def validate(settings: Settings, kind: str, to: str, text: str, now: datetime, voice: str = "alice") -> None:
    if not E164.fullmatch(to):
        raise GuardError("Destination must be E.164, such as +12125550123")
    if not matches(to, settings.allowed_numbers):
        raise GuardError("Destination is not in allowlist")
    if matches(to, blocked(settings)):
        raise GuardError("Destination is blocked")
    if not text.strip() or len(text) > settings.max_message_length:
        raise GuardError("Message is empty or exceeds max_message_length (including disclosure)")
    if kind == "call":
        if voice not in {"alice", "man", "woman"}:
            raise GuardError("Voice must be alice, man, or woman")
        zones = AREA_CODES.get(to[2:5]) if to.startswith('+1') and len(to) == 12 else None
        if not zones:
            raise GuardError("No supported US area-code timezone; call denied")
        if any(not 8 <= now.astimezone(ZoneInfo(zone)).hour < 21 for zone in zones):
            raise GuardError("Outside calling window: all recipient zones must be within 08:00 to 21:00")
