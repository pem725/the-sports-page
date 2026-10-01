# Putting the board's budget sheet behind real authentication

Decided 2026-10-01. The budget sheet at `/board/k7q2-desk-9f4m/` is currently
**unlisted, not private** — GitHub Pages serves static files and cannot
authenticate anybody. Cloudflare Access puts a real login in front of it, free
for up to 50 users, and costs each editor one emailed six-digit code.

Four readers, all of them family or close to it: Sean (brother), Tim, Patrick jr
(son), Patrick. **Their email addresses are entered at Cloudflare and are not
recorded in this repo**, same rule as reader questions.

---

## The part a human has to do, and why

Claude cannot create accounts or authenticate to a dashboard, so steps marked
**[you]** are yours. Everything else is already done or is checkable from here.

---

## PRE-FLIGHT: the zone as it stands

**The rollback reference is `tracking/dns-snapshot.md`,** generated from the
Porkbun API at full length. Regenerate it before starting:

```bash
source ~/.config/secrets/tokens.env
python3 scripts/porkbun.py --snapshot thesportspage.net
```

13 records. The shape, in summary — but **migrate from the snapshot file, not
from this summary**:

```
ALIAS   @        pem725.github.io          <- NOT four A records
CNAME   www      pem725.github.io
MX      @        10 fwd1.porkbun.com
MX      @        20 fwd2.porkbun.com
NS      @        x4 porkbun
TXT     @                      SPF
TXT     _dmarc                 DMARC, p=quarantine
TXT     default._domainkey     DKIM public key, 234 chars
TXT     _acme-challenge        x2, certificate validation
```

### Two things the first draft of this runbook got wrong

**`dig` cannot see half this zone.** A TXT query at the apex returns SPF and
nothing else, because `_dmarc`, `default._domainkey` and `_acme-challenge` are
separate names. An inventory built from public DNS silently omits them, and this
document was briefly written from exactly that incomplete picture.

**The list view truncates at 60 characters.** The DKIM key is **234**. A rollback
reference containing the first 60 characters of a DKIM key is worse than having
none, because it looks finished. `--snapshot` exists for this reason.

### Why that combination is dangerous

DMARC is set to **`p=quarantine`**. If DKIM does not survive the move, mail from
the domain fails DKIM, DMARC quarantines it, and messages go to spam rather than
bouncing. **Nothing errors.** Mail just quietly stops landing in inboxes.

---

## THE TRAP, stated first because it is the expensive one

**Moving the zone to Cloudflare moves ALL of it.** The free plan requires full
nameserver delegation; you cannot hand over one subdomain and keep the rest.

That means the **MX and SPF records above must be recreated at Cloudflare or
`ideas@thesportspage.net` stops receiving mail.** That address is:

- the reader-question front door, promised in public on `ask.html`
- in **23 `mailto:` links** across the published archive
- **embedded in `feed.xml` article bodies**, which Buttondown mails to the list

It would fail *silently*. Nothing errors; mail simply stops arriving, and we
would not notice until somebody mentioned they wrote in and heard nothing. That
is the same shape as every other failure in this paper's log: it degrades to
something that looks fine.

Porkbun's email **forwarding configuration stays at Porkbun** — it is
dashboard-only and not in the v3 API — but the MX records that *route* to it
must be replicated in Cloudflare's DNS.

**Verify mail still works after the switch before considering this done.**

---

## Steps

### 1. [you] Create the Cloudflare account and add the site
cloudflare.com → Sign Up → **Add a site** → `thesportspage.net` → **Free** plan.

Cloudflare scans the existing zone and imports what it finds. **Do not trust the
import.** Compare what it shows against the pre-flight block above, record by
record, and add anything missing. The MX and TXT lines are the ones that get
dropped.

### 2. [you] Set SSL mode to Full before changing nameservers
SSL/TLS → Overview → **Full** (or Full (strict)).

