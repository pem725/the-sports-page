---
name: sports-stat-storyteller
description: >
  Turn a single strange, extreme, or counterintuitive sports statistic into a
  publication-ready newsletter. Use this skill any time a user notices an odd
  number in any sport — a pitcher's 67.5 ERA, a batter's .667 average through 5
  AB, a QB's perfect passer rating — and wants to understand WHAT it means, WHY
  it happened mathematically, WHO else has been here before, and HOW LONG
  recovery will take. Drives an end-to-end workflow: statistical diagnosis,
  historical search, Bayesian modeling, schedule-mapped projections, broadsheet
  HTML newsletter. Also handles daily publishing from queue to GitHub Pages,
  Sunday Edition recaps with fresh data and model reruns, and cross-reference
  checks. Trigger on "strange stat", "crazy number", "what does this mean",
  "publish the next issue", or any stat with a small denominator.
---

# Sports Stat Storyteller Skill

## Purpose

Convert a single anomalous sports statistic into an educational newsletter
that helps fans understand the mathematical structure behind what they're
seeing — without requiring statistics knowledge. The canonical workflow is
the Paul Skenes Opening Day 2026 story: 5 ER, ⅔ IP, 67.5 ERA → newsletter
explaining denominator leverage, historical parallels, Bayesian recovery, and
schedule-mapped projections.

---

## Tone Selection (REQUIRED before writing each issue)

Before writing any issue, present the user with tone options and ask which
voice fits this story. Suggest 2-3 that seem like the best match. The
newsletter should feel like it has multiple sports writers, not one voice.

| Voice | Style | Best For |
|-------|-------|----------|
| **The Columnist** | Dry wit, editorial authority, measured confidence | Analysis, historical comparisons, EO series |
| **The Heckler** | Irreverent, sarcastic, bar-stool energy, trash talk | Jets misery, bad trades, front office disasters |
| **The Professor** | Patient, empathetic, explains the math gently | Bayesian explainers, Sunday recaps, teaching moments |
| **The Eulogist** | Respectful, melancholic, beautiful prose about loss | Player injuries, franchise collapses, end-of-era |
| **The Fan** | Emotional, raw, honest, first-person energy | Drought pieces, playoff heartbreak, loyalty |

Example prompt to user: "This piece on the Jets' draft history could work as
**The Heckler** (sarcastic roast) or **The Eulogist** (mourning what could
have been). Which voice do you want?"

For the automated publisher (scheduled trigger), default to **The Columnist**
unless the content obviously calls for another voice (e.g., injury = Eulogist,
Jets = Heckler).

---

## Workflow (run in order)

### Step 0 — Stat Intake & Diagnosis

When a user presents a stat or event, immediately diagnose:

1. **What type of stat is it?** Rate (ERA, BA, FG%) vs count (HR, SO) vs
   composite (passer rating, WAR)
2. **What is the denominator?** This is the key question. Small denominators
   weaponize numerators.
3. **Direction of extremity**: Unexpectedly high? Low? Impossible to sustain
   in either direction?
4. **Baseline**: What is typical for this player, this position, this era?

```
Denominator Leverage Formula:
  rate_stat = numerator / denominator × scale
  sensitivity = d(rate_stat)/d(numerator) = scale / denominator

The smaller the denominator, the more sensitive the rate stat is to any
single event. A pitcher who gives up 5 ER in 2/3 IP has a denominator of
0.67 — enormously sensitive.
```

Print the diagnosis inline before proceeding.

### Step 1 — Historical Search

Use `web_search` to find:
- Elite performers who had similar anomalous short outings
- Recovery stories: did they bounce back? How fast?
- Any all-time records this event touches (shortest Cy Young start, worst
  Opening Day ERA, etc.)
- ERA- or performance-adjusted comparisons across eras

**Search queries to run (adapt for sport):**
```
"{player name} {event} reaction historical"
"elite {position} terrible short outing career {sport} history"
"{player name} compared to {comparable legend}"
"worst {stat} Opening Day history MLB"
```

Surface 2–4 historical parallels that illuminate the current event.

### Step 2 — Bayesian Recovery Model (Python)

For ERA-based recovery (adapt formula for other stats):

