# Get your keys (DIY Twilio path)

For the recommended path, follow [RizzDial + Beam](RIZZDIAL_AND_BEAM.md). Twilio credentials are only for this repository's DIY server.

This server needs one thing before it can place a real call or send a real SMS: a Twilio
account. No OpenAI key is used by this server; your MCP client (Claude or ChatGPT) already
supplies the assistant, and this server only speaks a fixed script through Twilio.

If you only want the offline demo (`python -m phone_mcp.demo`) or the config doctor in dry-run
mode, you can skip this entire guide. Nothing here is needed until you set `DRY_RUN=false`.

## 1. Create a Twilio account

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio) and sign up.
2. Twilio starts you on a free trial. Trial accounts can only call or text phone numbers you
   have verified in the console, and outbound calls include a short trial message before your
   script. See [Twilio's trial account guide](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account)
   for exact current limits and how to verify a caller ID. For real pricing, see
   [Twilio's pricing page](https://www.twilio.com/en-us/pricing) rather than relying on any
   number quoted elsewhere.
3. In the console, verify your own phone number as a caller ID so you can safely test with it.

## 2. Buy a voice-capable phone number

1. In the [Twilio Console](https://console.twilio.com/), go to **Phone Numbers > Manage >
   Buy a number**.
2. Choose a number with **Voice** capability (and **SMS** if you also want to send texts).
3. Buy it. This is the number `TWILIO_FROM_NUMBER` will use to place calls and send messages.

## 3. Find your Account SID and Auth Token

1. Open the [Twilio Console dashboard](https://console.twilio.com/).
2. Your **Account SID** and **Auth Token** are shown near the top of that page. Click **View**
   to reveal the Auth Token.
3. Treat the Auth Token like a password. Never paste it into a chat with an AI assistant, a
   GitHub issue, or a public channel.

## 4. Put the values in `.env`

Copy `.env.example` to `.env` if you have not already, then edit `.env` directly in your editor
(never commit it, and never paste its contents into chat):

| Value from Twilio | `.env` variable |
| --- | --- |
| Account SID | `TWILIO_ACCOUNT_SID` |
| Auth Token | `TWILIO_AUTH_TOKEN` |
| The number you bought, in E.164 (for example `+15551234567`) | `TWILIO_FROM_NUMBER` |
| Your own verified phone number, in E.164 | `ALLOWED_NUMBERS` |

Leave `DRY_RUN=true` until you have run `python -m phone_mcp.check` successfully and are ready
for a real test call.

After changing configuration, restart any running MCP server/client connection so it reloads the values.

Environment variables and local `.env` values override YAML. Set `ALLOWED_NUMBERS` to your own test number and `CALLER_NAME` to your real business name there, or remove those entries so the policy values apply. Remove the blank `BLOCKLIST_FILE` entry to use the YAML blocklist, or set it to your actual blocklist path. Keep `DRY_RUN=true` until ready for the approved test.

## 5. Optional: a tunnel for remote MCP clients

You only need this if you are running the server in streamable HTTP mode for a remote client
such as ChatGPT. It is not required for Claude Desktop or Claude Code, which talk to the server
directly over stdio.

1. Install [ngrok](https://ngrok.com/download) (or [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
   as an alternative) and follow its own setup steps, including its account sign-in step.
2. Configure authentication as described below before starting the HTTP server with `python -m phone_mcp --http --port 8000`, then start the tunnel: `ngrok http 8000`.
3. Take the HTTPS URL ngrok prints, append `/mcp`, and set it as `MCP_PUBLIC_URL` in your local configuration. Restart the server to load it.
4. Set a bearer token in `MCP_HTTP_TOKEN` (generate one with
   `python -c 'import secrets; print(secrets.token_urlsafe(32))'`), or configure OAuth as
   described in the main [README](../README.md#chatgpt-remote-mcp-with-oauth). Never expose the
   HTTP server without one of these.

## Next step

Run `python -m phone_mcp.check`. If it reports `"ok": true`, continue with
[`QUICKSTART_15_MIN.md`](QUICKSTART_15_MIN.md) for your first real test call.
