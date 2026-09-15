#!/usr/bin/env python3
"""Pre-register a prediction so its timestamp cannot be argued with.

    python3 scripts/seal.py --seal tracking/sports-page-picks-2026-w4.md --unlock 2026-09-25T19:00
    python3 scripts/seal.py --list
    python3 scripts/seal.py --reveal --week 4

WHAT PROBLEM THIS SOLVES. This paper grades its own forecasts in public, and the
weakest link in that promise is the reasoning: anyone can produce a rationale
after a result and honestly believe they thought it beforehand. Hindsight is not
dishonesty, it is memory working normally, which is exactly why a promise not to
do it is worth nothing.

So: the text is written before kickoff and moved OUT of the repository. What gets
committed is a SHA-256 of the exact bytes. After the games, --reveal puts the text
back and recomputes the digest. If a single character changed, the digests differ
and the reveal is refused. Nobody has to trust us; they can run sha256sum.

WHY THE PLAINTEXT LEAVES THE REPO. A file committed to git is readable by anyone
with the repo, so "sealed" would be a fiction. The vault lives under
~/.local/share/sports-page/sealed/, outside the working tree and outside anything
git can see.

THE UNLOCK TIME IS PART OF THE COMMITMENT. It is recorded in the public file at
seal time and --reveal refuses before it. That stops the subtler cheat: revealing
selectively, early, only when the picks happen to be landing well.

WHAT THIS DOES NOT DO. It is not secrecy against an adversary -- the vault is a
plain file on disk and anyone with the machine can read it. It proves the text
existed unchanged at seal time, which is the only property the honesty of a
scorecard actually needs.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
VAULT = pathlib.Path.home() / ".local/share/sports-page/sealed"
PUBLIC = REPO / "tracking" / "sealed"


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def seal(src, week, unlock):
    src = pathlib.Path(src)
    if not src.exists():
        raise SystemExit(f"{src} does not exist")
    VAULT.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)

    sha = digest(src)
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    vault_file = VAULT / f"w{week:02d}-{src.name}"
    if vault_file.exists():
        raise SystemExit(f"{vault_file} already sealed. A seal is not re-issued; "
                         "that would defeat the entire point.")
    shutil.move(str(src), vault_file)
    os.chmod(vault_file, 0o600)

    commitment = PUBLIC / f"w{week:02d}-commitment.md"
    commitment.write_text(f"""# Sealed commitment — Week {week}

**SHA-256**

    {sha}

| | |
|---|---|
| sealed at | `{stamp}` |
| unlocks | `{unlock}` |
| covers | `{src.name}` |
| vault | outside the repository, not in git |

The reasoning behind The Sports Page's Week {week} pool entry was written before
kickoff and is held outside this repository. The digest above is of its exact
bytes, committed now.

After the unlock time the text is published here. To check it was not edited:

    sha256sum tracking/sports-page-picks-2026-w{week:02d}.md

If that does not match the hash above, the text was changed after the fact and
nothing in it should be believed.

*Why bother: anyone can write a rationale after a result and sincerely believe
they thought it beforehand. That is memory working normally, which is exactly why
a promise not to do it is worth nothing.*
""")
    (PUBLIC / f"w{week:02d}-commitment.json").write_text(json.dumps(
        dict(week=week, sha256=sha, sealed_at=stamp, unlock=unlock,
             covers=src.name, vault=str(vault_file)), indent=1))
    print(f"  sealed  {src.name}")
    print(f"  sha256  {sha}")
    print(f"  vault   {vault_file}  (outside the repo)")
    print(f"  public  {commitment.relative_to(REPO)}")
    print(f"  unlocks {unlock}")
    print("\n  Commit tracking/sealed/ now. Do NOT commit the plaintext.")
    return 0


def reveal(week, force=False):
    meta_path = PUBLIC / f"w{week:02d}-commitment.json"
    if not meta_path.exists():
        raise SystemExit(f"no commitment recorded for week {week}")
    meta = json.loads(meta_path.read_text())
    unlock = meta.get("unlock")
    now = datetime.datetime.now().astimezone()
    if unlock and not force:
        try:
            u = datetime.datetime.fromisoformat(unlock)
            if u.tzinfo is None:
                u = u.replace(tzinfo=now.tzinfo)
            if now < u:
                raise SystemExit(
                    f"  sealed until {unlock}; it is {now.isoformat(timespec='seconds')}.\n"
                    "  Refusing. Revealing early, selectively, is the cheat this exists to stop.")
        except ValueError:
            print(f"  could not parse unlock time {unlock!r}; proceeding")

    vault_file = pathlib.Path(meta["vault"])
    if not vault_file.exists():
        raise SystemExit(f"vault file missing: {vault_file}")
    actual = digest(vault_file)
    if actual != meta["sha256"]:
        raise SystemExit(f"  DIGEST MISMATCH\n    committed {meta['sha256']}\n"
                         f"    actual    {actual}\n"
                         "  The sealed text changed after it was sealed. Publish nothing.")
    dest = REPO / "tracking" / meta["covers"]
    shutil.copy2(vault_file, dest)
    print(f"  digest verified  {actual}")
    print(f"  revealed         {dest.relative_to(REPO)}")
    print(f"  sealed at        {meta['sealed_at']}")
    print("\n  Anyone can check it:")
    print(f"    sha256sum {dest.relative_to(REPO)}")
    return 0


def listing():
    if not PUBLIC.exists():
        print("  nothing sealed yet")
        return 0
    rows = sorted(PUBLIC.glob("*-commitment.json"))
    if not rows:
        print("  nothing sealed yet")
        return 0
    now = datetime.datetime.now().astimezone()
    print(f"\n  {'week':<6}{'sealed':<22}{'unlocks':<22}{'state':<12}sha256")
    for r in rows:
        m = json.loads(r.read_text())
        v = pathlib.Path(m["vault"])
        try:
            u = datetime.datetime.fromisoformat(m["unlock"])
            if u.tzinfo is None:
                u = u.replace(tzinfo=now.tzinfo)
            state = "OPEN" if now >= u else "sealed"
        except Exception:
            state = "?"
        if not v.exists():
            state = "VAULT GONE"
        print(f"  {m['week']:<6}{m['sealed_at'][:19]:<22}{m['unlock'][:19]:<22}{state:<12}{m['sha256'][:16]}...")
    print()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seal", metavar="FILE")
    ap.add_argument("--reveal", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--week", type=int)
    ap.add_argument("--unlock", help="ISO time the seal opens, e.g. 2026-09-25T19:00")
    ap.add_argument("--force", action="store_true", help="reveal before the unlock time")
    a = ap.parse_args()

    if a.list:
        return listing()
    if a.seal:
        if a.week is None:
            m = re.search(r"w(\d+)", pathlib.Path(a.seal).stem)
            if not m:
                ap.error("--week is required (could not infer it from the filename)")
            a.week = int(m.group(1))
        if not a.unlock:
            ap.error("--unlock is required: a seal with no stated opening time is not a commitment")
        return seal(a.seal, a.week, a.unlock)
    if a.reveal:
        if a.week is None:
            ap.error("--week is required")
        return reveal(a.week, a.force)
    ap.error("use --seal, --reveal or --list")


if __name__ == "__main__":
    sys.exit(main())