```python
import numpy as np

# Career state before bad event
prior_ip  = <career_IP>
prior_er  = <career_ER>
target    = <target_ERA>   # career ERA before disaster

# Post-disaster
cur_ip = prior_ip + bad_ip
cur_er = prior_er + bad_er

# Gamma-Poisson conjugate
# ER/inning ~ Poisson(λ),  λ ~ Gamma(α, rate=β)
alpha = 0.1 + prior_er
beta  = 0.1 + prior_ip   # rate parameterization

N_SIM  = 200_000
ip_mu  = <avg_IP_per_start>   # e.g. 6.5 for SP
ip_sig = 1.2

starts_needed = np.full(N_SIM, 162, dtype=int)
for i in range(N_SIM):
    lam = np.random.gamma(shape=alpha, scale=1.0/beta)
    er, ip = cur_er+0.0, cur_ip+0.0
    for s in range(1, 163):
        ip_s = float(np.clip(np.random.normal(ip_mu, ip_sig), 1.0, 9.0))
        er_s = int(np.random.poisson(lam * ip_s))
        er += er_s;  ip += ip_s
        if er * 9.0 / ip <= target:
            starts_needed[i] = s;  break

rec = starts_needed[starts_needed < 162]
print(f"P(recover this season): {len(rec)/N_SIM:.1%}")
for p in [10,25,50,75,90]:
    print(f"  {p}th pct: {int(np.percentile(rec,p))} starts")
```

**Key insight to always explain**: Recovery requires pitching *better than*
the target ERA, not just equal to it. Average future performance locks the
ERA above target forever if the damage is large enough.

### Step 3 — Schedule Mapping

Look up the team's schedule (use `web_search` → ESPN or CBS Sports schedule
pages) and project starts:
- Identify player's rotation slot (every 4th or 5th game)
- Map percentile starts to calendar dates and opponents
- Flag any notable matchups (division rivals, nationally televised)

### Step 4 — Newsletter Generation

Build an HTML artifact in broadsheet newspaper style (see Design System
below). Required sections:

1. **Masthead** — publication name, vol/issue, date, tagline
2. **Headline** — bold, punchy, includes the extreme number
3. **Deck** (subheadline) — one sentence capturing the counterintuitive insight
4. **Stat card row** — 3 key numbers: the extreme stat, current real number,
   target/prior number
5. **Two-column body** — narrative lead + "what it actually means"
6. **The Math** explainer box (dark background, monospace formula block)
7. **Recovery chart** (SVG, inline) — ERA/stat trajectory by percentile
8. **Recovery table** — percentile → starts needed → date → opponent
9. **Historical parallels** — 2–4 stories from search results
10. **Pull quote** — the key statistical insight in Playfair Display italic
11. **"Ask the Stats Desk" AI tool** — Claude API-powered textarea at bottom
    that contextualizes any stat the reader pastes in

### Step 5 — Skill Output

Produce two files:
- `[topic]_newsletter.html` — the artifact (present to user)
- This SKILL.md is the reusable template

---

## Design System

Aesthetic direction: **editorial broadsheet** — aged newsprint, ink, serif
type. NOT a tech blog. NOT a sports app.

```css
/* Core palette */
--ink:    #1a1208;   /* near-black, slightly warm */
--cream:  #f5f0e8;   /* paper background */
--aged:   #e8e0cf;   /* outer background */
--rust:   #b83a1e;   /* accent / bad stats */
--steel:  #2c4a6e;   /* accent / good stats / explainer BG */
--gold:   #c9962a;   /* AI tool accent */
--muted:  #6b5e4a;   /* secondary text */

/* Typography */
/* Display: Playfair Display — headlines, pull quotes */
/* Body: Libre Baskerville — editorial copy */
/* Data/labels: Roboto Mono — stats, datelines, captions */

/* Load from Google Fonts: */
/* Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700 */
/* Libre+Baskerville:ital,wght@0,400;0,700;1,400 */
/* Roboto+Mono:wght@400;600 */
```

**Component patterns:**
- Masthead: centered, triple-bordered, vol/issue/date line
- Stat cards: 3-column grid, `val` class for big number, `lbl` for mono label
- Pull quote: double-ruled top/bottom, Playfair italic centered
- Explainer box: `background: var(--steel)`, white text, `.math` code block
- Recovery chart: SVG, hand-drawn, labeled percentile curves
- AI Tool: `background: var(--ink)`, gold accents, Anthropic API call

