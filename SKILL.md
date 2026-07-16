---
name: google-chat
description: Send and receive Google Chat messages without an OAuth consent flow. Sending uses incoming webhooks (no credentials beyond a webhook URL); receiving uses a service account with app authentication. Use when the user wants to post to Google Chat, send build/deploy/monitoring notifications, or read recent messages from a Chat space.
---

# Google Chat (No OAuth)

Send messages to a Google Chat space through an incoming webhook, and read
messages back with a service account — no OAuth consent flow anywhere.

## Sending

### Setup (one-time, done by the user)

1. In Google Chat, open the target space → click the space name → **Apps & integrations** → **Webhooks** → **Add webhook**.
2. Copy the webhook URL and export it as an environment variable:

```bash
export GOOGLE_CHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/XXXX/messages?key=...&token=..."
```

The URL contains a secret token — never hardcode it in files or commit it.

### Send a text message

```bash
python3 scripts/send.py --text "Deploy finished ✅"
```

### Reply in a thread

A stable `--thread-key` groups messages into the same thread:

```bash
python3 scripts/send.py --text "build #124 passed" --thread-key ci-builds
```

### Send a card

Write a [cardsV2](https://developers.google.com/workspace/chat/api/reference/rest/v1/cards) payload to a JSON file and:

```bash
python3 scripts/send.py --card-file card.json --text "fallback text"
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

### Text formatting

Google Chat webhook text supports: `*bold*`, `_italic_`, `~strike~`, `` `code` ``,
```` ```code block``` ````, `<https://url|link text>`, and `<users/all>` to notify everyone.

## Receiving

Reading messages has no fully credential-free path — Google requires it — but
it works **without any OAuth consent flow** via service account app
authentication. Zero pip dependencies: the JWT is signed with the `openssl`
binary.

### Setup (one-time, done by the user — needs Workspace admin, ~10 minutes)

1. Create a [Google Cloud project](https://console.cloud.google.com) and enable the **Google Chat API**.
2. In **Google Chat API → Configuration**, set up the Chat app (name, avatar, description; app status **Live**; visibility: your domain).
3. Create a **service account** in the project and download its JSON key. Store it outside the repo:

```bash
export GOOGLE_CHAT_SA_KEY_FILE="$HOME/.config/google-chat-skill/sa-key.json"
```

4. As Workspace admin, approve the app's `chat.app.messages.readonly` scope — see [Set up app authorization for Chat](https://support.google.com/a/answer/15137461).
5. In Google Chat, **add the Chat app to the target space** (the app can only read spaces it is a member of).

### Read messages

```bash
# latest 25 messages as JSON lines
python3 scripts/receive.py --space spaces/AAAA1234

# human-readable, only messages after a timestamp
python3 scripts/receive.py --space AAAA1234 --plain --since "2026-07-16T00:00:00Z" --limit 50
```

The space ID is in the space's URL: `https://mail.google.com/chat/u/0/#chat/space/AAAA1234`.

## Limits (be honest with the user about these)

- Webhooks and the Chat API are **Google Workspace** features: spaces only, not DMs, not available on personal `@gmail.com` accounts.
- Receiving returns **public space messages only** (no private messages) and requires the one-time admin approval above — that is Google's floor for reading; there is no credential-free read API.
- Send quota is roughly 1 message/second per space; back off on HTTP 429.
