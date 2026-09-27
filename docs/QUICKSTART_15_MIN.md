# Get results in 15 minutes

> **Recommended: RizzDial + Beam.** If you would rather not self-host Twilio, skip straight to
> [`RIZZDIAL_AND_BEAM.md`](RIZZDIAL_AND_BEAM.md) for managed AI voice agents and calling on
> RizzDial, plus texting from an iMessage business line on Beam. The steps below are the DIY
> Twilio path, and keep working as the self-hosted alternative.

This walks a first-time user from a fresh clone to one real phone call, placed to your own
phone, through Claude. No coding required, but you do need a terminal and a Twilio account
(consult Twilio for account requirements and charges).

Times are approximate and assume you already have Python 3.11+ and a terminal open.

## 1. Install (3 minutes)

```bash
git clone https://github.com/jbrazy480/phone-mcp-server.git
cd phone-mcp-server
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

**You should see** pip finish with no errors.

## 2. Prove it works offline, no keys (2 minutes)

```bash
python -m phone_mcp.demo
python -m phone_mcp.check
```

**You should see** a printed plan, confirmation, and dry-run result for a call and an SMS, a
guard rejection for a disallowed destination, and a doctor report ending in `"ok": true`. No
network request is made.

## 3. Get your Twilio keys (5 minutes)

Follow [`GET_YOUR_KEYS.md`](GET_YOUR_KEYS.md) to create a Twilio account, buy a voice number,
and find your Account SID and Auth Token. Keep that tab open; you will paste values into `.env`
in the next step, not into any chat.

**You should see** your Account SID, Auth Token, and a new phone number in the Twilio Console.

## 4. Configure your business and yourself as the test recipient (2 minutes)

Pick the [example config](../examples/README.md) closest to your business, or start from
`policy.example.yaml`. Copy it to `policy.yaml` at the repo root, then edit it:

```yaml
dry_run: true
allowed_numbers:
  - "+15551234567"   # replace with your own phone number, in E.164
caller_name: "Your Real Business Name"
```

Then copy `.env.example` to `.env` and edit it directly in your editor:

```bash
cp .env.example .env
```

```
TWILIO_ACCOUNT_SID=<paste from Twilio>
TWILIO_AUTH_TOKEN=<paste from Twilio>
TWILIO_FROM_NUMBER=<the number you bought, in E.164>
```

Environment variables and local `.env` values override YAML. Set `ALLOWED_NUMBERS` to your own test number and `CALLER_NAME` to your real business name there, or remove those entries so the policy values apply. Remove the blank `BLOCKLIST_FILE` entry to use the YAML blocklist, or set it to your actual blocklist path. Keep `DRY_RUN=true` until ready for the approved test.

**You should see** your own editor showing the values you just pasted; nothing is sent anywhere
yet.

## 5. Validate the live configuration (1 minute)

```bash
python -m phone_mcp.check
```

**You should see** `"ok": true` and `"Mode: DRY_RUN"`. If it fails, the error points at
[`GET_YOUR_KEYS.md`](GET_YOUR_KEYS.md).

## 6. Connect Claude Code (2 minutes)

```bash
python -m pip install -e .
claude mcp add phone -- python -m phone_mcp
```

**You should see** Claude Code confirm the `phone` MCP server was added. Open a Claude Code
session in this checkout and ask it to read `phone://policy`.

## 7. Place one real test call to yourself (2 minutes)

In `.env`, set `DRY_RUN=false`, then run `python -m phone_mcp.check` again and confirm
`"Mode: LIVE"`. Restart the MCP server/client connection so it reloads the configuration, then read `phone://policy` to confirm live mode and your allowed number. In Claude, ask it to plan a call to your own number with a short, real message,
for example: *"Plan a call to +15551234567 that says: This is a test call from my new AI
receptionist setup."*

1. Claude returns the exact spoken script and a one-time confirmation code. Read the script.
2. Approve it, and ask Claude to place the call using that code.

**You should see (and hear)**: if Twilio accepts and connects the call, your phone rings and the call opens with
the automated-call disclosure (`This is an automated call from ...`) followed by your message.
That is your first real outcome.

## What's next

- Add real numbers to `allowed_numbers` and to a blocklist file as people opt out.
- Read the [compliance note](../README.md#compliance-note-not-legal-advice) before contacting
  anyone other than yourself.
- Ask in the [Evolving AI Hub](https://www.skool.com/evolving-ai-hub?utm_source=github&utm_medium=readme&utm_campaign=phone-mcp-server&utm_content=community)
  if you get stuck, or use the [setup skill](../.claude/skills/phone-mcp-setup/SKILL.md) with
  Claude Code or Codex to walk through all of this conversationally.