**Recovery chart SVG guide:**
- viewBox="0 0 680 260"
- Y-axis: ERA (0–4), scale = 52.5px per ERA unit, y = 220 - ERA*52.5
- X-axis: starts (0–22+), scale = ~27px per start, x = 54 + start*27
- Draw 3 curves for 10th/25th/50th percentile
- Target ERA: green dashed line
- Current ERA: rust dashed line
- Opening-Day dot: rust filled circle at origin

---

## Statistical Concepts to Always Explain

### The Denominator Problem
Rate stats are ratios. Small denominators amplify single events catastrophically:
```
ERA = ER × 9 / IP
sensitivity = 9 / IP   ← explodes as IP → 0
```
Translate: "5 ER in ⅔ IP = 5 ER in 0.2% of career innings moved ERA by 7%"

### Stabilization Thresholds (approximate)
| Stat         | PA/IP for stability |
|--------------|---------------------|
| ERA          | 50 IP (seasonal), 150+ IP (reliable) |
| Batting avg  | 150 PA |
| K%           | 70 PA |
| BB%          | 120 PA |
| FG% (hoops)  | 100 attempts |
| QB rating    | 100+ pass attempts |
| Save %       | 30+ save opportunities |

### Recovery Math
```
Deficit = 9×current_ER − target_ERA×current_IP
Units gained per start = target_ERA×IP_start − 9×ER_start
  → positive only when start_ERA < target_ERA
```

### Bayesian Intuition
The Gamma-Poisson model treats a player's true rate as uncertain (Gamma prior)
and updates based on all observed events (career + bad game = posterior).
Future starts are drawn from this posterior — meaning the model respects both
"he's historically great" and "something weird just happened."

---

## Historical Parallel Template

For each historical parallel, structure as:
1. **Setup**: Who, when, what happened (1–2 sentences)
2. **The number**: What was the extreme stat
3. **The math**: Why it looked so bad
4. **The recovery**: How long, what it took, outcome

### Canonical Parallels (for pitchers)

**Dwight Gooden, April 1984 (second career start)**
Second career start at Wrigley: 3⅓ IP, 6 ER. Told his father he "may not be
ready yet." He was. Gooden went on to finish 17-9 that season, then produced
a 1.53 ERA in 1985 — arguably the greatest single season since the Deadball
Era. The bad start is now a footnote.

**Doc Gooden's 1985 ERA started at 4.50**
After his first start of 1985, Gooden's ERA stood at 4.50. His second start
was a complete-game shutout with 10 Ks. His ERA never went above 2.00 for the
rest of the year. The opening stumble became invisible.

**Roger Clemens, 1986 Opening Day**
Coming off back-to-back Cy Young seasons, Clemens occasionally had brutal short
outings that inflated his ERA briefly before his workload diluted them. His
career ERA of 3.12 weathered every individual disaster because the denominator
— 4,916 IP — made any single start a rounding error.

**Pedro Martínez, 2000 AL**
Pedro's 1.74 ERA in 2000 was so dominant that even after rough outings his
ERA barely twitched — because the denominator was large. By contrast, a
comparable rate in his 2nd career start would have shown an ERA >30.

---

## Ask the Stats Desk — AI Tool Template

```html
<div class="stats-desk">
  <div class="stats-desk-head">Ask The Stats Desk</div>
  <div class="stats-desk-sub">Drop any strange stat. Get context.</div>

  <!-- Quick examples -->
  <div class="desk-examples">
    <span class="desk-example" onclick="fillExample(this)">Batter is .667 after 3 AB</span>
    <span class="desk-example" onclick="fillExample(this)">Kicker 0-for-3 (0% hit rate)</span>
    <!-- add more examples relevant to the newsletter's sport -->
  </div>

  <textarea id="stat-input" placeholder="Paste your weird stat here..."></textarea>
  <button onclick="askDesk()">▶ Explain the Context</button>

  <div id="desk-response"></div>
</div>

<script>
async function askDesk() {
  const input = document.getElementById('stat-input').value.trim();
  if (!input) return;
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system: `You are The Stats Desk — a sharp sports statistics explainer.
Given a weird sports stat, explain:
1. WHY the number looks so extreme (denominator, leverage, small sample)
2. What it would take to sustain it — anchor to reality
3. Historical context: has anyone been here before?
4. What it actually MEANS vs what it DOESN'T mean
5. Verdict: red flag / noise / genuinely impressive?
Style: editorial, dry wit, flowing paragraphs, no bullet lists. 2-4 paragraphs.`,
      messages: [{ role: "user", content: input }]
    })
  });
  const data = await resp.json();
  const text = data.content?.find(b=>b.type==='text')?.text || "No response.";
  document.getElementById('response-text').textContent = text;
  document.getElementById('desk-response').classList.add('visible');
}
</script>
```

