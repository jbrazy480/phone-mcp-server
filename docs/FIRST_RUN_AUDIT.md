# First-run audit

Performed by cloning the repo fresh, creating a new virtual environment, and following
`README.md` literally as a first-time, non-developer agency owner would, with no real API
keys and no real calls or SMS placed. Findings and fixes below.

## Findings

- [x] **Broken command (real bug): tests fail after following the README's own steps in order.**
  The Quickstart has the reader run `cp .env.example .env` before the Testing section runs
  `python -m pytest -q`. `python-dotenv`'s `load_dotenv()` locates `.env` by walking up from
  the *calling module's file path* (`phone_mcp/config.py`), not from the current working
  directory, so it always found the real repo `.env` regardless of `monkeypatch.chdir` in the
  tests. That leaked real values (for example `MAX_PER_HOUR=5`) into the test process and broke
  `tests/test_config.py::test_env_overrides_yaml`. Fixed by adding an autouse fixture in
  `tests/conftest.py` that stubs out `load_dotenv` during tests, so the suite is hermetic
  regardless of whether a real `.env` exists next to the checkout.
- [x] **Missing next step: no time-boxed path to a first real outcome.** The README's
  "Connect your MCP client" section leads with Claude Desktop JSON config, bearer tokens, and
  OAuth before the reader has done anything with their own phone. Added
  `docs/QUICKSTART_15_MIN.md`, linked near the top of the README, that sequences: offline demo,
  doctor, connect a client, then one real test call to your own phone.
- [x] **Missing prerequisite: no hand-held guide for getting Twilio credentials.** The README
  links to Twilio's docs but never walks through sign-up, trial number restrictions, verified
  caller IDs, or exactly where the Account SID and Auth Token live in the console. Added
  `docs/GET_YOUR_KEYS.md`, and the config doctor (`phone_mcp/check.py`) now points to it when
  live Twilio configuration is missing.
- [x] **Missing files: no ready-made starting point for common agency niches.** A first-time
  reader has to hand-write `policy.yaml` from scratch. Added `examples/niches/<niche>/` configs
  (med spa, home services, marketing agency, real estate, insurance) with a matching opt-out
  blocklist sample and an `examples/README.md` index, each validated by
  `tests/test_examples.py`.
- [x] **Missing onboarding path for agent-assisted setup.** Added
  `.claude/skills/phone-mcp-setup/SKILL.md` and root `AGENTS.md` so Claude Code or Codex can
  walk a non-developer through niche selection, key setup, and the first real test call without
  ever asking the user to paste secrets into chat.

## Not changed (working as intended)

- The config doctor's `WARN: allowlist is empty; all destinations denied` message before any
  `.env` exists is expected behavior (the default denies everything), not a bug.
- `python -m pip install -r requirements-dev.txt`, `python -m phone_mcp.demo`,
  `python -m phone_mcp.check`, `python -m pip install -e .`, and
  `python scripts/make_demo_gif.py` all ran without errors on a fresh Python 3.13 virtual
  environment.
