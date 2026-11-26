# One-tool audit: 20 codes for the editor

Five of each verdict, drawn at random (seed 1126). For each: open the issue, read the code, and mark **agree** or **disagree** (with the verdict you would give). The piece reports how many you agreed with.

Verdicts: SAME · SAME-WRONG-REASON · CHANGED · CANNOT-ASK. The one-tool analyst: t-tests and ANOVA only, median splits, every row independent, p < .05 means real, no design, no measurement (see CODEBOOK.md).

## #19: The Executive Order Isn’t Saving College Sports. It’s Restoring the Old Guard — With One Dangerous Asterisk.
https://thesportspage.net/published/eo-005-big-picture.html

- **Decision:** The executive order's transfer limits, NIL caps and eligibility rules will push blue-blood title share back toward 78-83%.
- **One-tool analysis:** two-sample t-test of blue-blood title (0/1), pre-portal vs portal era
- **Verdict:** CANNOT-ASK (no-forecast)
- **Why:** The decision is a projected future title share under the order, which the tool cannot make; a 12-title portal-era comparison would also come out non-significant and be read as no change.
- **Your call:** agree / disagree → ______

## #20: WNBA Players Make 116x Less Than NBA Players. That Number Is True. It’s Also the Wrong Comparison.
https://thesportspage.net/published/016-wnba-pay-maturity.html

- **Decision:** The 116x WNBA-NBA pay gap is the wrong comparison; matched for league age, inflation and roster size the WNBA pays comparably.
- **One-tool analysis:** t-test of WNBA vs NBA current salaries
- **Verdict:** CHANGED (measurement)
- **Why:** The analyst compares today's salaries raw, gets an enormous significant gap and endorses exactly the framing the issue rejects.
- **Your call:** agree / disagree → ______

## #25: Fifty Years, One Hall of Famer , and a 28% Rate at the Top of the Draft
https://thesportspage.net/published/020-jets-first-round-busts.html

- **Decision:** The Jets' first-round picks since 1976 have failed every definition of success 28% of the time.
- **One-tool analysis:** none needed; at most a t-test of Jets bust rate vs league
- **Verdict:** SAME
- **Why:** The core finding is a counted rate with no inference to get wrong.
- **Your call:** agree / disagree → ______

## #27: Same Stadium, Different Drafts : Jets vs. Giants, 50 Years In
https://thesportspage.net/published/021-draft-hit-rate-jets-giants.html

- **Decision:** Jets and Giants first-round drafting is comparable; the Giants' edge came from elsewhere.
- **One-tool analysis:** t-test of first-round bust indicator, Jets vs Giants picks
- **Verdict:** SAME-WRONG-REASON (null-not-absence)
- **Why:** The analyst reaches 'comparable' by p > .05 on binary busts, reading a non-significant 71% vs 56% gap as no difference.
- **Your call:** agree / disagree → ______

## #31: The Just-Noticeable Difference in College Football Rankings Is 13
https://thesportspage.net/published/022-cfb-jnd-rankings.html

- **Decision:** Two AP rankings closer than about 13 spots are not reliably distinguishable; arguments over #8 vs #11 are noise.
- **One-tool analysis:** one-way ANOVA (or t-tests) of higher-ranked-team win (0/1) across rank-gap bins, n=1,597
- **Verdict:** CHANGED (significance-not-size)
- **Why:** With 1,597 games even small rank gaps beat 50% significantly, so the analyst would declare every rank difference real, the opposite of the JND conclusion.
- **Your call:** agree / disagree → ______

## #47: The Rockies Have Never Won the West. Nobody’s Mad About It.
https://thesportspage.net/published/037-nobody-hates-rockies.html

- **Decision:** Hatred needs perceived stakes: teams that took a prize from you get hated, so nobody hates the Rockies.
- **One-tool analysis:** t-test of hate sentiment, teams with recent titles/blocking vs not
- **Verdict:** SAME
- **Why:** The issue makes no formal inference, and a crude title vs no-title comparison would point the same way.
- **Your call:** agree / disagree → ______

## #58: Marcus Freeman Won the Portal. Then He Started On 2027.
https://thesportspage.net/published/047-notre-dame-recruiting.html

- **Decision:** Notre Dame is winning both the portal and the 2027 recruiting race, unusual for any program.
- **One-tool analysis:** none needed; descriptive
- **Verdict:** SAME
- **Why:** Recruiting ranks are reported, not inferred.
- **Your call:** agree / disagree → ______

## #61: Forty, Fifty-Seven, Thirty-Two. The Other City Has Forty-Nine.
https://thesportspage.net/published/049-misery-index-ny-dc.html

- **Decision:** New York's three teams carry 129 drought years vs Washington's 49; D.C. fans have less misery.
- **One-tool analysis:** none possible (3 vs 3 droughts)
- **Verdict:** SAME
- **Why:** Pure arithmetic on championship dates, nothing for the tool to change.
- **Your call:** agree / disagree → ______

## #76: Juan Soto Is 94 Spots From Help. That Number Is Lying to You.
https://thesportspage.net/published/065-soto-least-supported.html

- **Decision:** Soto's 94-spot rank gap overstates the skill gap; rank gaps stretch most at the top of a leaderboard.
- **One-tool analysis:** none possible (n=1 vs teammates); would take the rank gap at face value
- **Verdict:** CHANGED (measurement)
- **Why:** Treating ranks as an equal-interval ruler, the analyst accepts '94 spots' as a skill gap, the exact error the issue corrects.
- **Your call:** agree / disagree → ______

## #79: How Do You Win Eight Straight and Then Lose by Six? You Build an Offense Designed to Do Exactly That.
https://thesportspage.net/published/064-mariners-streak.html

