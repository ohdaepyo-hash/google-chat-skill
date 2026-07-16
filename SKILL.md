---
name: google-chat
description: Send messages, alerts, and card notifications to Google Chat spaces via incoming webhooks — no OAuth, no Google Cloud project required. Use when the user wants to post to Google Chat or send build/deploy/monitoring notifications to a Chat space.
---

# Google Chat (Webhook, No OAuth)

Send messages to a Google Chat space through an incoming webhook. No OAuth flow,
no Google Cloud project, no service account — just a webhook URL.

## Setup (one-time, done by the user)

1. In Google Chat, open the target space → click the space name → **Apps & integrations** → **Webhooks** → **Add webhook**.
2. Copy the webhook URL and export it as an environment variable:

```bash
export GOOGLE_CHAT_WEBHOOK_URL="https://chat.googleapis.com/v1/spaces/XXXX/messages?key=...&token=..."
```

The URL contains a secret token — never hardcode it in files or commit it.

## Send a text message

```bash
python3 scripts/send.py --text "Deploy finished ✅"
```

## Reply in a thread

A stable `--thread-key` groups messages into the same thread:

```bash
python3 scripts/send.py --text "build #124 passed" --thread-key ci-builds
```

## Send a card

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

## Text formatting

Google Chat webhook text supports: `*bold*`, `_italic_`, `~strike~`, `` `code` ``,
```` ```code block``` ````, `<https://url|link text>`, and `<users/all>` to notify everyone.

## Limits (be honest with the user about these)

- **Send-only.** Reading messages requires the Chat API with OAuth or a service account — out of scope for this skill.
- Webhooks are a **Google Workspace** feature: they work in spaces, not in DMs, and are not available on personal `@gmail.com` accounts.
- Quota is roughly 1 message/second per space; back off on HTTP 429.
