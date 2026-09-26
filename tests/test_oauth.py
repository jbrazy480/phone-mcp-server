from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from phone_mcp.oauth import JWTVerifier
from phone_mcp.server import create_server, http_app

ISSUER = 'https://auth.example.invalid/'
RESOURCE = 'https://phone.example.invalid/mcp'


@pytest.mark.parametrize('change,valid', [({},True), ({'aud':'wrong'},False), ({'iss':'wrong'},False),
                                          ({'exp':1},False), ({'sub':None},False)])
async def test_jwt_verification(monkeypatch, change, valid):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = JWTVerifier(ISSUER, RESOURCE, ISSUER+'jwks')
    monkeypatch.setattr(verifier.keys, 'get_signing_key_from_jwt', lambda token: SimpleNamespace(key=key.public_key()))
    claims = {'iss':ISSUER,'aud':RESOURCE,'sub':'owner','scope':'phone:use',
              'exp':int(datetime.now(timezone.utc).timestamp())+300}
    claims.update(change)
    token = jwt.encode(claims, key, algorithm='RS256')
    result = await verifier.verify_token(token)
    assert (result is not None) is valid
    if result:
        assert result.scopes == ['phone:use']


async def test_oauth_metadata_and_rejection(factory):
    service, _, _ = factory(oauth_issuer=ISSUER, oauth_jwks_url=ISSUER+'jwks', mcp_public_url=RESOURCE)
    app = http_app(create_server(service), '')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://phone.example.invalid') as client:
        result = await client.get('/mcp')
        assert result.status_code == 401
        assert 'resource_metadata=' in result.headers['www-authenticate']
        metadata = await client.get('/.well-known/oauth-protected-resource/mcp')
        assert metadata.status_code == 200
        assert metadata.json()['resource'] == RESOURCE
        assert metadata.json()['authorization_servers'] == [ISSUER]


@pytest.mark.parametrize('scope,status', [('phone:use',200), ('unrelated',403)])
async def test_oauth_http_scope(factory, monkeypatch, scope, status):
    from mcp.server.auth.provider import AccessToken
    service, _, _ = factory(oauth_issuer=ISSUER, oauth_jwks_url=ISSUER+'jwks', mcp_public_url=RESOURCE)
    async def verified(self, token):
        return AccessToken(token=token, client_id='owner', scopes=scope.split(), resource=RESOURCE,
                           expires_at=int(datetime.now(timezone.utc).timestamp())+300)
    monkeypatch.setattr(JWTVerifier, 'verify_token', verified)
    app = http_app(create_server(service), '')
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://phone.example.invalid') as client:
            response = await client.post('/mcp', headers={'Authorization':'Bearer test',
                                         'Accept':'application/json, text/event-stream'}, json={
                                             'jsonrpc':'2.0','id':1,'method':'initialize','params':{
                                                 'protocolVersion':'2025-03-26','capabilities':{},
                                                 'clientInfo':{'name':'test','version':'1'}}})
            assert response.status_code == status