GitHub Pages forces HTTPS. Cloudflare's default **Flexible** mode talks to the
origin over HTTP, so Pages redirects to HTTPS, which Cloudflare answers over
HTTP again — an infinite redirect loop that takes the whole site down. This is
the single most common way this migration breaks.

### 3. [you] Point the apex and www through the proxy
The apex is an **ALIAS** at Porkbun, which is Porkbun's name for a CNAME at the
root. Cloudflare does the same thing and calls it CNAME flattening, so recreate
it as:

```
CNAME   @     pem725.github.io     Proxied
CNAME   www   pem725.github.io     Proxied
```

**Prefer this over hand-entering GitHub's four A records.** Both work, but the
CNAME follows GitHub if they ever renumber their Pages fleet; pinned A records
silently rot the day that happens.

Access only works on proxied traffic, so both of these must be orange-clouded.
MX records are never proxied — leave them grey/DNS-only. That is correct, not an
error.

### 4. [you] Change the nameservers at Porkbun
Porkbun → thesportspage.net → Authoritative Nameservers → replace the four
`*.ns.porkbun.com` entries with the two Cloudflare gives you.

Propagation is usually minutes, occasionally a few hours. The site stays up
throughout **if** step 1 was done honestly.

### 5. [you] Create the Access application
Zero Trust → Access → Applications → **Add an application** → *Self-hosted*.

```
Application name    The Budget
Session duration    1 month        <- so nobody re-authenticates weekly
Domain              thesportspage.net
Path                board
```

Policy:

```
Policy name   Editorial board
Action        Allow
Include       Emails  ->  the four board addresses
```

Leave the identity provider as **One-time PIN**. No accounts to create: an
editor enters their email, Cloudflare mails a code, they are in for a month.

**Scope the path to `board` and nothing else.** An application left at the apex
puts the entire newspaper behind a login, which is the opposite of the point —
this paper gives its statistics away.

### 6. Consider adding newsroom.html
`/newsroom.html` carries the ranked candidate pile and the held stories. It is
now disallowed in `robots.txt` but is still linked from the homepage and
readable by anyone. Either add it to the same Access application as a second
path, or accept that it is public. A decision either way, not an oversight.

---

## Verify — do not skip this

```bash
# 1. the board asks for a login (expect 302 to cloudflareaccess.com)
curl -sI https://thesportspage.net/board/k7q2-desk-9f4m/ | head -3

# 2. the PAPER does not (expect 200, no redirect to a login)
curl -sI https://thesportspage.net/ | head -3
curl -sI https://thesportspage.net/odds.html | head -3

# 3. mail still routes  <- the one that fails silently
dig +short MX thesportspage.net
dig +short TXT thesportspage.net
dig +short TXT _dmarc.thesportspage.net
dig +short TXT default._domainkey.thesportspage.net   # <- the 234-char one
#    all four must answer. The last two are the ones a dig-based
#    inventory misses, which is how they get left behind.

# 4. and actually send one from outside
#    email ideas@thesportspage.net and confirm it arrives
```

Compare every answer against `tracking/dns-snapshot.md`, in full. A DKIM record
that exists but is truncated passes a presence check and still fails validation.

Step 3 passing is not sufficient. **Send the real email**, from an outside
account, and confirm it arrives in the inbox and not in spam. DNS can be right
while forwarding is broken, and with `p=quarantine` a DKIM mistake shows up as
"it went to junk," not as an error.

---

## If it goes wrong

Set the nameservers at Porkbun back to the four `*.ns.porkbun.com` entries in the
pre-flight block. Porkbun's own DNS records are still there and untouched;
reverting the delegation restores the previous state within the hour.

---

## What this does and does not buy

**Does:** a real login on the budget sheet. No shared password, no link that
works forever once forwarded, and you can revoke one person without moving
anything.

**Does not:** protect the repository. The budget page is generated from
`QUEUE_ORDER.txt` and the queue files, and **the repo is public** — anyone who
wants the running order can read it there. Access protects the convenient view,
not the underlying facts. If the queue itself needs to be private, that is a
different and much larger decision about the repo.
