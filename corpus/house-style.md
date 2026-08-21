# House style — derived from Patrick's teaching voice

Not invented. **Measured**, on 20 August 2026, by comparing 52,069 words of
`GradStats-Book` (his own teaching prose) against 203,522 words of the newsletter
across 175 published works. Every number below is reproducible with
`scripts/check_voice.py`.

---

## The headline finding: the problem is person, not punctuation

| Feature | Newsletter /1k | Book /1k | |
|---|---|---|---|
| **you / your** | 5.91 | **15.67** | 2.7× too low |
| **we / us / our** | 3.34 | **8.44** | 2.5× too low |
| **Let us / let's** | 0.02 | **0.58** | 29× too low |
| **imperatives** (Ask, Notice, Watch, Hold onto) | 0.23 | **1.20** | 5× too low |
| I / my | 0.76 | 0.84 | fine |

**The newsletter writes *about* sport. He writes *to* a student.** That is the
single largest difference between the two corpora, and it is the one worth fixing
first. His prose is a person leaning over your shoulder: *"Hold onto that
sentence."* *"That 20% should bother you."* *"You cannot buy fewer false alarms
and more hits for free."*

## What is NOT wrong, and nearly got "fixed"

| Feature | Newsletter /1k | Book /1k |
|---|---|---|
| dash asides (— or spaced hyphen) | 12.25 | **15.94** |
| mid-sentence colon | 7.76 | 10.52 |

The first pass measured em dashes alone and found 12.06 vs 0.06 — an apparently
damning 200× overuse, the classic AI tell. It was an artifact. **He uses the dash
aside slightly more often than the newsletter does; he simply types it as a spaced
hyphen** rather than an em dash. Scrubbing them would have removed his own voice
and replaced it with nothing.

Semicolons are the one punctuation gap worth closing: **4.51 in the book, 1.83 in
the newsletter.** He reaches for a semicolon where the newsletter starts a new
sentence.

## The classic AI tells are already absent

Measured across all 175 works, from the `humanizer` skill's list:

| Tell | Count |
|---|---|
| "it is worth noting" / "important to note" | **0** |
| "underscores" / "highlights the importance" | **0** |
| "testament to" / "pivotal" / "vital role" | **0** |
| "delve" / "tapestry" / "multifaceted" | **0** |

So "scrub the AI tells" is not the job it sounds like. The prose is not full of
chatbot slop. It is full of **a small number of rhetorical moves repeated until
they became a tic** — and most of those are mine, not a model's default.

## The real tic list, with counts

| Move | Uses | Files |
|---|---|---|
| `X is not A. It is B.` (antithesis) | **104** | 77 |
| "exactly" | **182** | 96 |
| "quietly" | 49 | 41 |
| "genuinely" | 36 | 31 |
| "precisely" | 28 | 26 |
| "Here is the …" as an opener | 27 | 27 |
| "the shape of" / "the same shape" | 17 | 15 |
| rule of three (`a, b, and c.`) | 17 | 15 |
| "engineered to" / "built to" | 12 | 12 |

The antithesis is the worst of it. **It appears in 77 of 175 works** — nearly
every other piece reaches the same closing gesture. Once it is a formula the
reader stops hearing it as emphasis and starts hearing it as filler.

None of these words is banned. A tic is a *frequency* problem. Use "exactly" when
you mean exactly; do not use it as a rhythm filler nine times a month.

---

## The moves worth borrowing

These are his, they are distinctive, and the newsletter mostly lacks them.

1. **Name the misconception first, then correct it.**
   > *"We often label our efforts 'hypothesis testing.' Here we dispel that myth
   > and talk about what we are actually doing."*

2. **Address the reader directly and often.** Second person is the default, not a
   flourish.

3. **Tell them what they will be able to do.** Every chapter opens with numbered
   objectives. The newsletter's Reader's Contract is the same instinct.

4. **Admit your own past error, by name.**
   > *"…it is exactly backwards in a lot of lecture notes, including an old
   > version of mine."*
   This is the most humanising move in the whole book and the newsletter has
   almost none of it.

5. **Bold the term, italicise the pivot.** `**not** a test of your hypothesis`.
   The bold carries the vocabulary, the italic carries the argument.

6. **Rhetorical question, then answer it immediately.**
   > *"Why bother guessing at all? Because power protects the things you care
   > about."*

7. **Homely, physical analogies.** A scale that reads five pounds heavy. Not
   abstractions.

8. **Name the stakes concretely.** Not "resources" but *"funding, your time,
   scarce participants."*

9. **Dry, deadpan humour, never a joke for its own sake.**
   > *"It is deliberately boring."*

10. **Say the hard part plainly rather than hedging it.**
    > *"That 20% should bother you."*

---

## Checking

```
python3 scripts/check_voice.py queue/NNN-slug.html
python3 scripts/check_voice.py --corpus published/     # whole-corpus tic counts
```

It reports person density against the book's targets and flags the tic list. Like
the readability checker, it measures **presence and frequency, not quality** — it
cannot tell a well-earned "exactly" from a lazy one. It tells you where to look.
