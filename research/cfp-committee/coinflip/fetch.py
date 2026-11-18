#!/usr/bin/env python3
"""Fetch SP+ and the 2026 regular-season schedule from CFBD (2 calls).
Key read from os.environ only; never printed."""
import json, os, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://apinext.collegefootballdata.com"
def get(path, out):
    r = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + os.environ["CFBD_KEY"]})
    with urllib.request.urlopen(r, timeout=90) as resp:
        print(path, "status", resp.status, "X-CallLimit-Remaining", resp.headers.get("X-CallLimit-Remaining"))
        data = json.load(resp)
    json.dump(data, open(os.path.join(HERE, "raw", out), "w"))
    return data
get("/ratings/sp?year=2026", "sp.json")
get("/games?year=2026&seasonType=regular&classification=fbs", "games.json")
