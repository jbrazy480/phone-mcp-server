"""Deterministic offline demo over a real in-memory MCP client session."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp.shared.memory import create_connected_server_and_client_session

from .config import Settings
from .server import create_server
from .service import PhoneService


async def run_demo() -> None:
    logging.getLogger('mcp').setLevel(logging.CRITICAL)
    with TemporaryDirectory() as directory:
        settings = Settings(allowed_numbers=('+12125550123',), caller_name='the offline demo',
                            audit_file=Path(directory)/'audit.jsonl', state_file=Path(directory)/'rate.sqlite3')
        service = PhoneService(settings, clock=lambda: datetime(2026, 9, 26, 16, tzinfo=timezone.utc))
        async with create_connected_server_and_client_session(create_server(service)) as client:
            print('PHONE MCP | offline demo | DRY_RUN=true')
            print('MCP client connected. Demo clock: 2026-09-26 16:00 UTC.')
            for kind, tool, args, execute in [
                ('CALL', 'plan_call', {'to': '+12125550123', 'message_or_goal': 'Your appointment is tomorrow.'}, 'place_call'),
                ('SMS', 'plan_sms', {'to': '+12125550123', 'body': 'Your appointment is tomorrow.'}, 'send_sms'),
            ]:
                result = await client.call_tool(tool, args)
                assert not result.isError
                plan = json.loads(result.content[0].text)
                print(f'\nPLAN {kind}: {plan["plan"]}')
                print('CONFIRM: simulated human approves exact plan with its one-time code.')
                outcome = await client.call_tool(execute, {'confirmation_code': plan['confirmation_code']})
                assert not outcome.isError
                data = json.loads(outcome.content[0].text)
                assert data['dry_run']
                print(f'RESULT: DRY RUN {data["action"]}; no Twilio request.')
                print('PAYLOAD: ' + data.get('twiml', data.get('body', '')))
            rejected = await client.call_tool('plan_sms', {'to': '+14155550123', 'body': 'Hello'})
            assert rejected.isError
            print('\nGUARD REJECTION: destination is not in allowlist.')
            print('Done. No keys, no network, no real calls or SMS.')


def main() -> None:
    asyncio.run(run_demo())


if __name__ == '__main__':
    main()
