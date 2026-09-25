Fellas — we just opened the engine.

https://thesportspage.net/engine.html

Everything about how this paper gets made is now public. Not a
puff piece. The architecture, the daily run, the metric that
picks the story, the seven automated checks — and a full list
of everything that broke.

━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY

Statistics is the most useful thing almost nobody gets taught
properly, and it's sold as a specialism: priced, credentialed,
kept behind institutions. Sport is the smuggling route. People
already argue about numbers on a Sunday — they have the
intuitions, they just don't have the words.

Give them the words using something they already care about,
and the skill goes home with them. To a medical decision. A
mortgage. A ballot. A headline.

No paywall, no silo, no credential. The skills are the product
and the product is free.

━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT'S ON IT

Every number measured from the repo this morning, not guessed:

  180 issues in 181 days · 6.96 a week
  longest gap between issues: 3 days
  75 scripts · 15,718 lines
  719 commits since March 29
  1 person writing it

Plus the honest split of who does what. The editor decides what
matters and owns being wrong in public. The machine makes being
wrong *discoverable* — which is the only reason the first part
is possible.

━━━━━━━━━━━━━━━━━━━━━━━━━━

THE PART I'D ACTUALLY READ

The failure log. Seven real incidents, all in the git history:

· A fabricated poll ranking led a Sunday edition. The poll did
  not exist. Every surrounding fact was true, which is exactly
  what let the false one survive.
· A model went 15 for 15 — because it graded past games on
  ratings that had already absorbed those games.
· 51 social cards used the wrong typeface for months. Nobody
  reported it because a plausible serif looks fine.
· One superscript-two silently destroyed a card image.
· The topic icons rendered at 642 pixels. They were drawn for 20.
· 23 issues printed the share block twice.

The through-line, which is the actual lesson:

  The failures that survive are the ones that still look fine.
  Nothing was blank, nothing errored. Everything rendered as a
  slightly worse version of the intended thing.

Which is why "be more careful" is never the answer. Careful has
already failed by the time you find out.

━━━━━━━━━━━━━━━━━━━━━━━━━━

AND THE LINE THIS IS ALL BUILT ON

  We question uncertainty with curiosity,
  but we brave uncertainty with purpose.

Two different jobs, and most people only ever get taught the
first one.

━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT I WANT FROM YOU

1. Read the failure log and tell me what's missing. If you
   remember something breaking that isn't on there, it belongs
   on there. Nothing gets quietly dropped once it's fixed.

2. Is the "take it" section actually usable? It says you need a
   subject you know better than your reader, a primary data
   feed, a willingness to publish your misses, and two weeks.
   Not a newsroom, not a budget. Is that true, or am I
   underselling the work?

3. Who should see this? If you know somebody in a newsroom
   wondering whether any of this works — send it. That's what
   it's for.