---

## Quality Checklist (before presenting artifact)

- [ ] Headline includes the extreme number
- [ ] Denominator math is shown explicitly  
- [ ] At least 2 historical parallels found via web search
- [ ] Bayesian model run with ≥100,000 simulations
- [ ] Recovery percentiles mapped to actual schedule dates
- [ ] P(never recover this season) stated explicitly
- [ ] "Ask the Stats Desk" AI tool functional with Anthropic API call
- [ ] All assumptions stated in footer
- [ ] Broadsheet aesthetic: Playfair Display + Libre Baskerville + Roboto Mono
- [ ] **Cross-reference check**: Grep for "Issue #", "Issue No.", and "See Issue" — verify every reference points to an ALREADY PUBLISHED issue using reader-facing numbers (not internal file numbers). If referencing an unpublished piece, use "coming soon" instead of a number.

---

## Adapting to Other Sports

| Sport | Rate Stat | Denominator | Bayesian Model |
|-------|-----------|-------------|----------------|
| Baseball (pitching) | ERA | IP | Gamma-Poisson on ER/inn |
| Baseball (hitting) | BA, OBP | PA | Beta-Binomial on hits/PA |
| Basketball | FG%, 3P% | Attempts | Beta-Binomial |
| Football | Passer Rating | Pass attempts | Beta-Binomial on comp, TD, INT |
| Football | FG% | Attempts | Beta-Binomial |
| Soccer | xG conversion | Shots | Beta-Binomial |
| Hockey | SV% | Shots faced | Beta-Binomial |

For Beta-Binomial:
```python
# Prior: Beta(α, β) where α, β derived from career stats
# Update: observed successes/failures → Beta(α+successes, β+failures)
# Posterior predictive: Beta-Binomial
alpha_post = career_successes + prior_alpha
beta_post  = career_failures  + prior_beta
p_samples  = np.random.beta(alpha_post, beta_post, N_SIM)
```

---

## Example Trigger Phrases

This skill should fire whenever you see phrases like:
- "that's a crazy [stat]" / "what does that number mean"
- "how bad is [X]" / "how good is [X]" for a rate stat
- "he'll never recover" / "how long to fix his ERA"
- "worst [stat] in history" / "best ever through [N games/starts]"
- "is [small-sample stat] real"
- Any stat with explicit small sample: "through 3 starts", "in his first AB"

---

## Publishing Workflow (for automated and manual publishing)

### Repository Structure

```
index.html              <- Homepage with issue archive
publish.sh              <- One-command publish script
assets/                 <- Logo, banner, favicon, QR code
published/              <- LIVE issues (linked from index.html)
queue/                  <- Ready to publish (NOT linked)
reserve/                <- Evergreen, no specific date
```

### How to Publish an Issue (step by step)

1. **Select the article** from `queue/`. Priority:
   - Timely pieces first (breaking news, game reactions)
   - Then analytical pieces (series parts, trade analyses)
   - Sunday = publish the Sunday Edition recap

2. **Determine reader issue number**: Count `<div class="issue">` blocks in `index.html`. The next issue is that count + 1. This is the READER-FACING number — NOT the internal filename number.

3. **Update the HTML file**:
   - Find all occurrences of `Issue No. [TBD]` or `Issue No. XX` (usually 2: datebar and footer)
   - Replace with the correct reader number: `Issue No. 14`
   - Update the date if it has a placeholder or old date

