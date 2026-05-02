#!/usr/bin/env python3
"""
One-shot migration: replace the GitHub-button pitch box (outside .paper)
with the original Formspree form (inside .paper, before .footer).

The "ugly" version was added in a recent commit; this script removes it
and inserts the canonical Formspree form, matching the design used on
issues #1 through #19 of The Sports Page.

Idempotent — safe to re-run. Files already using the Formspree form
are left alone.
"""

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORMSPREE_BOX = '''  <!-- STORY IDEAS INBOX -->
  <div id="pitch" style="border:2px solid var(--gold);background:var(--card);padding:1.5rem 1.8rem;margin:1.8rem 0">
    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--gold);margin-bottom:.3rem">Pitch a Story</h3>
    <p style="font-size:.88rem;color:var(--muted);margin-bottom:1rem">Noticed a weird stat? Saw something that doesn&rsquo;t add up? Send it in. The best ideas become issues.</p>
    <form id="pitch-form" action="https://formspree.io/f/xykbazvr" method="POST" style="display:flex;flex-direction:column;gap:.6rem">
      <input type="hidden" name="_subject" value="New Story Pitch &mdash; The Sports Page">
      <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off">
      <input type="text" name="name" id="pitch-name" placeholder="Your name" required style="font-family:'Libre Baskerville',serif;font-size:.9rem;padding:.5rem .7rem;border:1px solid var(--div);background:var(--cream);color:var(--ink);outline:none">
      <input type="text" name="sport" id="pitch-sport" placeholder="Sport (MLB, NFL, NHL, CFB, WNBA, etc.)" style="font-family:'Libre Baskerville',serif;font-size:.9rem;padding:.5rem .7rem;border:1px solid var(--div);background:var(--cream);color:var(--ink);outline:none">
      <textarea name="idea" placeholder="What&rsquo;s the stat or story? Why is it weird, interesting, or important?" required rows="3" style="font-family:'Libre Baskerville',serif;font-size:.9rem;padding:.5rem .7rem;border:1px solid var(--div);background:var(--cream);color:var(--ink);outline:none;resize:vertical"></textarea>
      <div style="display:flex;gap:.8rem;align-items:center">
        <button id="pitch-btn" type="submit" style="background:var(--gold);color:var(--ink);font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;border:none;padding:.6rem 1.4rem;cursor:pointer">Submit Idea</button>
        <span style="font-family:'Roboto Mono',monospace;font-size:.6rem;color:var(--muted)">or <a href="https://github.com/pem725/the-sports-page/issues/new?title=Story+Idea:&labels=story-idea&body=Sport:%0A%0AStat+or+story:%0A%0AWhy+it%27s+interesting:" style="color:var(--steel)">post on GitHub</a></span>
      </div>
    </form>
    <div id="pitch-ok" style="display:none;padding:.8rem 0;font-family:'Roboto Mono',monospace;font-size:.78rem;color:var(--green);font-weight:600;letter-spacing:.08em">Sent! We read every pitch. The weird ones become issues.</div>
    <div id="pitch-err" style="display:none;padding:.8rem 0;font-family:'Roboto Mono',monospace;font-size:.78rem;color:var(--rust);font-weight:600;letter-spacing:.08em">Something went wrong. Try the GitHub link instead.</div>
  </div>
  <script>
  document.getElementById('pitch-form').addEventListener('submit',async function(e){
    e.preventDefault();
    var btn=document.getElementById('pitch-btn'),ok=document.getElementById('pitch-ok'),err=document.getElementById('pitch-err');
    btn.disabled=true;btn.textContent='SENDING\\u2026';ok.style.display='none';err.style.display='none';
    try{
      var r=await fetch(this.action,{method:'POST',body:new FormData(this),headers:{'Accept':'application/json'}});
      if(r.ok){ok.style.display='block';this.reset();}
      else{err.style.display='block';}
    }catch(x){err.style.display='block';}
    btn.disabled=false;btn.textContent='SUBMIT IDEA';
  });
  </script>

'''

# Pattern that matches the "ugly" pitch box I just added (outside .paper)
UGLY_BOX_PATTERN = re.compile(
    r'<!-- PITCH BOX -->\s*\n<div id="pitch"[^>]*?>.*?</div>\s*\n',
    re.DOTALL,
)


def is_formspree_already(content: str) -> bool:
    """Detect a Formspree-style pitch box (with form action to formspree.io)."""
    return 'formspree.io' in content


def has_ugly_box(content: str) -> bool:
    """Detect the recently-added GitHub-button pitch box."""
    return bool(UGLY_BOX_PATTERN.search(content))


def remove_ugly_box(content: str) -> str:
    return UGLY_BOX_PATTERN.sub('', content)


def insert_formspree_box(content: str) -> str:
    """Insert the Formspree pitch box just before <div class="footer">."""
    if 'formspree.io' in content:
        return content
    if '<div class="footer">' not in content:
        return content
    return content.replace(
        '<div class="footer">',
        FORMSPREE_BOX + '<div class="footer">',
        1,
    )


def migrate_file(path: str, dry_run: bool = False) -> str:
    with open(path, encoding='utf-8') as f:
        content = f.read()
    actions = []

    # Phase 1: remove the ugly box if present
    if has_ugly_box(content):
        content = remove_ugly_box(content)
        actions.append('removed-ugly')

    # Phase 2: insert Formspree box if not already present
    if not is_formspree_already(content):
        new_content = insert_formspree_box(content)
        if new_content != content:
            content = new_content
            actions.append('inserted-formspree')

    if not actions:
        return 'unchanged'
    if not dry_run:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    return ' + '.join(actions)


def main():
    dry_run = '--dry-run' in sys.argv
    targets = []
    for d in ('queue', 'published'):
        full = os.path.join(REPO, d)
        if not os.path.isdir(full):
            continue
        for fn in sorted(os.listdir(full)):
            if not fn.endswith('.html'):
                continue
            if fn.endswith('-deeper.html') or fn.startswith('sunday-'):
                continue
            targets.append(os.path.join(full, fn))

    summary = {'unchanged': 0, 'migrated': 0}
    for path in targets:
        result = migrate_file(path, dry_run=dry_run)
        rel = os.path.relpath(path, REPO)
        if result == 'unchanged':
            summary['unchanged'] += 1
        else:
            print(f"  {result:35s}  {rel}")
            summary['migrated'] += 1
    print(f"\nSummary: {summary['migrated']} migrated, "
          f"{summary['unchanged']} unchanged "
          f"({'dry-run' if dry_run else 'live'})")


if __name__ == '__main__':
    main()