- **Decision:** Seattle's boom-and-bust swings are what a high-power, low-average lineup produces by design: variance, not a change in the team.
- **One-tool analysis:** t-test of runs per game during the win streak vs after
- **Verdict:** CHANGED (regression-to-mean)
- **Why:** The tool compares means rather than spread, so a streak-vs-after difference reads as a team getting hot then cold.
- **Your call:** agree / disagree → ______

## #81: What “Banned” Used to Mean. A Lubbock County Judge Just Showed What It Means Now.
https://thesportspage.net/published/083-ncaa-enforcement-collapse.html

- **Decision:** A state judge overruling an NCAA ban shows 'banned' no longer carries weight, even though Sorsby withdrew.
- **One-tool analysis:** none needed; descriptive
- **Verdict:** SAME
- **Why:** No statistical inference is involved.
- **Your call:** agree / disagree → ______

## #126: A Good Week From Your Receiver Is 10× a Bad One. That’s Where the Season Is Decided.
https://thesportspage.net/published/112-variance-is-king.html

- **Decision:** Fantasy matchups are decided in high-variance positions, not by your best average scorer.
- **One-tool analysis:** t-test of mean points by position
- **Verdict:** CANNOT-ASK (no-forecast)
- **Why:** The tool compares means only and cannot pose where the chance of winning a matchup is decided.
- **Your call:** agree / disagree → ______

## #136: The Deepest Wound in Sports Is Always the Same Shape.
https://thesportspage.net/published/116-deepest-wound-same-shape.html

- **Decision:** A 71% season team is only about a 52% bet in one sudden-death moment, so the deepest wounds share a shape.
- **One-tool analysis:** none possible
- **Verdict:** CANNOT-ASK (no-forecast)
- **Why:** The decision is the chance of one event, which the tool cannot express.
- **Your call:** agree / disagree → ______

## #152: Two Teams a Rank Apart? The Higher One Wins 48.7% of the Time.
https://thesportspage.net/published/134-ranking-jnd.html

- **Decision:** Teams 1-2 ranks apart split 48.7/51.3; a ranking needs about 10 places to mean anything.
- **One-tool analysis:** one-way ANOVA of higher-ranked win indicator by rank-gap bin; t-tests vs .5
- **Verdict:** SAME-WRONG-REASON (null-not-absence)
- **Why:** Small gaps come out non-significant and read as 'no difference', near the issue's answer, but the threshold would move with sample size, not effect size.
- **Your call:** agree / disagree → ______

## #156: The Mets Cannot Ruin Anybody. The Athletics Can Ruin Four Seasons.
https://thesportspage.net/published/144-spoiler.html

- **Decision:** The eliminated Athletics can move about 201 points of other clubs' playoff odds; the Mets only 93.
- **One-tool analysis:** none possible
- **Verdict:** CANNOT-ASK (no-forecast)
- **Why:** Leverage is built from simulated playoff probabilities the tool cannot produce.
- **Your call:** agree / disagree → ______

## #165: One Game Told Us More Than the Whole Summer Did.
https://thesportspage.net/published/145-week1-signal.html

- **Decision:** An opening-week win is worth about 1.5 extra wins after controlling for talent; one game says more than the summer's indicators.
- **One-tool analysis:** two-sample t-test of final win% for week-one winners vs losers
- **Verdict:** SAME-WRONG-REASON (no-design)
- **Why:** The naive t-test also says the opener matters (1.8 wins) but folds talent into the gap the issue controls for.
- **Your call:** agree / disagree → ______

## #168: Detroit Outscored Its Opponents by 55 Runs. It Is Twelve Games Under.
https://thesportspage.net/published/153-one-run-luck.html

- **Decision:** Detroit's +55 run differential says about 79 wins; the 12-games-under record sits in one-run games, which is mostly luck.
- **One-tool analysis:** median split clubs on one-run win%, t-test next season's one-run win%
- **Verdict:** SAME-WRONG-REASON (null-not-absence)
- **Why:** The t-test would come out non-significant and say one-run records do not repeat, but as proof of absence and with no expected-wins figure, which the issue backs with a control correlation.
- **Your call:** agree / disagree → ______

## #220: Will Toney Play? Two of Every Three Questionable Players Do.
https://thesportspage.net/published/202-questionable.html

- **Decision:** A questionable player plays about 2 times in 3 (9,634 of 14,346); start there, then adjust.
- **One-tool analysis:** none possible
- **Verdict:** CANNOT-ASK (no-forecast)
- **Why:** The issue's decision is one player's chance of playing, and the tool has no single-event probability.
- **Your call:** agree / disagree → ______

## #221: Nine Traded Stars in Ten Fall Short. Four Trades in Five Do Not.
https://thesportspage.net/published/192-blockbuster-trades.html

- **Decision:** Only about 9% of traded stars match their past, yet the team that gets the star loses the trade fewer than one time in five.
- **One-tool analysis:** paired t-test of star WAR before vs after trade; t-test of WAR received vs sent
- **Verdict:** SAME-WRONG-REASON (regression-to-mean)
- **Why:** The analyst gets both numbers' direction but reads the selected-on-peak decline as an effect of the trade.
- **Your call:** agree / disagree → ______

## #236: Is Your Team Getting Hot at the Right Time?
https://thesportspage.net/published/209-momentum.html

- **Decision:** Five-game streaks add about 1 win in 100 beyond team strength; a hot finish adds nothing to playoff runs once the full season is known.
- **One-tool analysis:** t-test of next-game win%, teams on 5-game streaks vs not
- **Verdict:** CHANGED (no-design)
- **Why:** Streaking teams are better teams, so the raw test is significant and says momentum is real.
- **Your call:** agree / disagree → ______
