#!/usr/bin/env python3
"""Talk to Porkbun without ever putting a key on a command line.

    python3 scripts/porkbun.py --ping                  # do the keys work?
    python3 scripts/porkbun.py --dns thesportspage.net # list DNS records
    python3 scripts/porkbun.py --mx  thesportspage.net # just the mail records

Reads PORKBUN_API_KEY and PORKBUN_SECRET_KEY from the environment (they live in
~/.config/secrets/tokens.env, mode 600). Nothing here formats, logs, or returns a
key value; they go straight from os.environ into a request header.

WHY NOT curl. Because the obvious version leaks:

    curl -v -H "X-API-Key: $PORKBUN_API_KEY" https://api.porkbun.com/...

`-v` echoes request headers, so the key lands in your terminal and your
scrollback. Same for --trace and -w '%{header_json}'. Plain curl without -v is
fine, but the flag is one keystroke away and this file removes the temptation.

NOTE ON EMAIL FORWARDING. It is not in the v3 API. The spec exposes 68
endpoints; the only /email one is setPassword, for Porkbun's paid mailbox
product, and addUrlForward is *web* redirects, not mail. Email forwarding is
configured in the web dashboard only. What these keys actually unlock is DNS
(11 endpoints), domain management (21), SSL retrieval, and webhooks.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://api.porkbun.com/api/json/v3"
REQUIRED = ("PORKBUN_API_KEY", "PORKBUN_SECRET_KEY")


def call(path: str, body: dict | None = None) -> dict:
    missing = [n for n in REQUIRED if not os.environ.get(n)]
    if missing:
        raise SystemExit(
            f"unset: {', '.join(missing)}\n"
            f"  set them with:  python3 scripts/set_secret.py {missing[0]}\n"
            f"  then open a new shell, or: source ~/.config/secrets/tokens.env"
        )
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body or {}).encode(),
        headers={
            "Content-Type": "application/json",
            # header auth, so no credential is ever in a URL or a shell argument
            "X-API-Key": os.environ["PORKBUN_API_KEY"],
            "X-Secret-API-Key": os.environ["PORKBUN_SECRET_KEY"],
        },
        method="POST",
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=45))
    except urllib.error.HTTPError as e:
        # Porkbun returns a JSON message on failure; surface it, never the key
        try:
            return json.loads(e.read().decode())
        except Exception:
            raise SystemExit(f"HTTP {e.code} from {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Porkbun, without leaking anything.")
    ap.add_argument("--ping", action="store_true", help="verify the key pair works")
    ap.add_argument("--dns", metavar="DOMAIN", help="list all DNS records")
    ap.add_argument("--mx", metavar="DOMAIN", help="list only MX and mail-related records")
    a = ap.parse_args()

    if a.ping:
        r = call("/ping")
        ok = r.get("status") == "SUCCESS"
        print(f"  status: {r.get('status', '?')}")
        if ok:
            print(f"  the API answered; your IP as it sees it: {r.get('yourIp', '?')}")
            print("  both keys are valid.")
        else:
            print(f"  message: {r.get('message', '(none)')}")
        return 0 if ok else 1

    domain = a.dns or a.mx
    if not domain:
        ap.print_help()
        return 2

    r = call(f"/dns/retrieve/{domain}")
    if r.get("status") != "SUCCESS":
        print(f"  {r.get('status')}: {r.get('message', '')}")
        print("  note: API access must be enabled per-domain in the Porkbun dashboard.")
        return 1
    recs = r.get("records", [])
    if a.mx:
        recs = [x for x in recs if x.get("type") in ("MX", "TXT")]
    print(f"  {len(recs)} records for {domain}")
    print(f"  {'type':<7}{'name':<34}{'prio':>5}  content")
    for x in sorted(recs, key=lambda z: (z.get("type", ""), z.get("name", ""))):
        prio = x.get("prio") or ""
        print(f"  {x.get('type',''):<7}{x.get('name',''):<34}{prio:>5}  {x.get('content','')[:60]}")
    if a.mx and not any(x.get("type") == "MX" for x in recs):
        print("\n  NO MX RECORDS. Mail to this domain has nowhere to go.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
