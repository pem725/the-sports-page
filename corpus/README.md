# Corpus — how The Sports Page got made

This directory is the project's memory of its own process.

The published issues are the output. This is the input: the raw material people
contributed, the ideas that started threads, the datasets that shaped the
editorial calendar, and the reasoning behind decisions that are otherwise
invisible once a piece ships.

## Why it exists

Binary files — PDFs, spreadsheets, saved articles — are excluded by
`.gitignore` and always will be. They bloat the repo, they don't diff, and
GitHub Pages would serve them.

But the *content* of those files is part of the record. So the rule is:

> **The binary stays out. The material comes in, as JSON or Markdown.**

Anything contributed to the project gets transcribed into a durable, diffable,
plain-text form and lands here with its provenance attached.

## Layout

```
corpus/
  README.md            <- this file
  founders.md          <- who made this, and what each person contributed
  source-materials/    <- contributed data and documents, transcribed
```

## Provenance

Every file in `source-materials/` carries a header saying what it came from and
who contributed it. That attribution is the point. A dataset with no name on it
is just a file; a dataset with a name on it is a piece of the story.

## Related, elsewhere in the repo

- `data/` — cleaned, machine-readable datasets derived from these sources
- `tracking/` — live planning documents and project state
- `concepts/` — the statistical primers the issues link to

The corpus holds what came *in*. `data/` holds what we made *of* it.
