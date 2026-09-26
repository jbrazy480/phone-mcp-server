"""Small injectable boundary around Twilio. No client exists in dry-run mode."""

from typing import Protocol

from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

from .config import Settings


class PhoneProvider(Protocol):
    def call(self, to: str, twiml: str) -> str: ...
    def sms(self, to: str, body: str) -> str: ...
    def status(self, sid: str) -> dict: ...
    def calls(self, limit: int) -> list[dict]: ...
    def messages(self, limit: int) -> list[dict]: ...


class TwilioProvider:
    def __init__(self, settings: Settings):
        self.sender = settings.twilio_from_number
        self.client = Client(settings.twilio_account_sid.get_secret_value(),
                             settings.twilio_auth_token.get_secret_value(),
                             http_client=TwilioHttpClient(timeout=15, max_retries=0))

    def call(self, to: str, twiml: str) -> str:
        return self.client.calls.create(to=to, from_=self.sender, twiml=twiml).sid

    def sms(self, to: str, body: str) -> str:
        return self.client.messages.create(to=to, from_=self.sender, body=body).sid

    def status(self, sid: str) -> dict:
        item = self.client.calls(sid).fetch()
        return {"sid": item.sid, "status": item.status}

    def calls(self, limit: int) -> list[dict]:
        return [{"sid": x.sid, "status": x.status} for x in self.client.calls.list(limit=limit)]

    def messages(self, limit: int) -> list[dict]:
        return [{"sid": x.sid, "status": x.status} for x in self.client.messages.list(limit=limit)]
