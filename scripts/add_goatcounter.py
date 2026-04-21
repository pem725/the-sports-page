#!/usr/bin/env python3
"""
Idempotently inject the GoatCounter analytics snippet into every HTML file
in the repo: root-level pages, queue/, and published/. Also updates the
SHELL template in build_queue_batch.py so future auto-generated issues
inherit it.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SNIPPET = (
    '<script data-goatcounter="https://thesportspage.goatcounter.com/count" '
    'async src="//gc.zgo.at/count.js"></script>\n'
)

MARKER = "thesportspage.goatcounter.com"


def inject_into_html(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if MARKER in content:
        return "skipped (already present)"
    # Insert right before </head>
    new, n = re.subn(r'(\s*)</head>', r'\n' + SNIPPET + r'\1</head>', content, count=1)
    if n == 0:
        return "FAIL: no </head> found"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return "injected"


def update_shell_template():
    path = os.path.join(REPO, "scripts", "build_queue_batch.py")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if MARKER in content:
        return "skipped (already present)"
    # Double-braced because SHELL uses str.format; literal braces must be {{/}}
    snip = (
        '<script data-goatcounter="https://thesportspage.goatcounter.com/count" '
        'async src="//gc.zgo.at/count.js"></script>\n'
    )
    new, n = re.subn(
        r'(\s*)</head>',
        '\n' + snip + r'\1</head>',
        content,
        count=1,  # only the first </head> (inside the SHELL string)
    )
    if n == 0:
        return "FAIL: no </head> in template"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return "injected"


def main():
    # Root-level HTMLs
    targets = [os.path.join(REPO, f) for f in os.listdir(REPO) if f.endswith(".html")]
    # queue/
    q = os.path.join(REPO, "queue")
    targets += [os.path.join(q, f) for f in os.listdir(q) if f.endswith(".html")]
    # published/
    p = os.path.join(REPO, "published")
    targets += [os.path.join(p, f) for f in os.listdir(p) if f.endswith(".html")]

    print(f"HTML files found: {len(targets)}")
    injected = skipped = failed = 0
    for t in sorted(targets):
        rel = os.path.relpath(t, REPO)
        status = inject_into_html(t)
        if status.startswith("injected"):
            injected += 1
            print(f"  {rel}: {status}")
        elif status.startswith("skipped"):
            skipped += 1
        else:
            failed += 1
            print(f"  {rel}: {status}", file=sys.stderr)

    print(f"\nHTML summary: {injected} injected, {skipped} skipped, {failed} failed")

    print("\nTemplate update (scripts/build_queue_batch.py):")
    print(f"  {update_shell_template()}")


if __name__ == "__main__":
    main()
