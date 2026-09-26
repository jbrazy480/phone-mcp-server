"""OAuth resource verification for an externally managed authorization server."""

import asyncio

import jwt
from mcp.server.auth.provider import AccessToken


class JWTVerifier:
    """Accept only signed, expiring RS256 tokens for this resource and issuer."""
    def __init__(self, issuer: str, audience: str, jwks_url: str):
        self.issuer, self.audience = issuer, audience
        self.keys = jwt.PyJWKClient(jwks_url, timeout=10)

    async def verify_token(self, token: str) -> AccessToken | None:
        def verify():
            key = self.keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=['RS256'], issuer=self.issuer,
                                audience=self.audience, options={'require': ['exp', 'iss', 'aud', 'sub']})
            return AccessToken(token=token, client_id=claims.get('client_id', claims['sub']),
                               subject=claims['sub'], scopes=claims.get('scope', '').split(),
                               expires_at=int(claims['exp']), resource=self.audience)
        try:
            return await asyncio.to_thread(verify)
        except Exception:
            return None
