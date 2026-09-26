import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_stdio_entrypoint(tmp_path):
    env = dict(os.environ)
    for key in ('POLICY_FILE','OAUTH_ISSUER','OAUTH_JWKS_URL','MCP_PUBLIC_URL','BLOCKLIST_FILE'):
        env.pop(key, None)
    env.update(DRY_RUN='true', AUDIT_FILE=str(tmp_path/'audit.jsonl'),
               STATE_FILE=str(tmp_path/'state.sqlite3'))
    async with stdio_client(StdioServerParameters(command=sys.executable, args=['-m','phone_mcp'], env=env)) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            assert len((await client.list_tools()).tools) == 7
