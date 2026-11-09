# Sealed commitment — Bills at Vikings, Nov 9, 2026

**SHA-256**

    b065f9c0810c1f46e5cda60790f97d0944f17abeb1150cff0eeb63ad896e05ac

| | |
|---|---|
| sealed at | `2026-11-09T15:18:35-05:00` |
| unlocks | `2026-11-10T00:30` (after the game) |
| covers | `nfl-2026-11-09-bills-vikings.md` |
| vault | outside the repository, not in git |

The editor's call and ours for Monday night's No. 1 scoring offense against No. 1
scoring defense, plus a test fixed in advance for his "defense needs two looks"
hypothesis. Written before kickoff and held outside this repository; the digest
above is of its exact bytes. Graded in the Nov 15 Sunday Edition.

Sealed by hand rather than with `scripts/seal.py`, which keys every seal to a
pool week, and week 10 is already taken. Same mechanism: to check the text was not
edited after the unlock, run

    sha256sum tracking/sealed/nfl-2026-11-09-bills-vikings.md

and compare it with the hash above.
