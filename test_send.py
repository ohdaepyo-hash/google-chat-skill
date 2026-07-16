#!/usr/bin/env python3
"""Self-check for scripts/send.py using --dry-run (no network)."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEND = os.path.join(HERE, "scripts", "send.py")
URL = "https://chat.example/v1/spaces/X/messages?key=k&token=t"


def run(*args, env_url=None):
    env = {**os.environ}
    env.pop("GOOGLE_CHAT_WEBHOOK_URL", None)
    if env_url:
        env["GOOGLE_CHAT_WEBHOOK_URL"] = env_url
    return subprocess.run(
        [sys.executable, SEND, *args], capture_output=True, text=True, env=env
    )


# text message + thread key
r = run("--text", "안녕 *world*", "--thread-key", "ci/1", "--webhook-url", URL, "--dry-run")
assert r.returncode == 0, r.stderr
post_line, payload_json = r.stdout.split("\n", 1)
assert "threadKey=ci%2F1" in post_line
assert "messageReplyOption=REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD" in post_line
assert json.loads(payload_json) == {"text": "안녕 *world*"}

# webhook URL from env
r = run("--text", "hi", "--dry-run", env_url=URL)
assert r.returncode == 0, r.stderr

# missing URL and missing content both fail loudly
assert run("--text", "hi", "--dry-run").returncode != 0
assert run("--webhook-url", URL, "--dry-run").returncode != 0

# card file merges with fallback text
card_path = os.path.join(HERE, ".test_card.json")
with open(card_path, "w", encoding="utf-8") as f:
    json.dump({"cardsV2": [{"cardId": "c1", "card": {}}]}, f)
try:
    r = run("--card-file", card_path, "--text", "fb", "--webhook-url", URL, "--dry-run")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout.split("\n", 1)[1])
    assert payload["text"] == "fb" and payload["cardsV2"][0]["cardId"] == "c1"
finally:
    os.remove(card_path)

print("ok")
