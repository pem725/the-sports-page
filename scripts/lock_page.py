#!/usr/bin/env python3
"""Lock a generated page behind the board passphrase.

    lock(html, title) -> a page that holds `html` ENCRYPTED and asks for the
                         passphrase before showing it.

Why this exists. The editor, 2026-10-15: Sean could not find the board's page,
so "get a URL so it's easy for the gents... But you got to protect it also."
GitHub Pages cannot authenticate anybody, and an unguessable path is only
unlisted -- anyone holding the link can read it. Encryption is the protection a
static host CAN offer: the page served to the world is ciphertext, and only the
passphrase turns it back into the board.

How. `openssl enc -aes-256-cbc -pbkdf2 -md sha256` does the encrypting (present
on this machine and on every GitHub runner, so no new dependency), and the
browser's built-in WebCrypto does the decrypting with the same PBKDF2-SHA256 key
derivation. The passphrase is handed to openssl as `-pass env:BOARD_PASSPHRASE`,
so it never appears in a command line, a process list or a log.

Honest limits, stated here because they will be assumed away otherwise:
  * It is ONE shared passphrase. Revoking a single editor means changing it and
    telling the other three. Per-person logins need Cloudflare Access
    (tracking/cloudflare-access-runbook.md), which is still the better end state.
  * The REPOSITORY IS PUBLIC. The running order is derived from QUEUE_ORDER.txt
    and the queue files, which anyone can read on GitHub. This protects the
    convenient view of the board, not the underlying facts.
  * Earlier plaintext versions of the page remain in git history.
"""
import base64
import html as H
import os
import secrets
import subprocess

ENV = "BOARD_PASSPHRASE"
ITER = 250_000
# Prepended before encrypting. CBC has no built-in integrity check, so a wrong
# passphrase usually -- but not always -- fails on padding; this marker makes
# "wrong passphrase" certain instead of probable.
MARK = "<!--TSP-BOARD-OK-->"


def have_passphrase():
    return bool(os.environ.get(ENV))


def _encrypt(plain):
    out = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", str(ITER), "-md", "sha256",
         "-salt", "-pass", f"env:{ENV}"],
        input=(MARK + plain).encode("utf-8"), capture_output=True, check=True,
    ).stdout
    if not out.startswith(b"Salted__"):
        raise RuntimeError("openssl did not produce a salted payload")
    return base64.b64encode(out).decode("ascii")


def _decrypt_check(b64):
    """Round-trip through openssl so a page that cannot be opened is never written."""
    raw = base64.b64decode(b64)
    plain = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", str(ITER), "-md", "sha256",
         "-pass", f"env:{ENV}"],
        input=raw, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return plain.startswith(MARK)


def lock(plain_html, title="The Sports Page"):
    if not have_passphrase():
        raise SystemExit(f"{ENV} is not set -- refusing to write an unprotected board")
    blob = _encrypt(plain_html)
    if not _decrypt_check(blob):
        raise SystemExit("locked page failed its own round-trip -- not writing it")
    t = H.escape(title)
    return LOCK_PAGE.replace("{{TITLE}}", t).replace("{{BLOB}}", blob) \
                    .replace("{{ITER}}", str(ITER)).replace("{{MARK}}", MARK) \
                    .replace("{{NONCE}}", secrets.token_hex(4))


def not_ready_page(title="The Sports Page"):
    """Served at the board address until a passphrase has been set."""
    return NOT_READY.replace("{{TITLE}}", H.escape(title))


