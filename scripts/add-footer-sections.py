#!/usr/bin/env python3
"""
add-footer-sections.py — Add Pitch a Story form and Share/QR section
to all published pages and the Sunday template.

Run once. Idempotent (skips files that already have the pitch form).
"""

import os
import re
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files in published/ use ../assets/, files at root use assets/
PITCH_FORM = '''
  <!-- STORY IDEAS INBOX -->
  <div id="pitch" style="border:2px solid var(--gold);background:var(--card);padding:1.5rem 1.8rem;margin:1.8rem 0">
    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--gold);margin-bottom:.3rem">Pitch a Story</h3>
    <p style="font-size:.88rem;color:var(--muted);margin-bottom:1rem">Noticed a weird stat? Saw something that doesn&rsquo;t add up? Send it in. The best ideas become issues.</p>
    <form id="pitch-form" action="https://formspree.io/f/xykbazvr" method="POST" style="display:flex;flex-direction:column;gap:.6rem">
      <input type="hidden" name="_subject" value="New Story Pitch &mdash; The Sports Page">
      <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off">
      <input type="text" name="name" placeholder="Your name" required style="font-family:'Libre Baskerville',serif;font-size:.9rem;padding:.5rem .7rem;border:1px solid var(--div);background:var(--cream);color:var(--ink);outline:none">
      <input type="text" name="sport" placeholder="Sport (MLB, NFL, NHL, CFB, WNBA, etc.)" style="font-family:'Libre Baskerville',serif;font-size:.9rem;padding:.5rem .7rem;border:1px solid var(--div);background:var(--cream);color:var(--ink);outline:none">
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

def share_section(asset_prefix):
    return f'''
<!-- SHARE SECTION -->
<div id="share" style="max-width:820px;margin:1.5rem auto 0;background:var(--ink);padding:2.5rem 3rem;box-shadow:0 6px 40px rgba(0,0,0,.3);text-align:center">
  <img src="{asset_prefix}assets/banner.png" alt="The Sports Page" style="max-width:360px;height:auto;margin:0 auto 1.2rem;display:block;opacity:.9">
  <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#c9962a;margin-bottom:.4rem">Share The Sports Page</div>
  <div style="font-family:'Libre Baskerville',serif;font-size:.88rem;color:#a09070;font-style:italic;margin-bottom:1.4rem">Scan the code or share the link. Free, always.</div>
  <img src="{asset_prefix}assets/qr-code.png" alt="QR Code" style="width:180px;height:180px;display:block;margin:0 auto 1rem;border:6px solid #c9962a;padding:4px;background:#fff">
  <div style="font-family:'Roboto Mono',monospace;font-size:.75rem;color:#c9962a;letter-spacing:.08em;margin-bottom:.3rem">pem725.github.io/the-sports-page</div>
  <div style="font-family:'Roboto Mono',monospace;font-size:.6rem;color:#6b5e4a;letter-spacing:.1em;margin-top:1rem">&copy; 2026 The Sports Page &middot; A Statistical Dispatch for Friends &amp; Family</div>
</div>
'''


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has pitch form
    if 'id="pitch"' in content:
        print(f"  SKIP (already has pitch form): {os.path.basename(filepath)}")
        return False

    # Determine asset prefix based on file location
    if '/published/' in filepath:
        asset_prefix = '../'
    elif '/reserve/' in filepath:
        asset_prefix = '../'
    else:
        asset_prefix = ''

    modified = False

    # 1. Insert Pitch form before the footer (inside .paper)
    # Find the footer div inside the paper
    footer_match = re.search(r'(\n  <!-- FOOTER -->\n  <div class="footer">)', content)
    if not footer_match:
        # Try alternate pattern without comment
        footer_match = re.search(r'(\n  <div class="footer">)', content)

    if footer_match:
        insert_pos = footer_match.start()
        content = content[:insert_pos] + PITCH_FORM + content[insert_pos:]
        modified = True
    else:
        print(f"  WARN: No footer found in {os.path.basename(filepath)}")

    # 2. Insert Share/QR section before </body>
    if '</body>' in content and 'id="share"' not in content:
        content = content.replace('</body>', share_section(asset_prefix) + '\n</body>')
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  UPDATED: {os.path.basename(filepath)}")
        return True

    return False


def main():
    print("Adding Pitch a Story form and Share/QR section to all pages...")
    print()

    # Published pages
    published = sorted(glob.glob(os.path.join(REPO, 'published', '*.html')))
    # Sunday template
    template = os.path.join(REPO, 'reserve', 'sunday-recap-template.html')
    # Queue files
    queue = sorted(glob.glob(os.path.join(REPO, 'queue', '*.html')))

    all_files = published + [template] + queue
    updated = 0

    for f in all_files:
        if process_file(f):
            updated += 1

    print()
    print(f"Done. Updated {updated} files.")


if __name__ == '__main__':
    main()
