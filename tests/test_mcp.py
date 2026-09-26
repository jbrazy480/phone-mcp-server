import json

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from phone_mcp.demo import run_demo
from phone_mcp.server import create_server, http_app


async def test_registration_and_schemas(factory):
    service, _, _ = factory()
    async with create_connected_server_and_client_session(create_server(service)) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        assert set(tools) == {'plan_call','plan_sms','place_call','send_sms','get_call_status','list_recent_calls','list_recent_messages'}
        assert tools['plan_call'].inputSchema['required'] == ['to','message_or_goal']
        assert tools['plan_call'].inputSchema['properties']['voice']['default'] == 'alice'
        assert tools['place_call'].inputSchema['required'] == ['confirmation_code']
        assert tools['list_recent_calls'].inputSchema['properties']['limit']['maximum'] == 100
        assert str((await client.list_resources()).resources[0].uri) == 'phone://policy'
        policy = await client.read_resource('phone://policy')
        assert json.loads(policy.contents[0].text)['dry_run']
        assert (await client.list_prompts()).prompts[0].name == 'outbound_call_checklist'
        assert 'explicit human approval' in (await client.get_prompt('outbound_call_checklist')).messages[0].content.text
        invalid = await client.call_tool('list_recent_calls', {'limit': 101})
        assert invalid.isError
        result = await client.call_tool('plan_sms', {'to': '+12125550123', 'body': 'Hello'})
        code = json.loads(result.content[0].text)['confirmation_code']
        assert not (await client.call_tool('send_sms', {'confirmation_code': code})).isError
        assert (await client.call_tool('send_sms', {'confirmation_code': code})).isError


@pytest.mark.parametrize('method', ['GET','POST','DELETE'])
@pytest.mark.parametrize('token', [None, 'Bearer wrong', 'Basic secret'])
async def test_http_auth_rejection(factory, method, token):
    service, _, _ = factory()
    app = http_app(create_server(service), 'secret')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
        response = await client.request(method, '/mcp', headers={'Authorization': token} if token else {})
        assert response.status_code == 401
        assert response.headers['www-authenticate'] == 'Bearer'


async def test_http_authenticated_initialize(factory):
    service, _, _ = factory()
    app = http_app(create_server(service), 'secret')
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as client:
            result = await client.post('/mcp', headers={'Authorization':'Bearer secret',
                                       'Accept':'application/json, text/event-stream'},
                                       json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{
                                           'protocolVersion':'2025-03-26','capabilities':{},
                                           'clientInfo':{'name':'test','version':'1'}}})
            assert result.status_code == 200
            assert result.json()['result']['serverInfo']['name'] == 'phone-mcp-server'


async def test_http_rebinding_rejection(factory):
    service, _, _ = factory()
    app = http_app(create_server(service), 'secret')
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://attacker.invalid') as client:
            result = await client.post('/mcp', headers={'Authorization':'Bearer secret'}, json={})
            assert result.status_code == 421


async def test_demo(capsys):
    await run_demo()
    output = capsys.readouterr().out
    for expected in ['PLAN CALL', 'PLAN SMS', 'CONFIRM', 'DRY RUN', 'GUARD REJECTION', 'no network']:
        assert expected in output
