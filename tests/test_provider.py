from types import SimpleNamespace
from unittest.mock import Mock

from phone_mcp.config import Settings
from phone_mcp.provider import TwilioProvider


def test_twilio_adapter(monkeypatch):
    client = Mock()
    monkeypatch.setattr('phone_mcp.provider.Client', lambda *args, **kwargs: client)
    provider = TwilioProvider(Settings(twilio_from_number='+12125550100'))
    client.calls.create.return_value.sid = 'CA'+'a'*32
    client.messages.create.return_value.sid = 'SM'+'b'*32
    assert provider.call('+12125550123', '<Response/>') == 'CA'+'a'*32
    client.calls.create.assert_called_once_with(to='+12125550123', from_='+12125550100', twiml='<Response/>')
    assert provider.sms('+12125550123', 'Hello') == 'SM'+'b'*32
    client.messages.create.assert_called_once_with(to='+12125550123', from_='+12125550100', body='Hello')
    record = SimpleNamespace(sid='CA'+'a'*32, status='completed', to='+12125550123')
    client.calls.return_value.fetch.return_value = record
    assert provider.status(record.sid) == {'sid':record.sid, 'status':'completed'}
    client.calls.list.return_value = [record]
    client.messages.list.return_value = [record]
    assert provider.calls(2) == [{'sid':record.sid, 'status':'completed'}]
    assert provider.messages(3) == [{'sid':record.sid, 'status':'completed'}]
    client.calls.list.assert_called_once_with(limit=2)
    client.messages.list.assert_called_once_with(limit=3)
