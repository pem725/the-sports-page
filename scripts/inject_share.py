#!/usr/bin/env python3
"""inject_share.py — Insert/refresh the unified share section + Open Graph meta tags.

Two usages:

  1. As a library — autopublish.py and other scripts import `inject_into(path)`
     to add the share section to a single file right before commit.

  2. As a script — run directly to refresh share-section markup across every
     queued and published issue. Useful when the share-section design changes.

Idempotent: if a share section is already present, it gets replaced with the
current canonical version. OG meta tags are inserted once and updated on re-run.
"""
import re
import sys
from pathlib import Path
from html import escape, unescape
from urllib.parse import quote

REPO = Path(__file__).resolve().parent.parent
BASE = "https://thesportspage.net"
DEFAULT_OG_IMAGE = f"{BASE}/assets/banner.png"

# ---------- helpers ----------
TAG_STRIP_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(html):
    if not html:
        return ""
    t = TAG_STRIP_RE.sub(" ", html)
    t = unescape(t)
    return WS_RE.sub(" ", t).strip()


def extract_hed(content):
    """Match either <h1 class="hed"> or <h2 class="hed">."""
    m = re.search(r'<h[12] class="hed"[^>]*>(.+?)</h[12]>', content, re.DOTALL)
    return clean_text(m.group(1)) if m else None


def extract_deck(content):
    m = re.search(r'<p class="deck">(.+?)</p>', content, re.DOTALL)
    return clean_text(m.group(1)) if m else None


def canonical_url(filename):
    return f"{BASE}/published/{filename}"


# ---------- share section markup ----------
def share_section_html(filename, hed, deck):
    canonical = canonical_url(filename)

    def tagged(source):
        sep = "&" if "?" in canonical else "?"
        return f"{canonical}{sep}utm_source={source}&utm_medium=share"

    url_x = tagged("x")
    url_fb = tagged("facebook")
    url_li = tagged("linkedin")
    url_email = tagged("email")
    url_copy = tagged("copylink")

    x_text = hed if len(hed) <= 200 else hed[:197].rsplit(" ", 1)[0] + "…"
    email_subject = f"From The Sports Page: {hed[:120]}"
    email_body = (
        f"Thought you'd enjoy this:\n\n{hed}\n\n{deck if deck else ''}\n\n"
        f"Read it here: {url_email}\n\n— passed along via The Sports Page"
    )

    enc = quote
    x_url = f"https://twitter.com/intent/tweet?text={enc(x_text + ' — The Sports Page')}&url={enc(url_x)}"
    fb_url = f"https://www.facebook.com/sharer/sharer.php?u={enc(url_fb)}"
    li_url = f"https://www.linkedin.com/sharing/share-offsite/?url={enc(url_li)}"
    mail_url = f"mailto:?subject={enc(email_subject)}&body={enc(email_body)}"

    return f"""<!-- SHARE SECTION -->
<section id="share" style="max-width:820px;margin:1.5rem auto 0;background:var(--ink);padding:2.2rem 3rem 2.5rem;box-shadow:0 6px 40px rgba(0,0,0,.3);text-align:center" data-canonical-url="{canonical}">

  <div style="font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:700;color:#c9962a;margin-bottom:.3rem">Pass it on.</div>
  <div style="font-family:'Libre Baskerville',serif;font-size:.92rem;color:#a09070;font-style:italic;margin-bottom:1.5rem">A few minutes to read. A few seconds to send.</div>

  <!-- SOCIAL SHARE BUTTONS -->
  <div style="display:flex;justify-content:center;flex-wrap:wrap;gap:.5rem;margin-bottom:2.2rem">

    <a href="{x_url}" target="_blank" rel="noopener" aria-label="Share on X"
       style="display:inline-flex;align-items:center;gap:.45rem;background:#c9962a;color:#1a1208;padding:.6rem 1rem;font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:1px solid #c9962a;transition:background .15s">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24h-6.66l-5.214-6.817-5.97 6.817H1.673l7.73-8.835L1.254 2.25h6.832l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      Share on X
    </a>

    <a href="{fb_url}" target="_blank" rel="noopener" aria-label="Share on Facebook"
       style="display:inline-flex;align-items:center;gap:.45rem;background:transparent;color:#c9962a;padding:.6rem 1rem;font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:1px solid #c9962a;transition:all .15s">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M22.675 0H1.325C.593 0 0 .593 0 1.325v21.351C0 23.408.593 24 1.325 24H12.82v-9.294H9.692v-3.622h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12V24h6.116c.73 0 1.323-.593 1.323-1.325V1.325C24 .593 23.408 0 22.675 0z"/></svg>
      Facebook
    </a>

    <a href="{li_url}" target="_blank" rel="noopener" aria-label="Share on LinkedIn"
       style="display:inline-flex;align-items:center;gap:.45rem;background:transparent;color:#c9962a;padding:.6rem 1rem;font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:1px solid #c9962a;transition:all .15s">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.063 2.063 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
      LinkedIn
    </a>

    <a href="{mail_url}" aria-label="Share by email"
       style="display:inline-flex;align-items:center;gap:.45rem;background:transparent;color:#c9962a;padding:.6rem 1rem;font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:1px solid #c9962a;transition:all .15s">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M0 4v16h24V4H0zm21.518 2L12 12.713 2.482 6h19.036zM2 18V7.183l10 7.05 10-7.05V18H2z"/></svg>
      Email
    </a>

    <button type="button" id="sp-copy-link" aria-label="Copy link" data-url="{url_copy}"
       style="display:inline-flex;align-items:center;gap:.45rem;background:transparent;color:#c9962a;padding:.6rem 1rem;font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;border:1px solid #c9962a;cursor:pointer;transition:all .15s">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
      <span id="sp-copy-label">Copy link</span>
    </button>

  </div>

  <!-- DIVIDER -->
  <div style="max-width:200px;margin:0 auto 1.5rem;border-top:1px solid rgba(201,150,42,0.25)"></div>

  <!-- QR CODE -- physical/in-person sharing -->
  <a href="{BASE}/" style="text-decoration:none"><img src="../assets/banner.png" alt="The Sports Page" style="max-width:300px;height:auto;margin:0 auto 1rem;display:block;opacity:.85"></a>
  <div style="font-family:'Libre Baskerville',serif;font-size:.78rem;color:#a09070;font-style:italic;margin-bottom:1rem">Or scan, for sharing the old-fashioned way.</div>
  <a href="{BASE}/" style="text-decoration:none"><img src="../assets/qr-code.png" alt="QR Code to thesportspage.net" style="width:160px;height:160px;display:block;margin:0 auto 1rem;border:5px solid #c9962a;padding:4px;background:#fff"></a>
  <div style="font-family:'Roboto Mono',monospace;font-size:.72rem;color:#c9962a;letter-spacing:.08em;margin-bottom:.3rem"><a href="{BASE}/" style="color:#c9962a;text-decoration:none;border-bottom:1px solid rgba(201,150,42,0.5)">thesportspage.net</a></div>
  <div style="font-family:'Roboto Mono',monospace;font-size:.6rem;color:#6b5e4a;letter-spacing:.1em;margin-top:1rem">© 2026 The Sports Page · A Statistical Dispatch for Friends & Family</div>

</section>

<!-- COPY-LINK INTERACTION -->
<script>
(function(){{
  var btn = document.getElementById('sp-copy-link');
  if (!btn) return;
  var label = document.getElementById('sp-copy-label');
  var url = btn.getAttribute('data-url');
  btn.addEventListener('click', function(){{
    try {{
      navigator.clipboard.writeText(url).then(function(){{
        label.textContent = 'Copied!';
        btn.style.background = '#c9962a';
        btn.style.color = '#1a1208';
        setTimeout(function(){{
          label.textContent = 'Copy link';
          btn.style.background = 'transparent';
          btn.style.color = '#c9962a';
        }}, 1800);
      }});
    }} catch (e) {{
      window.prompt('Copy this link:', url);
    }}
  }});
}})();
</script>"""


