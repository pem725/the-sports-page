#!/usr/bin/env python3
"""Refuse to publish an unfinished Sunday Edition.

Added 2026-11-15, after the overnight Sunday routine found a human draft in
queue/ with eight yellow "[FILL SAT NIGHT: ...]" slots, filled them from web
search, and published at 3:16am. Three facts were wrong and one ranking was
cited two days before it existed.

Exit 0 = ready. Exit 1 = not ready; every reason is printed. Run it on the
queue file BEFORE `git mv` to published/. A draft a human left unfinished is
the human's to finish: an unattended run must stop, not fill.

    python3 scripts/sunday_ready.py queue/sunday-NNN.html
"""
import re
import sys

CHECKS = [
    (r"\[FILL[^\]]*\]", "unfilled slot"),
    (r'class="fill"', "highlighted fill span"),
    (r"\{\{[A-Z_]+\}\}", "template placeholder"),
    (r"<!--\s*DRAFT\b", "marked DRAFT"),
    (r"<!--\s*READERSHIP_BLOCK\s*-->", "readership block not injected"),
]


def main(path):
    s = open(path, encoding="utf-8").read()
    bad = []
    for pat, why in CHECKS:
        for m in re.finditer(pat, s):
            line = s.count("\n", 0, m.start()) + 1
            bad.append(f"  line {line}: {why}: {m.group(0)[:70]}")
    if bad:
        print(f"{path}: NOT READY ({len(bad)})")
        print("\n".join(bad))
        return 1
    print(f"{path}: ready")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
