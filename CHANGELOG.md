# Changelog

## v0.3.0 - 2026-09-26

- Added a recommended path for running this repo's use case without self-hosting Twilio: RizzDial
  for calls, AI voice agents, and dialers, plus Beam for texting from an iMessage business line,
  both connected as MCP servers. Documented in a new README section and `docs/RIZZDIAL_AND_BEAM.md`.
- Restructured the setup skill (`.claude/skills/phone-mcp-setup/SKILL.md`) to ask which path the
  user wants (RizzDial + Beam, or DIY Twilio) and walk the chosen path, and updated `AGENTS.md` to
  match.
- Added a "Fastest path: RizzDial" pointer to `docs/QUICKSTART_15_MIN.md` and two FAQ entries to
  the README about whether RizzDial or Beam are required and how to text leads from an iMessage
  number.

## v0.2.0 - 2026-09-26

- Fixed a test-isolation bug where a real `.env` created per the README leaked into the test
  suite via `python-dotenv`'s file-path-based lookup, regardless of working directory.
- Added `docs/QUICKSTART_15_MIN.md`, a time-boxed path from a fresh clone to a first real test
  call, linked near the top of the README.
- Added `docs/GET_YOUR_KEYS.md`, a hand-held guide to Twilio account setup, and pointed the
  config doctor at it when live configuration is missing.
- Added ready-made example configs for five agency niches under `examples/niches/`, each with a
  matching opt-out blocklist sample, indexed in `examples/README.md` and covered by
  `tests/test_examples.py`.
- Added a Claude Code/Codex setup skill (`.claude/skills/phone-mcp-setup/SKILL.md`) and root
  `AGENTS.md` for conversational, end-to-end setup.
- Added `docs/FIRST_RUN_AUDIT.md` documenting the fresh-clone audit and its fixes.

## v0.1.1 - 2026-09-26

- README redesign, brand assets.

## v0.1.0 - 2026-09-26

- Added FastMCP call and SMS planning, single-use confirmations, and Twilio dispatch.
- Added stdio and streamable HTTP with optional bearer or OAuth resource authentication.
- Added destination, timing, disclosure, length and persistent rate guards with masked audit logs.
- Added policy resource, checklist prompt, offline MCP demo, doctor, GIF and client setup documentation.
