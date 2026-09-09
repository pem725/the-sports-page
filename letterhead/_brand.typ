// The Sports Page letterhead, Typst.
// Palette and faces follow the website: ink #1a1208 on cream, Playfair Display
// for the masthead, Roboto Mono for the rules and meta lines.
#let ink   = rgb("#1a1208")
#let cream = rgb("#f5f0e8")
#let aged  = rgb("#e0d8c5")
#let rust  = rgb("#b83a1e")
#let muted = rgb("#6b5e4a")
#let navy  = rgb("#051954")

#let letterhead(
  recipient: none, subject: none, dateline: none, body
) = {
  set page(
    paper: "us-letter",
    margin: (top: 1.15cm, bottom: 1.5cm, left: 2.0cm, right: 2.0cm),
    fill: cream,
    footer: context [
      #set text(font: "Roboto Mono", size: 6.8pt, fill: muted)
      #line(length: 100%, stroke: 0.5pt + aged)
      #v(2pt)
      #grid(columns: (1fr, 1fr),
        align(left)[THESPORTSPAGE.NET],
        align(right)[#counter(page).display("1 of 1", both: true)])
    ],
  )
  set text(font: "Bitstream Charter", size: 10pt, fill: ink, lang: "en")
  set par(justify: false, leading: 0.66em)
  show par: set block(spacing: 0.85em)
  show heading: set text(font: "Playfair Display", weight: 700, size: 11.5pt)
  show heading: set block(above: 12pt, below: 6pt)

  // masthead
  align(center, image("banner-trimmed.png", width: 44%))
  v(-2pt)
  align(center, text(font: "Roboto Mono", size: 6.6pt, fill: muted, tracking: 1.6pt,
    upper("A daily statistics newspaper  ·  Published every day since Opening Day 2026")))
  v(6pt)
  line(length: 100%, stroke: 1.6pt + ink)
  v(1.6pt)
  line(length: 100%, stroke: 0.5pt + ink)
  v(11pt)

  if dateline != none {
    text(font: "Roboto Mono", size: 8pt, fill: muted, tracking: 0.8pt, upper(dateline))
    v(10pt)
  }
  if recipient != none { recipient; v(8pt) }
  if subject != none {
    block(inset: (left: 9pt), stroke: (left: 2.2pt + rust))[
      #text(font: "Playfair Display", weight: 700, size: 11.5pt, subject)
    ]
    v(10pt)
  }
  body
}

#let signoff(name, title, contact) = {
  v(9pt)
  text[Sincerely,]
  v(19pt)
  text(font: "Playfair Display", weight: 700, size: 12pt, name)
  linebreak()
  text(size: 9pt, fill: muted, style: "italic", title)
  linebreak()
  text(font: "Roboto Mono", size: 7.6pt, fill: muted, contact)
}

#let colophon(body) = {
  v(9pt)
  line(length: 100%, stroke: 0.5pt + aged)
  v(5pt)
  text(size: 8pt, fill: muted, style: "italic", body)
}