# ---------- Open Graph meta tags ----------
def og_tags(filename, hed, deck):
    url = canonical_url(filename)
    description = deck if deck else "A daily statistics newsletter — one strange number, explained."
    if len(description) > 200:
        description = description[:197].rsplit(" ", 1)[0] + "…"
    title = hed if hed else "The Sports Page"
    return f"""<!-- Open Graph + Twitter Card for social previews -->
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The Sports Page">
<meta property="og:image" content="{DEFAULT_OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{DEFAULT_OG_IMAGE}">"""


# ---------- main file processor ----------
SHARE_BLOCK_RE = re.compile(
    r'<!-- SHARE SECTION -->\s*<(?:div|section) id="share".*?</(?:div|section)>'
    r'\s*(?:<!--[^>]*COPY-LINK[^>]*-->\s*<script>.*?</script>)?',
    re.DOTALL,
)
OG_BLOCK_RE = re.compile(
    r'<!-- Open Graph[^>]*-->\s*(?:<meta property="og:[^"]+" content="[^"]*">\s*|<meta name="twitter:[^"]+" content="[^"]*">\s*)+',
    re.DOTALL,
)
HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)


def inject_into(filepath):
    """Insert/refresh share section + OG meta tags in a single HTML file.

    Returns a (changed, msg) tuple. Idempotent: re-running on an already-processed
    file replaces the existing share section with the current canonical version.
    """
    f = Path(filepath)
    text = f.read_text()
    hed = extract_hed(text)
    deck = extract_deck(text)
    if not hed:
        return False, "no headline found"
    orig = text

    # Refresh OG meta tags (remove existing, then insert)
    text = OG_BLOCK_RE.sub("", text)
    og = og_tags(f.name, hed, deck)
    text = HEAD_CLOSE_RE.sub(og + "\n</head>", text, count=1)

    # Refresh share section
    new_share = share_section_html(f.name, hed, deck)
    if SHARE_BLOCK_RE.search(text):
        text = SHARE_BLOCK_RE.sub(new_share, text, count=1)
    else:
        text = re.sub(r"</body>", new_share + "\n</body>", text, count=1, flags=re.IGNORECASE)

    if text != orig:
        f.write_text(text)
        return True, "ok"
    return False, "no change"


# ---------- script mode ----------
def main():
    targets = list((REPO / "queue").glob("*.html")) + list((REPO / "published").glob("*.html"))
    ok = 0
    skipped = []
    for f in sorted(targets):
        changed, msg = inject_into(f)
        if changed:
            ok += 1
        elif msg != "no change":
            skipped.append((f.name, msg))
    print(f"✓ {ok} files updated")
    if skipped:
        print(f"⚠ {len(skipped)} skipped (no headline):")
        for name, msg in skipped[:5]:
            print(f"    {name}")


if __name__ == "__main__":
    main()
