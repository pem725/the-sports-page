# Frames — issues written before the news happens

A **frame** is a finished issue with the numbers left out.

47% of the sports year is *recurring but unscheduled* — certain to happen inside
a known window, with the actor and timing unknown. Somebody always loses in
Week 2. The trade deadline always reshuffles somebody. An MVP race always
narrows. See `tracking/editorial-calendar-2026-27.md` for the full count.

For those, the expensive part — the question, the historical base rate, the
figure, the argument, the close — can all be built months early. Only the names
and this year's numbers have to wait.

## Why they live here and not in `queue/`

`queue/` is live ammunition. Anything listed in `QUEUE_ORDER.txt` publishes at
4:30am without a human in the loop. A frame is deliberately incomplete, so it
must never sit there.

**Frames stay in `frames/` until they are filled.**

## The workflow

1. **The trigger fires.** A top-10 team loses; the deadline passes; the streak ends.
2. **Fill the slots.** Every gap is marked `{{LIKE_THIS}}`. The frame's
   `FRAME-META` block lists exactly which numbers to pull and from where.
3. **Re-verify the pre-computed evidence.** The historical figures baked into a
   frame were true when it was written. If that was six months ago, re-run the
   query in the methods note before publishing.
4. **Move it:** `git mv frames/NAME.html queue/NNN-slug.html`
5. **Add it to `QUEUE_ORDER.txt`** at the position you want.

## The safety net

`scripts/autopublish.py` refuses to publish any file still containing a
`{{SLOT}}` marker. It's a hard failure, not a warning — the job stops and you
get the alert email. A frame that sneaks into the queue half-filled cannot reach
the site.

Test it any time:

```bash
grep -o '{{[A-Z0-9_]*}}' frames/*.html | sort -u
```

## Anatomy of a frame

```html
<!-- FRAME-META
trigger:    what has to happen for this to become publishable
window:     when it is likely to fire
sport:      topic, for the variety rule
slots:      every {{SLOT}} and what goes in it
evidence:   what is already computed and baked in
recheck:    what must be re-verified before publishing
-->
```

The `PUBLISH-META` block sits below it, ready for when the file moves to `queue/`.
