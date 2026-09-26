from datetime import datetime, timedelta, timezone

import pytest

from phone_mcp.guards import GuardError

NUMBER = '+12125550123'


@pytest.mark.parametrize('number', ['2125550123', '+0123456789', '+1 2125550123', '+12125550123\n', '+123', '+１２１２５５５０１２３'])
def test_e164(factory, number):
    service, _, _ = factory()
    with pytest.raises(GuardError, match='E.164'):
        service.plan('sms', number, 'Hello')


def test_empty_allowlist(factory):
    service, _, _ = factory(allowed_numbers=())
    with pytest.raises(GuardError, match='allowlist'):
        service.plan('sms', NUMBER, 'Hello')


def test_exact_allowlist(factory):
    service, _, _ = factory()
    with pytest.raises(GuardError, match='allowlist'):
        service.plan('sms', '+12125550124', 'Hello')


def test_prefix_allowlist(factory):
    service, _, _ = factory(allowed_numbers=('+1212*',))
    assert service.plan('sms', NUMBER, 'Hello')


@pytest.mark.parametrize('entry', [NUMBER, '+1212*'])
def test_blocklist_precedence(factory, tmp_path, entry):
    path = tmp_path/'blocked.txt'
    path.write_text('# deny list\n'+entry+' # opted out\n')
    service, _, _ = factory(blocklist_file=path)
    with pytest.raises(GuardError, match='blocked'):
        service.plan('sms', NUMBER, 'Hello')


@pytest.mark.parametrize('content', [None, 'invalid'])
def test_blocklist_fail_closed(factory, tmp_path, content):
    path = tmp_path/'blocked.txt'
    if content:
        path.write_text(content)
    service, _, _ = factory(blocklist_file=path)
    with pytest.raises(GuardError, match='Blocklist'):
        service.plan('sms', NUMBER, 'Hello')


def test_blocklist_rechecked_on_execute(factory, tmp_path):
    path = tmp_path/'blocked.txt'
    path.write_text('')
    service, fake, _ = factory(blocklist_file=path)
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    path.write_text(NUMBER)
    with pytest.raises(GuardError, match='blocked'):
        service.execute('sms', code)
    assert not fake.requests


@pytest.mark.parametrize('hour,minute,allowed', [(11,59,False),(12,0,True),(0,59,True),(1,0,False)])
def test_call_window_boundaries(factory, hour, minute, allowed):
    service, _, clock = factory()
    clock[0] = datetime(2026,9,26,hour,minute,tzinfo=timezone.utc)
    if allowed:
        assert service.plan('call', NUMBER, 'Hello')
    else:
        with pytest.raises(GuardError, match='calling window'):
            service.plan('call', NUMBER, 'Hello')


@pytest.mark.parametrize('month,hour,allowed', [(1,12,False),(1,13,True),(7,12,True)])
def test_dst(factory, month, hour, allowed):
    service, _, clock = factory()
    clock[0] = datetime(2026,month,15,hour,tzinfo=timezone.utc)
    if allowed:
        assert service.plan('call', NUMBER, 'Hello')
    else:
        with pytest.raises(GuardError, match='calling window'):
            service.plan('call', NUMBER, 'Hello')


@pytest.mark.parametrize('hour,allowed', [(14,False),(15,True),(3,False)])
def test_multizone_most_restrictive(factory, hour, allowed):
    service, _, clock = factory(allowed_numbers=('+12085550123',))
    clock[0] = datetime(2026,9,26,hour,tzinfo=timezone.utc)
    if allowed:
        assert service.plan('call', '+12085550123', 'Hello')
    else:
        with pytest.raises(GuardError, match='calling window'):
            service.plan('call', '+12085550123', 'Hello')


@pytest.mark.parametrize('number', ['+18005550123', '+442079460123', '+19995550123'])
def test_unknown_timezone(factory, number):
    service, _, _ = factory(allowed_numbers=(number,))
    with pytest.raises(GuardError, match='timezone'):
        service.plan('call', number, 'Hello')


def test_execution_rechecks_window(factory):
    service, _, clock = factory()
    clock[0] = datetime(2026,9,26,0,59,tzinfo=timezone.utc)
    code = service.plan('call', NUMBER, 'Hello')['confirmation_code']
    clock[0] += timedelta(minutes=1)
    with pytest.raises(GuardError, match='calling window'):
        service.execute('call', code)


@pytest.mark.parametrize('kind,body', [('sms',''),('sms',' '*3),('sms','x'*101),('call','x'*80)])
def test_message_length_includes_disclosure(factory, kind, body):
    service, _, _ = factory(max_message_length=100)
    with pytest.raises(GuardError, match='empty|length'):
        service.plan(kind, NUMBER, body)


def test_voice(factory):
    service, _, _ = factory()
    with pytest.raises(GuardError, match='Voice'):
        service.plan('call', NUMBER, 'Hello', 'invalid')


def test_rate_limit_persistent_and_rolling(factory):
    service, _, clock = factory(max_per_hour=1)
    code = service.plan('sms', NUMBER, 'Hello')['confirmation_code']
    service.execute('sms', code)
    restarted, _, _ = factory(max_per_hour=1)
    with pytest.raises(GuardError, match='rate limit'):
        restarted.plan('call', NUMBER, 'Hello')
    clock[0] += timedelta(hours=1)
    assert service.plan('sms', NUMBER, 'Hello')


def test_execute_rate_limit(factory):
    service, fake, _ = factory(max_per_hour=1, dry_run=False)
    codes = [service.plan('sms', NUMBER, 'Hello')['confirmation_code'] for _ in range(2)]
    service.execute('sms', codes[0])
    with pytest.raises(GuardError, match='rate limit'):
        service.execute('sms', codes[1])
    assert len(fake.requests) == 1
