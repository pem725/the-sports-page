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
    ['Ask',         'Ask',   'ask.html',   /ask\.html$/],
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
    '#sitenav a.sn-sub{margin-left:auto;background:#b83a1e;color:#fff;font-weight:600;border-right:none}' +
    '#sitenav a.sn-sub:hover{background:#962f17}' +
    '#sitenav .sn-s{display:none}' +
    '@media(max-width:520px){#sitenav a{padding:.6rem .62rem;letter-spacing:.06em}#sitenav .sn-l{display:none}#sitenav .sn-s{display:inline}}';
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
  var sub = document.createElement('a');
  sub.className = 'sn-sub';
  sub.href = BASE + '#subscribe';
  sub.textContent = 'Subscribe';
  sub.target = '_blank'; sub.rel = 'noopener';
  row.appendChild(sub);
  nav.appendChild(row);

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
