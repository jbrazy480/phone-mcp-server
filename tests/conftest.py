"""All tests prohibit network connections and use temporary storage."""

import socket
from datetime import datetime, timezone

import pytest

from phone_mcp.config import Settings
from phone_mcp.service import PhoneService


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError('Network access forbidden in offline tests')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)


@pytest.fixture(autouse=True)
def no_real_dotenv(monkeypatch):
    """python-dotenv's load_dotenv() locates .env from this package's file path,
    not from cwd, so a real .env created next to a checkout (per the README) would
    otherwise leak into every test regardless of monkeypatch.chdir."""
    monkeypatch.setattr('phone_mcp.config.load_dotenv', lambda *args, **kwargs: False)


class FakeProvider:
    def __init__(self):
        self.requests = []
        self.fail = False

    def call(self, to, twiml):
        self.requests.append(('call', to, twiml))
        if self.fail:
            raise RuntimeError('sensitive +12125550123 provider error')
        return 'CA' + 'a'*32

    def sms(self, to, body):
        self.requests.append(('sms', to, body))
        return 'SM' + 'b'*32

    def status(self, sid):
        self.requests.append(('status', sid))
        return {'sid': sid, 'status': 'completed'}

    def calls(self, limit):
        self.requests.append(('calls', limit))
        return [{'sid': 'CA'+'a'*32, 'status': 'completed'}]

    def messages(self, limit):
        self.requests.append(('messages', limit))
        return [{'sid': 'SM'+'b'*32, 'status': 'delivered'}]


@pytest.fixture
def factory(tmp_path):
    def make(**overrides):
        config = {'allowed_numbers': ('+12125550123',), 'audit_file': tmp_path/'audit.jsonl',
                  'state_file': tmp_path/'state.sqlite3'}
        config.update(overrides)
        fake = FakeProvider()
        clock = [datetime(2026, 9, 26, 16, tzinfo=timezone.utc)]
        return PhoneService(Settings(**config), fake, lambda: clock[0]), fake, clock
    return make
