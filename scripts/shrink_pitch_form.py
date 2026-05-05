#!/usr/bin/env python3
"""Replace the bloated pitch form with the compact single-row strip across all issues.

Reads the canonical OLD block from published/001-skenes-era.html and the canonical
NEW block from published/029-cfb-coaching-stabilization.html, then byte-replaces
across published/, queue/, and reserve/.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
OLD_SRC = ROOT / "published" / "001-skenes-era.html"
NEW_SRC = ROOT / "published" / "029-cfb-coaching-stabilization.html"


def extract_block(path: Path, start_marker: str, end_marker: str) -> str:
    text = path.read_text()
    start = text.find(start_marker)
    if start < 0:
        sys.exit(f"start marker not found in {path}")
    end = text.find(end_marker, start)
    if end < 0:
        sys.exit(f"end marker not found in {path}")
    return text[start:end + len(end_marker)]


OLD_START = '<div id="pitch" style="border:2px solid var(--gold);background:var(--card);padding:1.5rem 1.8rem;margin:1.8rem 0">'
NEW_START = '<aside id="pitch" style="border-top:1px solid var(--div);'

# Extract OLD_BLOCK from git (since the file on disk has already been converted on prior runs).
import subprocess
try:
    old_text = subprocess.check_output(
        ["git", "show", "HEAD:published/001-skenes-era.html"],
        cwd=ROOT, text=True,
    )
except subprocess.CalledProcessError:
    sys.exit("could not read pre-edit skenes-era from git HEAD")

start = old_text.find(OLD_START)
end = old_text.find("</script>", start)
if start < 0 or end < 0:
    sys.exit("could not locate OLD pitch block in git HEAD copy of skenes-era")
OLD_BLOCK = old_text[start:end + len("</script>")]

new_text = NEW_SRC.read_text()
n_start = new_text.find(NEW_START)
n_end = new_text.find("</script>", n_start)
if n_start < 0 or n_end < 0:
    sys.exit("could not locate NEW pitch block in #37")
NEW_BLOCK = new_text[n_start:n_end + len("</script>")]

if OLD_BLOCK == NEW_BLOCK:
    sys.exit("OLD and NEW blocks are identical — extraction failed")

import re
# Match the whole pitch block tolerantly: from the opening div through the
# closing </script> of the AJAX handler. The handler ends with `});\n  </script>`
# and is preceded by the "btn.textContent='SUBMIT IDEA'" line — a stable
# signature across every variant we've seen.
PATTERN = re.compile(
    r'<div id="pitch" style="border:2px solid var\(--gold\).*?'
    r"btn\.textContent='SUBMIT IDEA';\s*\}\);\s*</script>",
    re.DOTALL,
)

changed = []
skipped_already_new = []
skipped_no_match = []

for sub in ("published", "queue", "reserve"):
    for f in sorted((ROOT / sub).glob("*.html")):
        text = f.read_text()
        if NEW_BLOCK in text:
            skipped_already_new.append(f)
            continue
        new_text, n = PATTERN.subn(lambda _m: NEW_BLOCK, text)
        if n == 0:
            skipped_no_match.append(f)
            continue
        if n > 1:
            sys.exit(f"unexpected: {n} matches in {f}")
        f.write_text(new_text)
        changed.append(f)

print(f"Updated: {len(changed)} files")
for f in changed:
    print(f"  {f.relative_to(ROOT)}")
print(f"Already on new design: {len(skipped_already_new)}")
print(f"No pitch form found: {len(skipped_no_match)}")
for f in skipped_no_match:
    print(f"  {f.relative_to(ROOT)}")
