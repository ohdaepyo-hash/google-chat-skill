# google-chat-skill

> Send and receive Google Chat messages from [Claude Code](https://claude.com/claude-code) — **no OAuth consent flow, no dependencies.**

A Claude Code skill for Google Chat. **Sending** uses incoming webhooks — the
only credential is a webhook URL anyone in a space can create in 30 seconds,
with no Google Cloud project at all. **Receiving** uses service account app
authentication — still no OAuth consent screen, just a JSON key.

## Features

- ✅ **No OAuth anywhere** — sending needs only a webhook URL; receiving needs only a service account key
- ✅ **Zero dependencies** — Python 3.9+ standard library only (receiving signs its JWT with the `openssl` binary)
- ✅ **Text messages** with Google Chat markup (`*bold*`, `_italic_`, `` `code` ``, links, `<users/all>`)
- ✅ **Threads** — group related messages (e.g. CI builds) with a stable thread key
- ✅ **Cards** — full [cardsV2](https://developers.google.com/workspace/chat/api/reference/rest/v1/cards) support for rich notifications
- ✅ **Read messages** — list a space's recent messages as JSON lines or plain text
- ✅ **Works standalone** — `scripts/send.py` and `scripts/receive.py` are plain CLIs, usable without Claude

## Requirements

- A **Google Workspace** account (webhooks are not available on personal `@gmail.com` accounts)
- Python 3.9+
- Claude Code (optional — the script works on its own)

## Installation

### As a Claude Code skill (recommended)

```bash
# personal (all projects)
git clone https://github.com/ohdaepyo-hash/google-chat-skill.git ~/.claude/skills/google-chat

# or per-project
git clone https://github.com/ohdaepyo-hash/google-chat-skill.git .claude/skills/google-chat
```

### Standalone

```bash
git clone https://github.com/ohdaepyo-hash/google-chat-skill.git
```

## Setup: sending — get a webhook URL (one time, ~30 seconds)

1. In [Google Chat](https://chat.google.com), open the target **space**
2. Click the space name → **Apps & integrations** → **Webhooks** → **Add webhook**
3. Give it a name (e.g. `Claude`) and copy the generated URL
4. Export it — the URL contains a secret token, so keep it out of your code:

```bash
export GOOGLE_CHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/XXXX/messages?key=...&token=..."
```

Add that line to your `~/.bashrc` / `~/.zshrc` to make it permanent.

## Setup: receiving — service account (one time, ~10 minutes)

Google offers no credential-free read API, but app authentication avoids the
OAuth consent flow entirely. A Workspace admin is needed once:

1. Create a [Google Cloud project](https://console.cloud.google.com) and enable the **Google Chat API**
2. In **Google Chat API → Configuration**, set up the Chat app (name, avatar, status **Live**, visibility: your domain)
3. Create a **service account** and download its JSON key:

```bash
export GOOGLE_CHAT_SA_KEY_FILE="$HOME/.config/google-chat-skill/sa-key.json"
```

4. As Workspace admin, approve the `chat.app.messages.readonly` scope — [Set up app authorization for Chat](https://support.google.com/a/answer/15137461)
5. Add the Chat app to the target space (it can only read spaces it belongs to)

## Usage

### With Claude Code

Just ask in natural language — the skill triggers automatically:

> "Notify me on Google Chat when the tests pass"
> "Send the deploy result to Google Chat as a card"

### As a CLI

```bash
# text
python3 scripts/send.py --text "Deploy finished ✅"

# thread — same key = same thread
python3 scripts/send.py --text "build #124 passed" --thread-key ci-builds

# card (cardsV2 JSON file), --text becomes the notification fallback
python3 scripts/send.py --card-file card.json --text "Deploy: success"

# preview the request without sending
python3 scripts/send.py --text "hello" --dry-run

# read the latest 25 messages of a space (JSON lines)
python3 scripts/receive.py --space spaces/AAAA1234

# human-readable, only messages after a timestamp
python3 scripts/receive.py --space AAAA1234 --plain --since "2026-07-16T00:00:00Z"
```

Example `card.json`:

```json
{
  "cardsV2": [{
    "cardId": "status",
    "card": {
      "header": {"title": "Deploy", "subtitle": "production"},
      "sections": [{
        "widgets": [
          {"decoratedText": {"topLabel": "Status", "text": "<b>Success</b>"}},
          {"buttonList": {"buttons": [{"text": "Open logs", "onClick": {"openLink": {"url": "https://example.com/logs"}}}]}}
        ]
      }]
    }
  }]
}
```

## Text formatting cheatsheet

| Markup | Result |
|---|---|
| `*bold*` | **bold** |
| `_italic_` | *italic* |
| `~strike~` | ~~strike~~ |
| `` `code` `` | `code` |
| `<https://example.com\|label>` | link with label |
| `<users/all>` | notify everyone in the space |

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `error: set GOOGLE_CHAT_WEBHOOK_URL` | Export the env var or pass `--webhook-url` |
| HTTP 400 | Malformed card JSON — validate with `--dry-run` first |
| HTTP 403 / 404 | Webhook was deleted or the URL is truncated — regenerate it |
| HTTP 429 | Rate limit (~1 msg/sec per space) — back off and retry |
| Can't find the Webhooks menu | Personal `@gmail.com` account or a DM — webhooks need a Workspace **space** |
| `receive.py`: HTTP 403 | Scope not admin-approved yet, or the app isn't a member of the space |
| `receive.py`: HTTP 404 | Wrong space ID — copy it from the space URL (`.../space/AAAA1234`) |

## Limitations

- Workspace spaces only — no DMs, no personal `@gmail.com` accounts.
- Receiving returns **public space messages only** (no private messages) and
  needs the one-time admin approval above — that is Google's floor for
  reading; a fully credential-free read API does not exist.

## Development

```bash
python3 test_send.py      # webhook sender self-check, no network needed
python3 test_receive.py   # JWT/signature self-check, no network needed
```

## License

[MIT](LICENSE) © 2026 ohdaepyo
