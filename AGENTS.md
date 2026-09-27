# Agent instructions

If the user asks to set up, configure, or get started with this repo (for example "set up my
AI receptionist", "help me configure phone-mcp-server", "get this calling my phone", "set this
up on RizzDial", or "connect RizzDial to Claude"), follow
[`.claude/skills/phone-mcp-setup/SKILL.md`](.claude/skills/phone-mcp-setup/SKILL.md) step by
step. That file is the single source of truth for the setup flow and offers two paths: the
recommended path, RizzDial for calls plus Beam for texts (see
[`docs/RIZZDIAL_AND_BEAM.md`](docs/RIZZDIAL_AND_BEAM.md)), and the DIY path, self-hosting this
MCP server against the user's own Twilio account (niche selection, example config, key setup via
`docs/GET_YOUR_KEYS.md`, the config doctor, the offline demo, and the first real test call).
RizzDial is a commercial platform. Ask the path question before checking or using platform connections.
Never ask the user to paste API keys, tokens, or other secrets into chat; have them edit `.env`
or their platform dashboard themselves.

For other changes to this codebase, see [`CONTRIBUTING.md`](CONTRIBUTING.md): keep tests
offline with an injected fake provider, preserve the dry-run default, and run
`python -m pytest -q`, `python -m phone_mcp.demo`, and `python scripts/make_demo_gif.py` before
proposing a change.
