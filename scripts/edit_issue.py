#!/usr/bin/env python3
"""Safe surgical edits to a published or queued issue.

Not part of the publish pipeline. This is the tool used for the readability
pass -- rewriting decks and paragraphs for the bottom-line-up-front / sixth-grade
standard without disturbing anything else.

It exists because the same two mistakes kept happening by hand:

1. **Greedy regex escaping its element.** A pattern like
   `<p>Some opening.*?</p>` with DOTALL will happily run past the paragraph it
   was aimed at if the exact wording is off, swallowing whole sections. The same
   trap ate two concept-primer spans earlier in this pass and spliced a stale
   50-word sentence back into an issue. Every matcher here is TEMPERED --
   `(?:(?!</p>).)*?` -- so a match physically cannot cross the closing tag.

2. **Changing the headline.** The RSS item title is "#N: <headline>" and the
   Open Graph card renders the headline, so editing one silently invalidates a
   social card and changes the field an RSS-to-email bridge may key on.
   `edit()` snapshots the headline before and asserts it after, refusing to
   write if it moved.

Nothing is written unless every replacement matched, so a typo aborts cleanly
instead of leaving a half-edited file.

    from edit_issue import edit
    with edit("published/066-foo.html") as e:
        e.deck("<div class='deck'>New deck.</div>")
        e.para("The old opening words", "<p>New paragraph.</p>")
"""
import re
from contextlib import contextmanager

HED = re.compile(r'class="hed"[^>]*>(.*?)</(?:h1|h2|h3|div)', re.S)


class _Editor:
    def __init__(self, text):
        self.s = text
        self.n = 0

    def deck(self, new):
        """Replace the deck, whether it is a <p class="deck"> or a <div>."""
        m = re.search(r'<(p|div) class="deck">(?:(?!</\1>).)*?</\1>', self.s, re.S)
        assert m, "no deck found"
        self.s = self.s[:m.start()] + new + self.s[m.end():]
        self.n += 1

    def para(self, prefix, new):
        """Replace the one <p> containing `prefix`, matching within that <p>."""
        rx = re.compile(r'<p[^>]*>(?:(?!</p>).)*?' + re.escape(prefix)
                        + r'(?:(?!</p>).)*?</p>', re.S)
        m = rx.search(self.s)
        assert m, f"paragraph not found: {prefix[:60]!r}"
        self.s = self.s[:m.start()] + new + self.s[m.end():]
        self.n += 1

    def swap(self, old, new, required=True):
        """Plain substring swap, for word-level tightening."""
        if old not in self.s:
            assert not required, f"swap target not found: {old[:60]!r}"
            return False
        self.s = self.s.replace(old, new)
        self.n += 1
        return True

    def drop_para(self, prefix):
        rx = re.compile(r'\s*<p[^>]*>(?:(?!</p>).)*?' + re.escape(prefix)
                        + r'(?:(?!</p>).)*?</p>', re.S)
        m = rx.search(self.s)
        assert m, f"paragraph not found: {prefix[:60]!r}"
        self.s = self.s[:m.start()] + self.s[m.end():]
        self.n += 1


@contextmanager
def edit(path):
    original = open(path, encoding="utf-8").read()
    hed_before = HED.search(original)
    e = _Editor(original)
    yield e
    hed_after = HED.search(e.s)
    assert (hed_before is None) == (hed_after is None), "headline element vanished"
    if hed_before:
        assert hed_before.group(1) == hed_after.group(1), (
            "HEADLINE CHANGED -- refusing to write. The RSS title and the OG card "
            "both derive from it.")
    open(path, "w", encoding="utf-8").write(e.s)
    print(f"  {path}: {e.n} edits, headline intact")
