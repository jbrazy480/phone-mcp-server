"""FastMCP registration and authenticated streamable HTTP application."""

import json
import secrets
from typing import Annotated
from urllib.parse import urlparse

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

from .service import PhoneService
from .oauth import JWTVerifier


class BearerAuth:
    """Authenticate every HTTP request, including session reconnects and deletes."""
    def __init__(self, app, token: str):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http' and self.token:
            headers = [v for k, v in scope['headers'] if k.lower() == b'authorization']
            expected = ('Bearer ' + self.token).encode()
            if len(headers) != 1 or not secrets.compare_digest(headers[0], expected):
                await JSONResponse({"error": "Bearer authentication required"}, status_code=401,
                                   headers={"WWW-Authenticate": "Bearer"})(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_server(service: PhoneService, port: int = 8000) -> FastMCP:
    hosts = ['127.0.0.1', 'localhost', '[::1]', '127.0.0.1:*', 'localhost:*', '[::1]:*']
    origins = ['http://127.0.0.1:*', 'http://localhost:*']
    public = service.settings.mcp_public_url
    if public:
        parsed = urlparse(public)
        if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
            raise ValueError("MCP_PUBLIC_URL must be an HTTPS URL")
        hosts.append(parsed.netloc)
        origins.append(f'https://{parsed.netloc}')
    oauth = {}
    if service.settings.oauth_issuer:
        oauth = {
            'auth': AuthSettings(issuer_url=service.settings.oauth_issuer,
                                 resource_server_url=public, required_scopes=['phone:use'],
                                 validate_token_resource=True),
            'token_verifier': JWTVerifier(service.settings.oauth_issuer, public, service.settings.oauth_jwks_url),
        }
    server = FastMCP('phone-mcp-server' , port=port, stateless_http=True, json_response=True, **oauth,
                     instructions='Show each exact plan and wait for human approval before execution. Never self-confirm.',
                     transport_security=TransportSecuritySettings(allowed_hosts=hosts, allowed_origins=origins))

    @server.tool()
    def plan_call(to: str, message_or_goal: str, voice: str = 'alice') -> dict:
        """Plan a spoken call. Text is spoken literally, not expanded into a conversation. Ask the human to approve."""
        return service.plan('call', to, message_or_goal, voice)

    @server.tool()
    def plan_sms(to: str, body: str) -> dict:
        """Plan an SMS and return a short code. Show the exact body and ask for approval."""
        return service.plan('sms', to, body)

    @server.tool()
    def place_call(confirmation_code: str) -> dict:
        """Execute the exact approved call plan once. Only after explicit human approval."""
        return service.execute('call', confirmation_code)

    @server.tool()
    def send_sms(confirmation_code: str) -> dict:
        """Execute the exact approved SMS plan once. Only after explicit human approval."""
        return service.execute('sms', confirmation_code)

    @server.tool()
    def get_call_status(call_sid: str) -> dict:
        """Read Twilio call status; dry-run never contacts Twilio."""
        return service.read('status', sid=call_sid)

    @server.tool()
    def list_recent_calls(limit: Annotated[int, Field(ge=1, le=100)] = 10) -> dict:
        """List recent account call SIDs and statuses without destination numbers."""
        return service.read('calls', limit)

    @server.tool()
    def list_recent_messages(limit: Annotated[int, Field(ge=1, le=100)] = 10) -> dict:
        """List recent account message SIDs and statuses without message bodies."""
        return service.read('messages', limit)

    @server.resource('phone://policy')
    def policy() -> str:
        """Active outbound guards and operating limitations."""
        return json.dumps(service.policy(), indent=2)

    @server.prompt()
    def outbound_call_checklist() -> str:
        """Human review checklist before any outbound call."""
        return ('Read phone://policy. Verify recipient consent, destination, local time, caller identity, '
                'and exact disclosed script. Call plan_call, show the entire plan, and wait for explicit '
                'human approval before place_call. Never invent approval or reuse a code. '
                'A goal is spoken verbatim; write the final script first.')

    return server


def http_app(server: FastMCP, token: str):
    app = server.streamable_http_app()
    app.user_middleware.insert(0, Middleware(BearerAuth, token=token))
    return app
