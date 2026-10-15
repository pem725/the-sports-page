/* The section bar: one slim, pinned row of the paper's permanent features.

   ONE SOURCE OF TRUTH. Every page that wants the bar carries a single line,
     <script src="assets/sitenav.js" defer></script>
   (relative: "assets/sitenav.js" from the root, "../assets/sitenav.js" one level
   down) and nothing else. The script path is relative so it loads on both hosts;
   the LINKS it writes are absolute. The markup AND its styles are injected from here, because
   this repo has already broken three components by copying markup into a page
   whose stylesheet did not travel with it (glyphs, OG entities, the share
   panel). A bar that brings its own CSS cannot lose it.

   CLUTTER RULE (editor, 2026-09-25 and again 2026-10-15): this bar holds the
   PERMANENT features only. A new feature earns a button here by being something
   a reader returns to, not something we want to promote this week. Keep it to
   one line on a phone; past six items it scrolls sideways, and that is the
   signal to cut something rather than shrink the type. */
(function () {
  if (document.getElementById('sitenav')) return;
  var BASE = 'https://thesportspage.net/';
  var items = [
    /* label, short label for phones, path, matches-current-page */
    ['Home',        'Home',  '',           /^\/?(index\.html)?$/],
    ['Odds Board',  'Odds',  'odds.html',  /odds\.html$/],
    ['Pool Desk',   'Pool',  'pool/',      /\/pool\/?(index\.html)?$/],
    ['Ask The Sports Page', 'Ask', 'ask.html', /ask\.html$/],
    ['About',       'About', 'about.html', /about\.html$/]
  ];
  var path = location.pathname.replace(/^\/the-sports-page/, '');

  var css = document.createElement('style');
  css.textContent =
    '#sitenav{position:sticky;top:0;z-index:60;background:#1a1208;max-width:820px;margin:.5rem auto 0;' +
      'box-shadow:0 2px 10px rgba(0,0,0,.18)}' +
    '#sitenav .sn-row{display:flex;align-items:stretch;overflow-x:auto;scrollbar-width:none;' +
      'font-family:"Roboto Mono",monospace;font-size:.66rem;letter-spacing:.12em;text-transform:uppercase}' +
    '#sitenav .sn-row::-webkit-scrollbar{display:none}' +
    '#sitenav a{flex:0 0 auto;color:#e0d8c5;text-decoration:none;padding:.62rem .95rem;border:none;' +
      'border-right:1px solid rgba(224,216,197,.14);white-space:nowrap;transition:background .15s,color .15s}' +
    '#sitenav a:hover,#sitenav a:focus-visible{background:#2c4a6e;color:#f5f0e8;outline:none}' +
    '#sitenav a[aria-current="page"]{color:#c9962a;box-shadow:inset 0 -3px 0 #c9962a}' +
    '#sitenav .sn-sub{margin-left:auto;background:#b83a1e;color:#fff;font-weight:600;border-right:none}' +
    '#sitenav .sn-sub:hover{background:#962f17}' +
    '#sitenav .sn-s{display:none}' +
    '#sitenav button.sn-sub{font:inherit;letter-spacing:inherit;text-transform:inherit;cursor:pointer;flex:0 0 auto;' +
      'padding:.62rem .95rem;border:none;white-space:nowrap}' +
    '#sitenav button.sn-sub[aria-expanded="true"]{background:#962f17}' +
    '#sitenav .sn-drop{background:#f5f0e8;border:2px solid #b83a1e;border-top:none;padding:1.1rem 2.4rem 1rem 1.3rem;' +
      'display:grid;grid-template-columns:1fr auto;gap:1.2rem;align-items:center;color:#1a1208;position:relative}' +
    '#sitenav .sn-drop[hidden]{display:none}' +
    '#sitenav .sn-drop h3{font-family:"Playfair Display",serif;font-size:1.1rem;font-weight:700;color:#b83a1e;margin:0 0 .25rem}' +
    '#sitenav .sn-drop p{font-family:"Libre Baskerville",serif;font-size:.86rem;font-style:italic;color:#6b5e4a;margin:0 0 .75rem}' +
    '#sitenav .sn-drop form{display:flex;flex-wrap:wrap;gap:.5rem}' +
    '#sitenav .sn-drop input[type=email]{flex:1 1 200px;font-family:"Libre Baskerville",serif;font-size:.95rem;' +
      'padding:.5rem .75rem;border:1px solid #c8bca4;background:#fff;color:#1a1208;min-width:0}' +
    '#sitenav .sn-drop button[type=submit]{background:#b83a1e;color:#fff;font-family:"Roboto Mono",monospace;font-size:.72rem;' +
      'font-weight:600;letter-spacing:.14em;text-transform:uppercase;border:none;padding:.5rem 1.2rem;cursor:pointer}' +
    '#sitenav .sn-fine{font-family:"Roboto Mono",monospace;font-size:.62rem;letter-spacing:.05em;color:#6b5e4a;margin-top:.55rem}' +
    '#sitenav .sn-qr{text-align:center;font-family:"Roboto Mono",monospace;font-size:.58rem;letter-spacing:.1em;' +
      'text-transform:uppercase;color:#6b5e4a}' +
    '#sitenav .sn-qr img{width:110px;height:110px;display:block;border:5px solid #b83a1e;padding:3px;background:#fff;margin-bottom:.3rem}' +
    '#sitenav .sn-x{position:absolute;top:.3rem;right:.5rem;background:none;border:none;font-size:1.3rem;line-height:1;' +
      'color:#6b5e4a;cursor:pointer;padding:.2rem .4rem}' +
    '@media(max-width:520px){#sitenav a,#sitenav button.sn-sub{padding:.6rem .62rem;letter-spacing:.06em}' +
      '#sitenav .sn-drop{grid-template-columns:1fr}#sitenav .sn-qr{display:none}#sitenav .sn-l{display:none}#sitenav .sn-s{display:inline}}';
  document.head.appendChild(css);

  var nav = document.createElement('nav');
  nav.id = 'sitenav';
  nav.setAttribute('aria-label', 'Sections');
  var row = document.createElement('div');
  row.className = 'sn-row';
  items.forEach(function (it) {
    var a = document.createElement('a');
    a.href = BASE + it[2];
    a.innerHTML = '<span class="sn-l">' + it[0] + '</span><span class="sn-s">' + it[1] + '</span>';
    a.target = '_blank'; a.rel = 'noopener';   /* house rule: real links open a new tab */
    if (it[3].test(path)) a.setAttribute('aria-current', 'page');
    row.appendChild(a);
  });
  /* Subscribe is not a link to another page: it drops the sign-up form (and the
     scan-to-subscribe code) down from the bar, on whatever page the reader is on.
     Editor, 2026-10-15: "when you click subscribe, the little scan thing comes
     down. Make it so that it's easy." The homepage no longer carries its own
     subscribe panel, so this is the only one. */
  var sub = document.createElement('button');
  sub.type = 'button';
  sub.className = 'sn-sub';
  sub.textContent = 'Subscribe';
  sub.setAttribute('aria-expanded', 'false');
  sub.setAttribute('aria-controls', 'sn-drop');
  row.appendChild(sub);
  nav.appendChild(row);

  var drop = document.createElement('div');
  drop.className = 'sn-drop';
  drop.id = 'sn-drop';
  drop.hidden = true;
  drop.innerHTML =
    '<div><h3>Get The Sports Page in Your Inbox</h3>' +
    '<p>Five issues a week. The Sunday Edition grades the predictions. Free.</p>' +
    '<form action="https://buttondown.com/api/emails/embed-subscribe/thesportspage" method="POST" target="_blank">' +
      '<input type="email" name="email" placeholder="you@email.com" required autocomplete="email" aria-label="Email address">' +
      '<input type="hidden" value="1" name="embed">' +
      '<button type="submit">Sign me up</button></form>' +
    '<div class="sn-fine">No spam. Unsubscribe anytime. Powered by Buttondown.</div></div>' +
    '<div class="sn-qr"><img src="' + BASE + 'assets/qr-subscribe.png" alt="Scan to subscribe" width="110" height="110">Scan to subscribe</div>' +
    '<button type="button" class="sn-x" aria-label="Close">&times;</button>';
  nav.appendChild(drop);

  function setOpen(open) {
    drop.hidden = !open;
    sub.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) { var f = drop.querySelector('input[type=email]'); if (f) f.focus({ preventScroll: true }); }
  }
  sub.addEventListener('click', function () { setOpen(drop.hidden); });
  drop.querySelector('.sn-x').addEventListener('click', function () { setOpen(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setOpen(false); });
  document.addEventListener('click', function (e) { if (!nav.contains(e.target)) setOpen(false); });
  /* Old links to the homepage's #subscribe panel still land on an open form. */
  if (location.hash === '#subscribe') setOpen(true);

  /* Sit directly under the masthead when there is one; otherwise at the top. */
  var mast = document.querySelector('.masthead');
  if (mast && mast.parentNode) {
    /* Match the page's own column: the odds board runs wider than an issue. */
    var mw = getComputedStyle(mast).maxWidth;
    if (mw && mw !== 'none') nav.style.maxWidth = mw;
    mast.parentNode.insertBefore(nav, mast.nextSibling);
  }
  else document.body.insertBefore(nav, document.body.firstChild);
})();
