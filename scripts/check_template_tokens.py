#!/usr/bin/env python3
"""Can the publisher actually stamp the template it tells people to copy?

    python3 scripts/check_template_tokens.py

WHY THIS EXISTS. On 2026-10-02 every one of the five autopublish slots failed
and Issue #188 never went out. The cause was not the publisher and not the
article: `queue/_TEMPLATE.html` emits `Vol. I, No. TODO_NN`, and the regex in
autopublish.py that fills the issue number accepted `__`, `[TBD]` and digits --
but not `TODO_NN`. The template had been updated to a new placeholder and the
publisher had not. Every issue drafted from the current template was therefore
unpublishable, and nobody found out until the day one reached the front of the
queue.

The post-substitution guard did its job perfectly: it refused to ship a page
reading "Vol. I, No. TODO_NN" and failed loudly. The problem was that it fails
at 4:30am, on the day of publication, after the queue order is already set.

So this runs the real substitution over the real template and asserts nothing is
left behind. It is a drift detector between two files that must agree and have no
other reason to stay in step. Run it in CI, not at publish time -- the entire
point is to find out on the day the TEMPLATE changes rather than on the day an
article built from it comes up for publication.

HONEST LIMIT: this proves the tokens get filled, not that they get filled
correctly. A regex that replaced the issue number with the wrong number would
pass this cleanly.
"""
import datetime
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "queue" / "_TEMPLATE.html"

# Same pattern the publisher's own post-substitution guard uses. Kept identical
# on purpose: if that one is widened, this must see the same universe.
PLACEHOLDER = r"TODO_[A-Z0-9_]+|\{\{[A-Z0-9_]+\}\}|\[TBD\]"

# The tokens autopublish.py is RESPONSIBLE for filling. Everything else in the
# template is the author's to replace before the file joins QUEUE_ORDER. This
# set is the contract between the two files; widening the template's furniture
# without widening this is exactly the drift that broke 2026-10-02.
FURNITURE = {"TODO_NN", "TODO_DATE"}


def main():
    if not TEMPLATE.exists():
        print(f"  no template at {TEMPLATE}")
        return 0

    sys.path.insert(0, str(REPO / "scripts"))
    try:
        import autopublish
    except Exception as e:
        print(f"  cannot import autopublish.py: {e}")
        return 1

    content = TEMPLATE.read_text(encoding="utf-8")
    present = set(re.findall(PLACEHOLDER, content))

    # Drive the publisher's own stamping path rather than reimplementing it,
    # so this cannot drift from the thing it is testing.
    fn = getattr(autopublish, "update_article", None)
    if fn is None:
        print("  autopublish.update_article not found -- cannot test stamping")
        return 1

    # update_article(content, issue_num, today) -- `today` is a date object and
    # the function formats it itself.
    try:
        out = fn(content, 999, datetime.date(2026, 1, 1))
    except Exception as e:
        print(f"  could not call update_article: {type(e).__name__}: {e}")
        return 1
    if not isinstance(out, str):
        print(f"  update_article returned {type(out).__name__}, expected str")
        return 1

    after = set(re.findall(PLACEHOLDER, out))

    # Only the FURNITURE is the publisher's job. Everything else in the template
    # -- headline, deck, stat cards, slug -- is the author's, and a finished
    # article has none of it left by the time it joins QUEUE_ORDER. Demanding the
    # publisher fill TODO_HEADLINE would be asking it to write the piece.
    print(f"  furniture the publisher owns : {', '.join(sorted(FURNITURE))}")
    missing = sorted(t for t in FURNITURE if t not in present)
    unfilled = sorted(t for t in FURNITURE if t in after)
    author = sorted(t for t in after if t not in FURNITURE)
    print(f"  present in the template      : "
          f"{', '.join(sorted(t for t in FURNITURE if t in present)) or 'none'}")
    print(f"  author tokens left (expected): {len(author)}")

    if missing:
        print(f"\n  FAIL. The template no longer emits {', '.join(missing)}.")
        print("  If it was renamed, autopublish.py must learn the new token.")
        return 1
    if unfilled:
        print(f"\n  FAIL. The publisher could not fill {', '.join(unfilled)}.")
        print("  Every issue drafted from this template will abort at 4:30am on")
        print("  the day it reaches the front of the queue -- which is how all five")
        print("  slots failed on 2026-10-02 and Issue #188 did not go out.")
        print("  Fix the substitution in autopublish.py, or change the template to")
        print("  emit a token the publisher already understands.")
        return 1
    print("\n  OK -- the publisher can stamp every piece of furniture in its own template.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
