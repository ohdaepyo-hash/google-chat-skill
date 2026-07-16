#!/usr/bin/env python3
"""Send a message to a Google Chat space via incoming webhook (no OAuth).

Stdlib only. Webhook URL comes from --webhook-url or GOOGLE_CHAT_WEBHOOK_URL.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def build_url(webhook_url: str, thread_key: str | None) -> str:
    if not thread_key:
        return webhook_url
    sep = "&" if "?" in webhook_url else "?"
    return (
        f"{webhook_url}{sep}threadKey={urllib.parse.quote(thread_key, safe='')}"
        "&messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD"
    )


def build_payload(text: str | None, card_file: str | None) -> dict:
    payload = {}
    if card_file:
        with open(card_file, encoding="utf-8") as f:
            payload = json.load(f)
    if text:
        payload["text"] = text
    return payload


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--text", help="message text (Google Chat simple markup allowed)")
    p.add_argument("--card-file", help="path to a JSON file with a cardsV2 payload")
    p.add_argument("--thread-key", help="stable key to group messages into one thread")
    p.add_argument(
        "--webhook-url",
        default=os.environ.get("GOOGLE_CHAT_WEBHOOK_URL"),
        help="webhook URL (default: $GOOGLE_CHAT_WEBHOOK_URL)",
    )
    p.add_argument("--dry-run", action="store_true", help="print request instead of sending")
    args = p.parse_args()

    if not args.webhook_url:
        sys.exit("error: set GOOGLE_CHAT_WEBHOOK_URL or pass --webhook-url")
    if not args.text and not args.card_file:
        sys.exit("error: --text or --card-file is required")

    url = build_url(args.webhook_url, args.thread_key)
    payload = build_payload(args.text, args.card_file)

    if args.dry_run:
        print(f"POST {url}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=UTF-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"error: HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"error: {e.reason}")


if __name__ == "__main__":
    main()
