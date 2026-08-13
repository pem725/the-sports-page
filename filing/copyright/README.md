# Copyright registration — the package and the plan

**This is research and preparation, not legal advice.** Everything below comes
from the Copyright Office's own published rules, cited inline. A lawyer should
confirm the two open questions at the bottom before anything is filed.

---

## First, the thing that needs correcting

> *"I know they're only good for ninety days."*

Close, and the instinct is a good one — but it is about a different thing than it
sounds like, and the difference matters.

**Copyright is not good for ninety days. It already exists, automatically, for
life plus seventy years.** Every issue was protected the instant it was written.
Nothing has expired, nothing is unprotected, and nothing is at risk of lapsing.

What the ninety days actually is: **17 U.S.C. § 412**. To claim **statutory
damages and attorney's fees**, a published work must be registered either *before
the infringement began* or *within three months of first publication*. Miss that
window and you can still sue — you are just limited to proving **actual damages**.

For a free newsletter, actual damages are approximately **zero**. Nobody paid for
it, so nothing was lost in dollars. Which means:

> **For this project, statutory damages are not a bonus on top of the remedy.
> They are the entire remedy.** § 412 timeliness is close to the whole value of
> registering at all.

That reframes the priority. The point of registering is not to *obtain* copyright
— you have it. The point is to stay inside the three-month window so an
infringement is worth doing something about.

---

## The vehicle: GRTX

