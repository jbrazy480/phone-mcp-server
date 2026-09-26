"""python -m phone_mcp: stdio by default, HTTP on loopback when requested."""

import argparse
import logging

import uvicorn

from .config import load_settings
from .server import create_server, http_app
from .service import PhoneService


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--http', action='store_true')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    try:
        settings = load_settings()
        server = create_server(PhoneService(settings), args.port)
    except Exception:
        parser.exit(2, 'Configuration or storage initialization failed. Run python -m phone_mcp.check.\n')
    if args.http:
        token = settings.mcp_http_token.get_secret_value()
        if not token and not settings.oauth_issuer:
            logging.warning('HTTP has NO AUTH. Never expose it without auth. Listening on loopback only.')
        uvicorn.run(http_app(server, token), host='127.0.0.1', port=args.port, access_log=False)
    else:
        server.run(transport='stdio')


if __name__ == '__main__':
    main()