4. **Cross-reference check** (REQUIRED):
   ```bash
   grep -n "Issue #\|See Issue" queue/FILENAME.html
   ```
   Every reference must point to an ALREADY PUBLISHED issue using reader-facing numbers. If it references an unpublished piece, change to "coming soon" or remove the reference.

5. **Add entry to index.html**: Insert a new issue block at the TOP of `<div class="issues">`, BEFORE all existing issues. Use this exact HTML pattern:
   ```html
   <div class="issue">
     <div class="issue-num">NUMBER</div>
     <div class="issue-body">
       <div class="issue-date">Month Day, Year</div>
       <div class="issue-hed"><a href="published/FILENAME.html">HEADLINE</a></div>
       <div class="issue-deck">One-sentence summary.</div>
       <div class="issue-tags">
         <span class="tag mlb">SPORT</span>
         <span class="tag">TOPIC</span>
       </div>
     </div>
   </div>
   ```
   Available tag classes: `.mlb`, `.nfl`, `.nhl`, `.cfb` (colored), or plain `.tag`.

6. **Move the file**:
   ```bash
   git mv queue/FILENAME.html published/FILENAME.html
   ```

7. **Commit and push**:
   ```bash
   git add index.html published/FILENAME.html
   git commit -m "Publish Issue #N: brief description"
   git push
   ```

### Sunday Edition Workflow

The Sunday Edition MUST be built fresh on Sunday morning — never from a pre-built draft. Follow these steps:

**Step 1 — Gather fresh data (REQUIRED before writing anything)**:
- Use web search to pull current MLB standings, team records, and player stats
- Check injury report updates (especially for players we've been tracking, e.g., Soto calf)
- Get current NHL standings and playoff picture
- Check NFL draft news if draft season
- Get any other relevant current stats for teams we cover

**Step 2 — Rerun prediction models with updated data**:
For EVERY prediction made in the past week's issues, rerun the relevant model:
- Beta-Binomial BA projections: update with current AB/hits
- Bayesian injury estimates: update with actual recovery timeline
- Season win projections: update with current W-L record
- Any other quantitative prediction: pull actual outcome and compare

**Step 3 — Score each prediction**:
- **HIT**: Our prediction/model matched the outcome within a reasonable margin
- **MISS**: We were materially wrong — own it, explain why
- **PARTIALLY HIT**: Direction was right, magnitude was off (or vice versa)
- **PENDING**: Not enough data yet to judge — state what we're still watching

**Step 4 — Write the Sunday Edition**:
- Recap each issue from the week with a one-line summary and link
- Present the prediction scorecard with FRESH numbers (not stale pre-built data)
- Honest self-assessment: over-reactions and under-reactions
- What we learned, what we'd do differently
- Preview of next week's planned content

**Step 5 — Publish**:
- Follow the standard 7-step publish workflow
- This issue should be LONGER than regular issues

**Key rule**: If a Sunday Edition skeleton exists in `queue/` from an earlier session, treat it as a TEMPLATE ONLY. Replace all statistics, scores, and predictions with fresh data pulled that morning. Never publish stale numbers on Sunday.

### Issue Numbering Rules

- **Reader-facing numbers** are sequential: #1, #2, #3... assigned at publish time
- **Internal filenames** keep their creation-order numbers (e.g., `010-soto-calf.html` was published as reader Issue #7)
- NEVER expose internal file numbers to readers
- Count existing published entries in index.html to determine the next number

### Content Tiers

| Tier | Shelf Life | When to Publish |
|------|-----------|-----------------|
| Timely | Hours to 1 day | Immediately — goes stale fast |
| Analytical | 1-2 weeks | Fill gaps between timely pieces |
| Evergreen | Indefinite | Slow news weeks, pre-season |
| Sunday Edition | Must be fresh | Sunday mornings only |

### Editorial Rules

- ONE statistical question per issue
- No holiday specials — sports only
- Do NOT label who roots for which team — cover the teams naturally
- Milestone celebrations at Issue #50, #100, etc.
- No basketball content
- Goal: 500 total issues over ~2 years

### Team Priorities (in order)

1. Notre Dame football (always, year-round)
2. College football (during season; off-season only for ND)
3. NY Mets (during season)
4. NY Rangers (when doing well)
5. NY Jets + Raiders, Bills, Seahawks (extended family)
6. Any player with a remarkably great or terrible performance
