"""Offline configuration doctor. Never prints secrets or calls a provider."""

import importlib.metadata
import json
import sys
from zoneinfo import ZoneInfo

from .config import load_settings
from .guards import AREA_CODES, blocked
from .service import PhoneService


def main() -> int:
    checks = []
    try:
        settings = load_settings()
        for zones in AREA_CODES.values():
            for zone in zones:
                ZoneInfo(zone)
        service = PhoneService(settings)
        blocked(settings)
        service.audit.write('doctor', 'ok', service.clock())
        checks.append('Configuration, timezone data, blocklist, audit and state storage: OK')
        checks.append('Mode: ' + ('DRY_RUN' if settings.dry_run else 'LIVE'))
        if not settings.allowed_numbers:
            checks.append('WARN: allowlist is empty; all destinations denied')
        if not settings.mcp_http_token.get_secret_value() and not settings.oauth_issuer:
            checks.append('WARN: HTTP has no bearer token. Never expose it without auth.')
        if not settings.dry_run and not all([settings.twilio_account_sid.get_secret_value(),
                                            settings.twilio_auth_token.get_secret_value(), settings.twilio_from_number]):
            raise ValueError('Missing live configuration')
        checks.append('MCP SDK: ' + importlib.metadata.version('mcp'))
        print(json.dumps({'ok': True, 'checks': checks}, indent=2))
        return 0
    except Exception:
        print(json.dumps({'ok': False, 'checks': checks,
                          'error': 'Check policy/env values, live credentials, blocklist and writable storage. '
                                   'Secrets omitted. Missing a Twilio value? See docs/GET_YOUR_KEYS.md.'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
