"""Get and keep a Doctavian bearer token.

Doctavian needs two credentials on every call: the `x-api-key` (long-lived, from the
portal) and an OAuth bearer for the signed-in user. The bearer expires in about an
hour, and the previous run stored only the access token — so it went stale and cost a
browser round trip to notice. This keeps the refresh token too, and refreshes silently
from then on.

    python -m before.doctavian_auth --url          # print the sign-in URL
    python -m before.doctavian_auth --code "<redirect url or code>"
    python -m before.doctavian_auth --token        # a valid bearer, refreshing if needed
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".cache" / "doctavian" / "oauth.json"

TENANT = "consumers"
CLIENT_ID = "11e71170-3499-43f3-b878-7df343f43d37"
RESOURCE = "40728276-52a7-4932-bf32-76737f1fd01a"
REDIRECT = "https://oauth.pstmn.io/v1/callback"
SCOPE = f"api://{RESOURCE}/.default offline_access"
AUTH = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/authorize"
TOKEN = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"


def _load() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def _save(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def sign_in_url() -> str:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(12)
    data = _load()
    data.update({"verifier": verifier, "state": state})
    _save(data)
    query = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "response_type": "code", "redirect_uri": REDIRECT,
        "scope": SCOPE, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
        "prompt": "select_account",
    })
    return f"{AUTH}?{query}"


def _extract_code(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("http"):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
        if "error" in qs:
            raise SystemExit(f"Sign-in returned an error: {qs.get('error_description', qs['error'])}")
        if "code" not in qs:
            raise SystemExit("That URL has no ?code= in it. Copy the whole address bar after signing in.")
        return qs["code"][0]
    return raw


def exchange(raw: str) -> dict:
    data = _load()
    verifier = data.get("verifier")
    if not verifier:
        raise SystemExit("No PKCE verifier stored. Run --url first, in this same checkout.")
    r = requests.post(TOKEN, timeout=60, data={
        "client_id": CLIENT_ID, "grant_type": "authorization_code",
        "code": _extract_code(raw), "redirect_uri": REDIRECT,
        "code_verifier": verifier, "scope": SCOPE,
    })
    if r.status_code >= 400:
        raise SystemExit(f"Token exchange failed {r.status_code}: {r.text[:300]}")
    payload = r.json()
    data.update({
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token", ""),   # kept this time
        "expires_at": time.time() + int(payload.get("expires_in", 3600)) - 60,
    })
    _save(data)
    return data


def _refresh(data: dict) -> dict:
    r = requests.post(TOKEN, timeout=60, data={
        "client_id": CLIENT_ID, "grant_type": "refresh_token",
        "refresh_token": data["refresh_token"], "scope": SCOPE,
    })
    if r.status_code >= 400:
        raise SystemExit(f"Refresh failed {r.status_code}: {r.text[:200]}\nRun --url and sign in again.")
    payload = r.json()
    data.update({
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token", data["refresh_token"]),
        "expires_at": time.time() + int(payload.get("expires_in", 3600)) - 60,
    })
    _save(data)
    return data


def bearer() -> str:
    """A valid access token, refreshed silently when it has aged out."""
    env = os.environ.get("DOCTAVIAN_BEARER", "").strip()
    data = _load()
    if not data.get("access_token"):
        if env:
            return env
        raise SystemExit("No Doctavian token stored. Run: python -m before.doctavian_auth --url")
    if time.time() >= data.get("expires_at", 0):
        if not data.get("refresh_token"):
            raise SystemExit("Token expired and no refresh token stored. Run --url and sign in again.")
        data = _refresh(data)
    return data["access_token"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", action="store_true", help="print the sign-in URL")
    g.add_argument("--code", metavar="REDIRECT_URL", help="the URL you were redirected to")
    g.add_argument("--token", action="store_true", help="print a valid bearer")
    args = ap.parse_args()

    if args.url:
        print("\nOpen this, sign in with the account Kanwal enabled, then copy the")
        print("address bar you land on (it will start https://oauth.pstmn.io/...):\n")
        print(sign_in_url())
        print('\nThen: python -m before.doctavian_auth --code "<that whole URL>"\n')
    elif args.code:
        d = exchange(args.code)
        left = int(d["expires_at"] - time.time())
        print(f"stored. access token valid ~{left // 60} min; "
              f"refresh token {'saved' if d.get('refresh_token') else 'NOT returned'}")
    else:
        print(bearer())


if __name__ == "__main__":
    main()
