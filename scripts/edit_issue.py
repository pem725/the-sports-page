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
        self.missed = []

    def deck(self, new):
        """Replace the deck, whether it is a <p class="deck"> or a <div>."""
        m = re.search(r'<(p|div) class="deck">(?:(?!</\1>).)*?</\1>', self.s, re.S)
        assert m, "no deck found"
        self.s = self.s[:m.start()] + new + self.s[m.end():]
        self.n += 1

    def para(self, prefix, new, optional=False):
        """Replace the one <p> containing `prefix`, matching within that <p>.

        Strict by default: a missed anchor aborts the whole edit rather than
        writing a partial file. Pass optional=True for best-effort edits in a
        large batch, where one bad anchor should not discard the other twenty.
        Anchors must not straddle inline markup -- a prefix spanning an <em> or
        <strong> can never match, which is the usual cause of a miss.
        """
        rx = re.compile(r'<p[^>]*>(?:(?!</p>).)*?' + re.escape(prefix)
                        + r'(?:(?!</p>).)*?</p>', re.S)
        m = rx.search(self.s)
        if not m:
            if optional:
                self.missed.append(prefix[:50])
                return False
            raise AssertionError(f"paragraph not found: {prefix[:60]!r}")
        self.s = self.s[:m.start()] + new + self.s[m.end():]
        self.n += 1
        return True

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


def _structure(text):
    """Counts of the containers an edit must never disturb."""
    return {t: (len(re.findall(rf"<{t}\b", text)), len(re.findall(rf"</{t}>", text)))
            for t in ("svg", "div", "table", "figure")}


@contextmanager
def edit(path):
    original = open(path, encoding="utf-8").read()
    hed_before = HED.search(original)
    struct_before = _structure(original)
    e = _Editor(original)
    yield e

    hed_after = HED.search(e.s)
    assert (hed_before is None) == (hed_after is None), "headline element vanished"
    if hed_before:
        assert hed_before.group(1) == hed_after.group(1), (
            "HEADLINE CHANGED -- refusing to write. The RSS title and the OG card "
            "both derive from it.")

    # Structural guard, added after a hard lesson. During the readability pass a
    # regex aimed at a paragraph matched a region that STARTED INSIDE AN <svg>,
    # and deleting it took the chart's three data curves, five labels, two
    # markers, the closing </svg>, the closing </div> and a section heading with
    # it. Both affected issues then scored as PASSING -- because the unclosed
    # <svg> swallowed the rest of the article, so the checker was grading a
    # quarter of the piece. A broken figure shipped live and the metrics said
    # everything was fine. Container counts must come out unchanged.
    struct_after = _structure(e.s)
    for tag, (o_b, c_b) in struct_before.items():
        o_a, c_a = struct_after[tag]
        assert (o_a, c_a) == (o_b, c_b), (
            f"STRUCTURE CHANGED for <{tag}>: was {o_b} open/{c_b} close, "
            f"now {o_a}/{c_a}. An edit crossed a container boundary. Refusing to write.")
        assert o_a == c_a, f"<{tag}> is unbalanced ({o_a} open, {c_a} close)"

    open(path, "w", encoding="utf-8").write(e.s)
    note = f" | MISSED {len(e.missed)}: {', '.join(e.missed)}" if e.missed else ""
    print(f"  {path}: {e.n} edits, headline + structure intact{note}")
