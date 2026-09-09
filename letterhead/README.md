# Letterhead

Business correspondence on the newspaper's own furniture, built with the same
toolchain as everything else here: **Quarto's Typst engine**. No LaTeX, no Word,
no hand-fiddling in a PDF editor.

```bash
quarto typst compile ces-media-credential.typ out.pdf
```

## Making a new letter

Copy any `.typ` in this folder, change the body. The whole design lives in
`_brand.typ`, so a new letter is prose and nothing else:

```typst
#import "_brand.typ": *

#show: letterhead.with(
  dateline: "9 September 2026",
  recipient: [Name \ Organisation],
  subject: [What this is about],
)

Body text. *Bold* and _italic_ work as normal.

= A section heading

#signoff(
  "Patrick E. McKnight, PhD",
  "Owner and Managing Editor, The Sports Page",
  "ideas" + "@" + "thesportspage.net  ·  thesportspage.net",
)

#colophon[A closing note, set small.]
```

## Two things that will bite you

**Write the email address as `"ideas" + "@" + "..."`.** Typst treats a bare `@`
as a citation reference, and escaping it as `\@` prints the backslash. The first
draft of the CES letter went out reading `ideas\@thesportspage.net`.

**Use `banner-trimmed.png`, not `banner.png`.** The original ships with its own
cream background (`#f9f2de`), which is a shade off the page and draws a visible
rectangle around the masthead. The trimmed copy has that background removed, so
the mark sits directly on the paper.

## Faces

| Role | Face | Note |
|---|---|---|
| Masthead, headings | Playfair Display | the site face |
| Meta lines, rules | Roboto Mono | the site face |
| Body | **Bitstream Charter** | a substitution — see below |

The site sets body copy in Libre Baskerville, and only its *italic* is
installable on this machine; Google no longer serves the regular weight through
any endpoint that worked here. Charter is Matthew Carter's print serif, designed
for exactly this — long body text at small sizes on paper — and is a closer match
in colour and rhythm than any of the alternatives available. If Libre Baskerville
Regular is ever installed, change one line in `_brand.typ`.

## Keep it to one page

A cover letter that runs to two pages reads as a document rather than a letter.
`_brand.typ` is tuned so a page of prose fits; if you overrun, cut words before
you cut leading.