_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>{{TITLE}}</title>
<style>
:root{--ink:#1a1208;--paper:#f5f0e8;--ground:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--muted:#6b5e4a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#ece2cf;--paper:#1d1810;--ground:#120e08;--rust:#e07050;--steel:#7fa8d4;--muted:#9c8d75}}
:root[data-theme="dark"]{--ink:#ece2cf;--paper:#1d1810;--ground:#120e08;--rust:#e07050;--steel:#7fa8d4;--muted:#9c8d75}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:var(--ground);color:var(--ink);font-family:Georgia,'Times New Roman',serif;padding:1rem}
.gate{background:var(--paper);max-width:380px;width:100%;padding:2rem 1.6rem 1.6rem;text-align:center;
  border-top:4px solid var(--ink);box-shadow:0 6px 40px rgba(26,18,8,.18)}
.gate img{width:72px;height:72px;display:block;margin:0 auto .6rem}
.eyebrow{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.64rem;letter-spacing:.22em;
  text-transform:uppercase;color:var(--muted)}
h1{font-size:1.7rem;margin:.2rem 0 1.1rem;letter-spacing:.03em;text-transform:uppercase}
input[type=password]{width:100%;font:inherit;font-size:1rem;padding:.6rem .75rem;border:1px solid var(--muted);
  background:#fff;color:#1a1208}
label.rem{display:flex;gap:.4rem;align-items:center;justify-content:center;margin:.7rem 0 0;
  font-size:.8rem;color:var(--muted)}
button{margin-top:.9rem;width:100%;background:var(--rust);color:#fff;border:none;padding:.65rem;
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.75rem;letter-spacing:.16em;
  text-transform:uppercase;cursor:pointer}
.err{color:var(--rust);font-size:.85rem;min-height:1.2em;margin:.6rem 0 0}
.note{font-size:.78rem;color:var(--muted);margin:1rem 0 0;line-height:1.5}
</style>
</head>
"""

LOCK_PAGE = _HEAD + """<body>
<form class="gate" id="gate" autocomplete="on">
  <img src="https://thesportspage.net/assets/logo-badge.png" alt="" width="72" height="72">
  <div class="eyebrow">For the Editorial Board</div>
  <h1>The Board</h1>
  <input type="text" name="username" value="board" autocomplete="username" hidden>
  <input type="password" id="pw" autocomplete="current-password" placeholder="Board passphrase" aria-label="Board passphrase" required>
  <label class="rem"><input type="checkbox" id="rem" checked> Remember on this device</label>
  <button type="submit">Open the board</button>
  <p class="err" id="err" role="alert"></p>
  <p class="note">Ask Patrick for the passphrase. This page is encrypted; without it, there is nothing here to read.</p>
</form>
<script id="blob" type="application/octet-stream">{{BLOB}}</script>
<script>
(function () {
  var KEY = 'tsp-board-pass', ITER = {{ITER}}, MARK = '{{MARK}}';
  var form = document.getElementById('gate'), pw = document.getElementById('pw'),
      rem = document.getElementById('rem'), err = document.getElementById('err');

  async function open(pass) {
    var raw = Uint8Array.from(atob(document.getElementById('blob').textContent.trim()), function (c) { return c.charCodeAt(0); });
    var salt = raw.slice(8, 16), data = raw.slice(16);           // "Salted__" + 8-byte salt
    var base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveBits']);
    var bits = new Uint8Array(await crypto.subtle.deriveBits(
      { name: 'PBKDF2', salt: salt, iterations: ITER, hash: 'SHA-256' }, base, 384));
    var key = await crypto.subtle.importKey('raw', bits.slice(0, 32), 'AES-CBC', false, ['decrypt']);
    var plain = new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-CBC', iv: bits.slice(32, 48) }, key, data));
    if (plain.indexOf(MARK) !== 0) throw new Error('wrong passphrase');
    return plain.slice(MARK.length);
  }
  function show(page) { document.open(); document.write(page); document.close(); }
  function store(v) { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} }

  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved) open(saved).then(show, function () { store(null); });   /* passphrase changed: ask again */

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    err.textContent = 'Opening…';
    var p = pw.value;
    open(p).then(function (page) { store(rem.checked ? p : null); show(page); },
                 function () { err.textContent = 'That is not the passphrase.'; pw.select(); });
  });
})();
</script>
</body>
</html>
<!-- build {{NONCE}} -->
"""

NOT_READY = _HEAD + """<body>
<div class="gate">
  <img src="https://thesportspage.net/assets/logo-badge.png" alt="" width="72" height="72">
  <div class="eyebrow">For the Editorial Board</div>
  <h1>The Board</h1>
  <p class="note" style="font-size:.95rem">The board is being locked. It will open here, behind a passphrase, shortly.</p>
</div>
</body>
</html>
"""
