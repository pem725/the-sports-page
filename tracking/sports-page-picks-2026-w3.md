# The Sports Page — Week 3 entry — reasoning

Submitted 2026-09-15, before any Week 3 game kicked off. Committed to git at the
time of entry, which is the point: a timestamped commit *proves* the reasoning
existed beforehand rather than asserting it.

## The method, stated in advance

**Side:** whichever team our SP+ rating — frozen before kickoff by
`scripts/snapshot_ratings.py` — makes the better value against the mean closing
line. Home field 2.5 points. Nothing else.

**No edge is claimed.** Issue #154 measured this exact method across 2,140 games:
51.0% against the spread, 95% interval 48.9%–53.1%, break-even 52.4%. It also
found the confidence ranking *flat* across edge bands — a bigger disagreement with
the line does not produce a better result. This entry exists to be graded against
a human's eye test, not to win money.

**Tiebreaker:** 53, the mean market over/under for Houston at Texas Tech. No
opinion of our own; the market's number is better than one we would invent.

## What the model liked, in order of disagreement with the line

| our side | line | edge | public on our side |
|---|---:|---:|---:|
| South Carolina | −3.5 | +5.9 | 45% |
| Kansas | +5.5 | +4.9 | 35% |
| James Madison | +2.5 | +4.5 | 65% |
| Northwestern | −3.5 | +3.1 | 31% |
| UConn | −3.5 | +3.0 | 46% |
| LSU | −3.5 | +2.9 | 61% |
| Florida | −2.5 | +2.7 | 61% |
| Texas Tech | −7.5 | +2.5 | 47% |
| Maryland | +3.5 | +2.0 | 28% |
| Texas State | −2.5 | +1.6 | 38% |
| Wyoming | +0.5 | +1.2 | 49% |
| Vanderbilt | −3.5 | +1.1 | 80% |
| Clemson | −3.5 | +0.7 | 44% |
| SMU | +1.5 | +0.2 | 57% |
| East Carolina | +2.5 | +0.2 | 53% |
| *Ohio / South Alabama* | — | **0.0** | — |

Ohio–South Alabama was the one game we had no opinion on at all, so the intention
was to drop it.

## What actually got entered, and where it deviates

**This matters and it is not a footnote.** The entry does not fully match the
method above, and pretending otherwise would poison the comparison.

CBS assigns confidence points **by row position**, and rows are reordered by
dragging. The drag interface would not respond to synthetic events, real
keypresses, or the accessibility path, and after several attempts I stopped rather
than keep manipulating a live pool entry. Two consequences:

1. **The confidence order is by kickoff time, not by edge.** Texas Tech got 15
   points and South Carolina — our largest edge of the week — got 7. That is not
   the stated method. By our own evidence the ranking is flat anyway, so the
   expected cost is near zero; but it is a deviation and it is on the record.
2. **We play South Alabama and dropped James Madison.** The site kept placing the
   unpicked game in a live scoring slot, at one point stranding 13 points on a game
   we had not picked. Given the choice between a no-opinion pick in a scoring slot
   and a wanted pick earning nothing, the first is worth more. So the game we
   meant to drop is in at 4 points, and a +4.5 edge is out.

Net: the *sides* are the model's on fourteen of fifteen games. The *weights* are
the calendar's.

## The honest expectation

Somewhere around 7 or 8 correct out of 15. That is what a coin flip looks like and
what #154 says to expect. If this entry wins the week it will be luck, and we will
say so; if it loses badly it will also be luck. The interesting number is not this
week, it is the calibration curve in November across every band.

## The one thing the model cannot see

The editor's Virginia Tech pick rests on James Franklin being passed over for the
Maryland job years ago, recruiting against them from Penn State ever since, and
having now told the Virginia Tech fanbase to fill a stadium whose own students do
not attend. No rating system on earth represents that. Our model has **Maryland**
by two points and would never know to ask.

That is the whole experiment. A number that cannot see a grudge, against a person
who cannot see 2,140 games.

## Protocol from Week 4

This week the editor submitted first, so there was nothing to conceal. From next
week the order reverses: **The Sports Page enters and commits its reasoning before
looking at anyone else's slate.** If a sealed version is wanted, commit the
SHA-256 of this file at entry time and publish the text after kickoff — the hash
proves it, and nobody has to take our word for it.
