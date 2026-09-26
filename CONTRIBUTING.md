# Contributing

Use Python 3.11 or later, a virtual environment, and `requirements-dev.txt`.
Run `python -m pytest -q`, `python -m phone_mcp.demo`, and `python scripts/make_demo_gif.py` before proposing a change.

Keep tests offline with an injected fake provider. Do not include credentials, real destination numbers, or runtime audit files. Add guard boundary tests when changing policy behavior. Explain any changed safety assumptions and update the README. Keep provider actions behind the interface and preserve the dry-run default.
