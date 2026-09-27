# Example niche configs

These examples support the DIY path. For the recommended commercial platform path, start with [RizzDial + Beam](../docs/RIZZDIAL_AND_BEAM.md). These files are not platform import instructions.

Ready-made `policy.yaml` starting points for common agency niches. Every business name,
phone number, and domain below is fictional. Phone numbers use the NANP reserved
555-01xx test block, so they cannot dial a real destination even if you skip the edit step.

Each config is dry-run by default, includes a matching opt-out blocklist sample, and validates
offline with the config doctor, no Twilio or OpenAI account required.

| Niche | Folder | Example business | Try it |
| --- | --- | --- | --- |
| Med spa | [`med-spa/`](niches/med-spa/) | Example Glow Med Spa | `POLICY_FILE=examples/niches/med-spa/policy.yaml python -m phone_mcp.check` |
| Home services | [`home-services/`](niches/home-services/) | Example Reliable Home Services | `POLICY_FILE=examples/niches/home-services/policy.yaml python -m phone_mcp.check` |
| Marketing agency | [`marketing-agency/`](niches/marketing-agency/) | Example North Star Marketing | `POLICY_FILE=examples/niches/marketing-agency/policy.yaml python -m phone_mcp.check` |
| Real estate | [`real-estate/`](niches/real-estate/) | Example Summit Realty Group | `POLICY_FILE=examples/niches/real-estate/policy.yaml python -m phone_mcp.check` |
| Insurance | [`insurance/`](niches/insurance/) | Example Harbor Point Insurance | `POLICY_FILE=examples/niches/insurance/policy.yaml python -m phone_mcp.check` |

Run the command from the repo root so the relative `blocklist_file` path in each config
resolves correctly.

## Using one for your own business

1. Copy the folder closest to your niche, or copy just its `policy.yaml` to `policy.yaml` at
   the repo root.
2. Replace `allowed_numbers` with your own phone number in E.164 (for example `+15551234567`),
   and update `caller_name` to your real business name. The disclosure line
   (`This is an automated call from ...`) always uses this name, so it must be accurate.
3. Add any number that has opted out to the matching `blocklist.example.txt` (or your own
   `BLOCKLIST_FILE`) before you ever dial it.
4. Run `python -m phone_mcp.check` to validate, then follow
   [`../docs/QUICKSTART_15_MIN.md`](../docs/QUICKSTART_15_MIN.md) for a first real test call to
   your own phone.

Environment variables and local `.env` values override YAML. Set `ALLOWED_NUMBERS` to your own test number and `CALLER_NAME` to your real business name there, or remove those entries so the policy values apply. Remove the blank `BLOCKLIST_FILE` entry to use the YAML blocklist, or set it to your actual blocklist path. Keep `DRY_RUN=true` until ready for the approved test.

These configs only set safe defaults. They do not collect consent, disclose AI use on your
behalf beyond the built-in automated-call disclosure, or check calling regulations for you.
See the [compliance note](../README.md#compliance-note-not-legal-advice) before contacting any
real person.