The Copyright Office has a group option built for exactly this shape of
publication: **Group Registration of Short Online Literary Works**
([Circular 67](https://www.copyright.gov/circs/circ67.pdf),
[FAQ](https://www.copyright.gov/grtx/faq.pdf)).

| | |
|---|---|
| **Works per application** | 2–50 |
| **Length per work** | 50–17,500 words |
| **Publication window** | all works published within **three consecutive calendar months** |
| **Authorship** | same individual author(s), named as claimant |
| **Fee** | **$65 per application** ([fee schedule](https://www.copyright.gov/about/fees.html)) |
| **Deposit** | one file per work, in a single ZIP, plus a form listing title, filename, publication date and word count |

Every issue and every concept primer we have published qualifies. At $65 for
fifty works, the entire back catalogue — **167 works** — costs **$390**.

Note the elegant coincidence: **GRTX's three-month window and § 412's three-month
window are the same three months.** File on a three-month rhythm and the group
rule and the damages rule are satisfied by the same act.

### Why not GRNW

There is a newer option, [Group Registration of Updates to a News
Website](https://www.copyright.gov/registration/grnw/Group-Registration-of-Updates-to-a-News-Websites-GRNW-Frequently-Asked-Questions.pdf)
(GRNW, $95). It looks tempting for a daily publication. It does not fit, for
three independent reasons — any one of which is fatal:

1. **"News website" is defined narrowly.** It must carry "a broad range of news
   on all subjects" and be "**not limited to any specific subject matter**."
   The Sports Page is limited to one subject on purpose.
2. **Every update must be a work made for hire.** Ours are not.
3. **The claim in each update is limited to the collective work** — so it would
   register the *arrangement of the site*, not the issues themselves. That is the
   opposite of what we want protected.

Ruled out on the merits, not on cost.

---

## Tim was right about the images

**GRTX covers the text and only the text.** The FAQ is explicit: artwork,
photographs, illustrations and charts are *not* covered.

That is a real gap here, not a technicality. **140 of our 141 published pieces
carry an original inline SVG figure**, and the house rule is that every issue gets
one. Those figures are original visual authorship — often the most distinctive
thing on the page, and the part most likely to be lifted and reposted without the
words around it. A GRTX registration would not reach them.

So the visual work needs its own answer, and the honest options are:

| Route | Cost | Verdict |
|---|---|---|
| Standard Application per issue, claiming text **and** artwork | $65 × 141 = **$9,165** | Complete, and absurd at this scale |
| Group of Unpublished Works (GRUW), 10 works, **before** publication | $85 per 10 → ~$1,190/yr | Workable going forward, awkward, and only for figures registered pre-publication |
| Register nothing extra; rely on automatic copyright and register a specific figure if it is ever infringed | $0 now, $45–65 later | Loses § 412 for infringement before that filing |
| Register a short list of flagship figures individually | $45 each | Cheap, targeted |

**Recommendation, for the lawyer to confirm:** GRTX everything for the text, and
do *not* attempt to register 141 figures. Instead pick the handful of figures with
standalone value — the ones designed to be screenshot and shared on their own —
and register those individually as visual arts works. Automatic copyright still
covers the rest; what is lost is only statutory damages for infringement
occurring before a later filing.

**Also register the logo** as a visual arts work. $45 on the single-work
application (single author, one work, not for hire). It is the same asset as the
trademark drawing in `../` and it is the thing a reader recognises. Cheap, and it
is the one image with obvious independent commercial value.

---

## What is in this folder

Everything below is generated by `scripts/build_copyright_manifest.py` directly
from the repository, so no date or word count is ever typed by hand into a
government form signed under penalty of perjury.

```
manifest.csv        every published work: title, filename, publication date,
                    word count, GRTX eligibility, and any discrepancy noted
summary.json        counts, per-application batching, total fee
deposits/           one plain-text copy per work -- the actual deposit material
batches/<app>/      one folder per application:
                      works.csv    title / filename / date / word count
                      deposit.zip  exactly the files in that application
```

### The applications, ready to file

| Application | Works | Published | Fee |
|---|---|---|---|
| `2026-Q1` | 2 | 27–29 Mar 2026 | $65 |
| `2026-Q2-1of3` | 50 | 1 Apr – 15 May 2026 | $65 |
| `2026-Q2-2of3` | 50 | 16 May – 21 Jun 2026 | $65 |
| `2026-Q2-3of3` | 9 | 22–30 Jun 2026 | $65 |
| `2026-Q3-1of2` | 50 | 1 Jul – 6 Aug 2026 | $65 |
| `2026-Q3-2of2` | 6 | 7–12 Aug 2026 | $65 |
| **Total** | **167** | | **$390** |

Quarters are split because the ceiling is 50 works per application. Every part
sits inside the same three-calendar-month window, so each is independently valid.

**167 works, not 141.** The first pass covered `published/` only and missed the
**26 concept primers** in `concepts/`. They are separately authored, separately
reachable original text, and because the fee is per *application* rather than per
work, including them cost one extra application — $65 — rather than 26 fees.

### On the publication dates — how they were derived, and what went wrong twice

The publication date is a sworn fact, so it was worth getting right rather than
approximately right. Three rules were tried:

1. **Git history with `--follow`** — returned the date the *draft* was created in
   `queue/`, sometimes weeks before publication. Wrong.
2. **`--follow` at all** — actively dangerous on this repository. Every issue
   shares the same CSS and masthead, so git's similarity heuristic matches
   unrelated files: it traced `011-infield-hitting` back through
   `queue/005-draft-combinatorics` to `mets_500_newsletter` on a 60% match.
   **Three different works.** A fuzzy match cannot underwrite a sworn date.
3. **Add-date of the `published/` path, no follow** — right for almost everything,
   but wrong for issues 001 and 002, which went live at the repository root on
   **29 March 2026** and were only moved into `published/` during the 2 April
   restructure. That rule reported them four days late.

The rule now used: build the full add/rename history in one pass, then chase
renames **one explicit step at a time**, stopping at the first path that was
publicly reachable — treating `queue/`, `reserve/` and `frames/` as non-public.
This reproduces the printed issue date for every work that has one.

**137 of the 167 dates come straight off the printed datebar.** The 26 primers
carry no datebar by design and take their date from git, which is expected rather
than a discrepancy. Four issue files also lack one and are flagged for review: the
`-deeper` companion pages for issues 020, 022, 027 and 034. They are reachable by URL but
are not linked from the index; they are included as separate works because they
are separately authored text, publicly available.

---

## The going-forward cadence — and why monthly, not quarterly

The back catalogue is one thing. The habit is what actually matters.

At the current rate (**6.92 issues/week**, about 30 a month, 90 a quarter):

| Cadence | Applications/yr | Cost/yr | § 412 exposure |
|---|---|---|---|
| **Monthly** | 12 | **$780** | None. Oldest work in each filing is ~31 days. |
| Quarterly | 8 (the 50-cap forces two per quarter) | $520 | Real. Filing even one day after quarter end puts the first day's issue outside three months. |

**Monthly is the recommendation.** It costs $260/year more and removes the edge
case entirely. Quarterly filing only stays timely if the application goes in on
the *first day* after the quarter closes, every quarter, forever — and the one
quarter it slips is the quarter that matters.

Set it as a recurring task: **first business day of each month, file the previous
month.** The script regenerates the batch folder; the filing itself takes minutes.

To switch the batching from quarters to months, change `quarter()` in
`scripts/build_copyright_manifest.py`.

---

## What registering now does and does not buy

Worth being straight about, because most of the catalogue is already outside its
three-month window:

- **Does not** restore § 412 for infringement that happened before registration.
  For issues published in April, that window shut in July.
- **Does** make statutory damages available for any infringement that **begins
  after** the registration date — which is all of the risk that actually lies
  ahead, especially with a marketing campaign coming.
- **Does** satisfy 17 U.S.C. § 411, which requires registration before a US
  author can file an infringement suit at all. Without it there is no case to
  bring, whatever the merits.
- **Does** create a public record with a presumption of validity.

So the lost window is not a reason to delay. It is a reason to file now and then
never fall behind again.

---

## Open questions for the attorney

1. **Do the four `-deeper` pages and the 26 concept primers count as separate
   works, or as parts of the issues they extend?** They are separately reachable
   and separately authored, so registering them separately is the safer reading
   and is what this package does. If the Office views a primer as part of the
   issue that links to it, the claim is merely redundant rather than wrong.
2. **For statutory damages, does a group registration yield one award per work,
   or one for the group?** § 504(c) treats "all the parts of a compilation" as
   one work. GRTX creates a separate registration for each work, which should
   mean separate awards — but this is exactly the kind of point that decides
   whether a case is worth bringing, and it should not rest on my reading.
3. Whether the **non-commercial licence** on the site interacts with any of this
   the way it does with the trademark question — see `corpus/trademark-prep.md` §4.

---

## Not yet covered by this package

Stated plainly so nothing is assumed done that isn't:

- **The figures.** See above — deliberately deferred pending a decision.
- **The Sunday Edition prediction scorecards** are inside the issues, so they are
  covered as text.
- **`index.html` as a collective work** — the selection and arrangement of the
  archive is separately copyrightable. Low value, not pursued.

---

*I cannot file any of this. Registration requires the applicant's certification,
the applicant's signature, and the applicant's payment. The package is built so
that filing is data entry and an upload, not a research project.*

*Regenerate: `python3 scripts/build_copyright_manifest.py` (needs `beautifulsoup4`).*
