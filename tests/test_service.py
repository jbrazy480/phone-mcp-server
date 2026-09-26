import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from xml.etree import ElementTree

import pytest

from phone_mcp.guards import GuardError

NUMBER = '+12125550123'


@pytest.mark.parametrize('kind', ['call', 'sms'])
@pytest.mark.parametrize('dry_run', [True, False])
def test_dry_run_and_live(factory, kind, dry_run):
    service, fake, _ = factory(dry_run=dry_run)
    plan = service.plan(kind, NUMBER, 'Hello <friend> & welcome')
    result = service.execute(kind, plan['confirmation_code'])
    assert result['dry_run'] is dry_run
    assert len(fake.requests) == (0 if dry_run else 1)
    if kind == 'call':
        xml = result['twiml'] if dry_run else fake.requests[0][2]
        say = ElementTree.fromstring(xml).find('Say')
        assert say.text == 'This is an automated call from your assistant. Hello <friend> & welcome'
        assert say.attrib['voice'] == 'alice'
    if not dry_run:
        assert result['call_sid' if kind == 'call' else 'message_sid'].startswith('CA' if kind == 'call' else 'SM')


def test_replay(factory):
    service, _, _ = factory()
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    service.execute('sms', code)
    with pytest.raises(GuardError, match='already used'):
        service.execute('sms', code)


@pytest.mark.parametrize('seconds,expired', [(299, False), (300, True), (301, True)])
def test_expiry(factory, seconds, expired):
    service, _, clock = factory()
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    clock[0] += timedelta(seconds=seconds)
    if expired:
        with pytest.raises(GuardError, match='expired'):
            service.execute('sms', code)
    else:
        assert service.execute('sms', code)['dry_run']


def test_payload_hash_binding(factory):
    service, fake, _ = factory()
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    pending = service.pending[code]
    service.pending[code] = replace(pending, payload=pending.payload.replace('Hello', 'Changed'))
    with pytest.raises(GuardError, match='hash mismatch'):
        service.execute('sms', code)
    assert not fake.requests


def test_action_binding(factory):
    service, _, _ = factory()
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    with pytest.raises(GuardError, match='different action'):
        service.execute('call', code)
    with pytest.raises(GuardError, match='already used'):
        service.execute('sms', code)


def test_mode_binding(factory):
    service, _, _ = factory()
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    service.settings = service.settings.model_copy(update={'dry_run': False})
    with pytest.raises(GuardError, match='different action or mode'):
        service.execute('sms', code)


def test_concurrent_confirmation(factory):
    service, fake, _ = factory(dry_run=False)
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    def execute():
        try:
            service.execute('sms', code)
            return True
        except GuardError:
            return False
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sum(pool.map(lambda _: execute(), range(4))) == 1
    assert len(fake.requests) == 1


def test_provider_error_is_sanitized_and_consumes_code(factory):
    service, fake, _ = factory(dry_run=False)
    fake.fail = True
    code = service.plan('call', NUMBER, 'Hello')['confirmation_code']
    with pytest.raises(GuardError, match='delivery may be unknown') as error:
        service.execute('call', code)
    assert NUMBER not in str(error.value)
    with pytest.raises(GuardError, match='already used'):
        service.execute('call', code)


def test_audit_masking(factory):
    service, _, _ = factory()
    code = service.plan('sms', NUMBER, 'PRIVATE BODY')['confirmation_code']
    service.execute('sms', code)
    with pytest.raises(GuardError):
        service.plan('sms', '+14155550123', 'PRIVATE BODY')
    with pytest.raises(GuardError):
        service.execute('call', 'SECRET_BAD_CODE')
    text = service.settings.audit_file.read_text()
    for secret in (NUMBER, '+14155550123', 'PRIVATE BODY', code, 'SECRET_BAD_CODE'):
        assert secret not in text
    records = [json.loads(line) for line in text.splitlines()]
    assert {r['event'] for r in records} == {'plan', 'execute'}
    assert records[0]['to'] == '***0123'
    assert any(r['outcome'] == 'rejected' for r in records)


def test_unwritable_audit_prevents_dispatch(factory, monkeypatch):
    service, fake, _ = factory(dry_run=False)
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    def fail(*args, **kwargs):
        raise OSError('disk full')
    monkeypatch.setattr(service.audit, 'write', fail)
    with pytest.raises(OSError):
        service.execute('sms', code)
    assert not fake.requests


@pytest.mark.parametrize('dry_run', [True, False])
def test_reads(factory, dry_run):
    service, fake, _ = factory(dry_run=dry_run)
    for kind in ('status', 'calls', 'messages'):
        assert service.read(kind, sid='CA'+'a'*32)['dry_run'] is dry_run
    assert len(fake.requests) == (0 if dry_run else 3)


@pytest.mark.parametrize('limit', [0, -1, 101])
def test_read_limit(factory, limit):
    service, _, _ = factory()
    with pytest.raises(GuardError, match='Limit'):
        service.read('calls', limit)


def test_bad_sid(factory):
    service, _, _ = factory()
    with pytest.raises(GuardError, match='SID'):
        service.read('status', sid='bad')


def test_live_requires_credentials(factory):
    service, _, _ = factory(dry_run=False)
    service._provider = None
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    with pytest.raises(GuardError, match='credentials'):
        service.execute('sms', code)
