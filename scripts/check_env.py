#!/usr/bin/env python3
"""Report whether secrets are present. Cannot print one.

WHY THIS EXISTS. Twice in one week a shell one-liner leaked a live token into a
chat transcript. Both times the culprit was the same expansion:

    echo "TOKEN: ${TOKEN:+SET}${TOKEN:-unset}"

`${VAR:-default}` substitutes the VALUE when the variable is set, so the "safe
looking" check printed the secret in full. `${VAR:+SET}` is fine on its own; the
`:-` half is the trap, and pairing them looks harmless and is not.

The lesson is not "be more careful." Careful failed twice. The fix is a tool with
no code path that can emit a secret: this script reads values, hashes them, and
discards them. The raw value is never formatted, never concatenated into output,
never returned.

    python3 scripts/check_env.py                 # all known secrets
    python3 scripts/check_env.py CFBD_KEY        # just one
    python3 scripts/check_env.py --json          # for scripts

The fingerprint is a salted SHA-256 prefix. It is stable for a given value, so
you can confirm a rotation actually changed the token, and it reveals nothing
about the token itself.

NEVER do any of these with a secret:
    echo $TOKEN                      env | grep TOKEN
    echo "${TOKEN:-unset}"           printenv TOKEN
    curl -H "Authorization: $TOKEN"  # fine, but never with -v / --trace
"""
import argparse
import hashlib
import json
import os
import sys

# Secrets this project and its neighbours use. Add names, never values.
KNOWN = [
    "ANTHROPIC_API_KEY",
    "BUTTONDOWN_KEY",
    "CANVAS_KEY",
    "CFBD_KEY",
    "GOATCOUNTER_TOKEN",
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "OSF_TOKEN",
    "PORKBUN_API_KEY",
    "PORKBUN_SECRET_KEY",
    "SPOTIFY_CLIENT_ID",
    "TBK_DOMAIN",
    "TBK_WP_PWD",
    "TBK_WP_USER",
    "YOUTUBE_API_KEY",
]

SALT = b"the-sports-page/check_env/v1"


def fingerprint(value: str) -> str:
    """Eight hex characters derived from the value. One-way, by construction."""
    return hashlib.sha256(SALT + value.encode()).hexdigest()[:8]


def inspect(name: str) -> dict:
    """Return metadata only. The value goes out of scope and is never returned."""
    raw = os.environ.get(name)
    if not raw:
        return {"name": name, "set": False}
    return {"name": name, "set": True, "length": len(raw), "fingerprint": fingerprint(raw)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Check secrets without revealing them.")
    ap.add_argument("names", nargs="*", help="specific variables (default: all known)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rows = [inspect(n) for n in (a.names or KNOWN)]

    if a.json:
        print(json.dumps(rows, indent=1))
        return 0 if all(r["set"] for r in rows) else 1

    width = max(len(r["name"]) for r in rows) + 2
    print(f"  {'variable':<{width}}{'status':<9}{'len':>5}  fingerprint")
    print(f"  {'-'*(width-2):<{width}}{'-'*7:<9}{'-'*4:>5}  {'-'*11}")
    for r in rows:
        if r["set"]:
            print(f"  {r['name']:<{width}}{'SET':<9}{r['length']:>5}  {r['fingerprint']}")
        else:
            print(f"  {r['name']:<{width}}{'unset':<9}{'-':>5}  -")
    missing = [r["name"] for r in rows if not r["set"]]
    if missing:
        print(f"\n  unset: {', '.join(missing)}")
        print("  add them to ~/.config/secrets/tokens.env (mode 600), then open a new shell")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
