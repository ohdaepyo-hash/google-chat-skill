# google-chat-skill

> Send messages to Google Chat from [Claude Code](https://claude.com/claude-code) — **no OAuth, no Google Cloud project, no dependencies.**

A Claude Code skill that posts text, threaded messages, and rich cards to
Google Chat spaces via **incoming webhooks**. The only credential you need is
a webhook URL that anyone in a space can create in 30 seconds.

## Features

- ✅ **Zero auth setup** — no OAuth flow, no service account, no GCP project
- ✅ **Zero dependencies** — Python 3.9+ standard library only
- ✅ **Text messages** with Google Chat markup (`*bold*`, `_italic_`, `` `code` ``, links, `<users/all>`)
- ✅ **Threads** — group related messages (e.g. CI builds) with a stable thread key
- ✅ **Cards** — full [cardsV2](https://developers.google.com/workspace/chat/api/reference/rest/v1/cards) support for rich notifications
- ✅ **Works standalone** — `scripts/send.py` is a plain CLI, usable without Claude

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

## Setup: get a webhook URL (one time, ~30 seconds)

1. In [Google Chat](https://chat.google.com), open the target **space**
2. Click the space name → **Apps & integrations** → **Webhooks** → **Add webhook**
3. Give it a name (e.g. `Claude`) and copy the generated URL
4. Export it — the URL contains a secret token, so keep it out of your code:

```bash
export GOOGLE_CHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/XXXX/messages?key=...&token=..."
```

Add that line to your `~/.bashrc` / `~/.zshrc` to make it permanent.

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

## Limitations

- **Send-only.** Reading messages requires the Chat API with OAuth or a service
  account, which this project deliberately avoids. If you need two-way
  integration, you need a full Chat app instead.
- Workspace spaces only — no DMs, no personal accounts.

## Development

```bash
python3 test_send.py   # self-check, no network needed
```

## License

[MIT](LICENSE) © 2026 ohdaepyo
