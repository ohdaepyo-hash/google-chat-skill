#!/usr/bin/env python3
"""List messages from a Google Chat space using a service account (app auth).

No OAuth consent flow and no pip dependencies: the RS256 JWT signature is
produced with the ubiquitous `openssl` binary, everything else is stdlib.

Requires a one-time setup (see SKILL.md): a Chat app + service account key,
the `chat.app.messages.readonly` scope approved by a Workspace admin, and the
app added to the target space. Returns public space messages only.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://oauth2.googleapis.com/token"
CHAT_API = "https://chat.googleapis.com/v1"
DEFAULT_SCOPE = "https://www.googleapis.com/auth/chat.app.messages.readonly"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign_rs256(data: bytes, private_key_pem: str) -> bytes:
    # ponytail: shell out to openssl instead of adding a crypto dependency
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
        f.write(private_key_pem)
        key_path = f.name
    try:
        return subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=data, capture_output=True, check=True,
        ).stdout
    finally:
        os.remove(key_path)


def build_jwt(key: dict, scope: str, now: int) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    claims = {
        "iss": key["client_email"],
        "scope": scope,
        "aud": key.get("token_uri", TOKEN_URL),
        "iat": now,
        "exp": now + 3600,
    }
    signing_input = (
        f"{b64url(json.dumps(header).encode())}.{b64url(json.dumps(claims).encode())}"
    )
    signature = sign_rs256(signing_input.encode(), key["private_key"])
    return f"{signing_input}.{b64url(signature)}"


def http_json(url: str, data: bytes | None = None, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"error: HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"error: {e.reason}")


def get_access_token(key: dict, scope: str) -> str:
    assertion = build_jwt(key, scope, int(time.time()))
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": assertion,
    }).encode()
    resp = http_json(
        key.get("token_uri", TOKEN_URL), data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return resp["access_token"]


def list_messages(token: str, space: str, limit: int, since: str | None) -> list[dict]:
    params = {"pageSize": min(limit, 1000), "orderBy": "createTime DESC"}
    if since:
        params["filter"] = f'createTime > "{since}"'
    messages, page_token = [], None
    while len(messages) < limit:
        if page_token:
            params["pageToken"] = page_token
        url = f"{CHAT_API}/{space}/messages?{urllib.parse.urlencode(params)}"
        resp = http_json(url, headers={"Authorization": f"Bearer {token}"})
        messages.extend(resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return messages[:limit]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--space", required=True, help='space ID, e.g. "spaces/AAAA1234" or "AAAA1234"')
    p.add_argument(
        "--key-file",
        default=os.environ.get("GOOGLE_CHAT_SA_KEY_FILE"),
        help="service account JSON key (default: $GOOGLE_CHAT_SA_KEY_FILE)",
    )
    p.add_argument("--limit", type=int, default=25, help="max messages to return (default: 25)")
    p.add_argument("--since", help='only messages after this RFC 3339 time, e.g. "2026-07-16T00:00:00Z"')
    p.add_argument("--scope", default=DEFAULT_SCOPE, help=f"OAuth scope (default: {DEFAULT_SCOPE})")
    p.add_argument("--plain", action="store_true", help="print 'time  sender: text' lines instead of JSON")
    args = p.parse_args()

    if not args.key_file:
        sys.exit("error: set GOOGLE_CHAT_SA_KEY_FILE or pass --key-file")
    with open(args.key_file, encoding="utf-8") as f:
        key = json.load(f)

    space = args.space if args.space.startswith("spaces/") else f"spaces/{args.space}"
    token = get_access_token(key, args.scope)
    messages = list_messages(token, space, args.limit, args.since)

    for m in messages:
        if args.plain:
            sender = m.get("sender", {}).get("name", "?")
            print(f"{m.get('createTime', '?')}  {sender}: {m.get('text', '')}")
        else:
            print(json.dumps(m, ensure_ascii=False))


if __name__ == "__main__":
    main()
