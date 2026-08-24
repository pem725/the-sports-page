#!/usr/bin/env python3
"""Set or rotate a secret in ~/.config/secrets/tokens.env without exposing it.

    python3 scripts/set_secret.py CFBD_KEY

Prompts with a hidden input, writes the file, prints the before/after
fingerprint so you can confirm the rotation took. The value is never echoed,
never placed on a command line, never written to shell history.

WHY NOT JUST USE sed. Because this leaks in three quiet ways:

    sed -i "s|^export CFBD_KEY=.*|export CFBD_KEY=$NEW|" ~/.config/secrets/tokens.env

the value lands in your shell history file, it is visible in `ps` output to any
process on the machine for as long as the command runs, and it sits in the
terminal scrollback. getpass avoids all three: the input is never displayed, and
the value goes straight from stdin into the file.

The file is rewritten with mode 600 preserved, and a timestamped backup is kept.
"""
import getpass
import hashlib
import os
import re
import shutil
import sys
import time

PATH = os.path.expanduser("~/.config/secrets/tokens.env")
SALT = b"the-sports-page/check_env/v1"


def fp(v: str) -> str:
    return hashlib.sha256(SALT + v.encode()).hexdigest()[:8]


def current(text: str, name: str):
    m = re.search(rf'(?m)^\s*export\s+{re.escape(name)}=(.*)$', text)
    if not m:
        return None
    return m.group(1).strip().strip('"').strip("'")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--from-file" in sys.argv:
        i = sys.argv.index("--from-file")
        if i + 1 < len(sys.argv):
            args = [a for a in args if a != sys.argv[i + 1]]
    if len(args) != 1:
        print(__doc__.strip().split("\n\n")[1])
        return 2
    name = args[0]
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
        print(f"refusing: {name!r} does not look like an environment variable name")
        return 2

    from_file = None
    if "--from-file" in sys.argv:
        i = sys.argv.index("--from-file")
        if i + 1 >= len(sys.argv):
            print("  --from-file needs a path")
            return 2
        from_file = sys.argv[i + 1]

    # HARD STOP without a terminal. getpass silently falls back to a mode that
    # ECHOES the input ("Warning: Password input may be echoed"), which would
    # print a live secret into whatever is capturing this session. That fallback
    # is the same class of bug that leaked two tokens already, so it is refused
    # rather than warned about.
    if from_file is None and not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("  REFUSING: no terminal, so the hidden prompt is not available.")
        print("  getpass would fall back to echoing your input in plain text.\n")
        print("  Do one of these instead:")
        print("    1. Run this in a real terminal window (not inside an agent or a pipe):")
        print(f"         python3 scripts/set_secret.py {name}")
        print("    2. Or put the value alone in a file and hand it over:")
        print(f"         python3 scripts/set_secret.py {name} --from-file /path/to/keyfile")
        print("       The file is overwritten and deleted once the value is stored.")
        return 2

    os.makedirs(os.path.dirname(PATH), mode=0o700, exist_ok=True)
    text = open(PATH, encoding="utf-8").read() if os.path.exists(PATH) else ""

    old = current(text, name)
    print(f"  {name}: {'currently ' + fp(old) if old else 'not currently set'}")

    if from_file:
        if not os.path.exists(from_file):
            print(f"  no such file: {from_file}")
            return 2
        with open(from_file, encoding="utf-8") as fh:
            new = fh.read().strip()
        # scrub it: overwrite the bytes, then unlink, so the value does not
        # linger on disk after it has been stored properly
        try:
            n = os.path.getsize(from_file)
            with open(from_file, "wb") as fh:
                fh.write(os.urandom(max(n, 64)))
                fh.flush()
                os.fsync(fh.fileno())
        finally:
            os.remove(from_file)
        print(f"  read from {from_file}, which has been overwritten and removed")
    else:
        new = getpass.getpass(f"  paste new {name} (input hidden, nothing is echoed): ").strip()
    if not new:
        print("  empty input; nothing changed")
        return 1
    if old is not None and new == old:
        print("  WARNING: identical to the current value. Nothing rotated.")
        return 1

    if os.path.exists(PATH):
        shutil.copy2(PATH, f"{PATH}.bak-{time.strftime('%Y%m%d-%H%M%S')}")

    line = f"export {name}={new}"
    if old is not None:
        text = re.sub(rf'(?m)^\s*export\s+{re.escape(name)}=.*$', line, text)
    else:
        text = text.rstrip("\n") + "\n" + line + "\n"

    fd = os.open(PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(PATH, 0o600)

    print(f"  written. fingerprint {fp(old) if old else '(none)'} -> {fp(new)}")
    print("  open a new shell, or:  source ~/.config/secrets/tokens.env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
