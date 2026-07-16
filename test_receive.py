#!/usr/bin/env python3
"""Self-check for scripts/receive.py: JWT construction + RS256 signature (no network)."""
import base64
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import receive  # noqa: E402


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


with tempfile.TemporaryDirectory() as tmp:
    priv = os.path.join(tmp, "priv.pem")
    pub = os.path.join(tmp, "pub.pem")
    subprocess.run(["openssl", "genrsa", "-out", priv, "2048"], check=True, capture_output=True)
    subprocess.run(["openssl", "rsa", "-in", priv, "-pubout", "-out", pub], check=True, capture_output=True)

    key = {
        "client_email": "bot@example.iam.gserviceaccount.com",
        "private_key": open(priv, encoding="utf-8").read(),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    jwt = receive.build_jwt(key, receive.DEFAULT_SCOPE, now=1_750_000_000)
    header_b64, claims_b64, sig_b64 = jwt.split(".")

    assert json.loads(b64url_decode(header_b64)) == {"alg": "RS256", "typ": "JWT"}
    claims = json.loads(b64url_decode(claims_b64))
    assert claims["iss"] == key["client_email"]
    assert claims["scope"] == receive.DEFAULT_SCOPE
    assert claims["exp"] - claims["iat"] == 3600

    # verify the signature with the public key
    sig_file = os.path.join(tmp, "sig.bin")
    with open(sig_file, "wb") as f:
        f.write(b64url_decode(sig_b64))
    r = subprocess.run(
        ["openssl", "dgst", "-sha256", "-verify", pub, "-signature", sig_file],
        input=f"{header_b64}.{claims_b64}".encode(), capture_output=True,
    )
    assert r.returncode == 0 and b"Verified OK" in r.stdout, r.stdout + r.stderr

# CLI arg validation fails loudly without a key file
r = subprocess.run(
    [sys.executable, os.path.join(HERE, "scripts", "receive.py"), "--space", "AAAA"],
    capture_output=True, text=True, env={**os.environ, "GOOGLE_CHAT_SA_KEY_FILE": ""},
)
assert r.returncode != 0 and "key-file" in r.stderr

print("ok")
