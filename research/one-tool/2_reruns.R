# Validation reruns: the one-tool analyst (t-tests and ANOVA only) on two published issues,
# using the same NFL team-game data (data/nfl/team-games.csv, nflverse, 1999-2025).
d <- read.csv('../../data/nfl/team-games.csv'); d <- d[d$points_for != d$points_against,]
d$top_min <- d$top_seconds/60
cat('team-games:', nrow(d), '\n\n')
## #179 "Your team held the ball longer. That just means they were ahead."
cat('#179 time of possession\n')
t1 <- t.test(top_min ~ win, d); print(round(c(mean_loser=t1$estimate[[1]], mean_winner=t1$estimate[[2]], t=t1$statistic[[1]], p=t1$p.value),4))
d$top_grp <- cut(d$top_min, quantile(d$top_min, 0:3/3), include.lowest=TRUE, labels=c('low','mid','high'))
a <- aov(win ~ top_grp, d); print(summary(a)); print(round(tapply(d$win, d$top_grp, mean),3))
cat('one-tool verdict: winners hold the ball longer (p < .001); more possession -> more wins. Decision: "control the clock to win".\n')
cat('issue verdict: the lead causes the possession (teams ahead run); a 4th-quarter run share of 67 vs 22 per 100 by score.\n')
# what the one-tool analyst never looks at: possession time in the FIRST three quarters is not in this file;
# show instead that the link nearly vanishes once you compare teams with the same final margin band
d$margin <- d$points_for - d$points_against
close <- d[abs(d$margin) <= 3,]
t2 <- t.test(top_min ~ win, close); cat('\nclose games only (margin <= 3): winner - loser TOP =', round(diff(t2$estimate),2), 'min, p =', signif(t2$p.value,2), ' n =', nrow(close), '\n')
## #181 "Turnovers win games. They do not win seasons."
cat('\n#181 turnovers\n')
t3 <- t.test(turnovers ~ win, d); cat('turnovers, losers vs winners:', round(t3$estimate,2), ' p =', signif(t3$p.value,2), '\n')
# season halves: does a team's turnover margin persist?
opp <- d[,c('game_id','team','turnovers')]; names(opp) <- c('game_id','opp','opp_to')
d2 <- merge(d, opp, by=c('game_id','opp')); d2$tomargin <- d2$opp_to - d2$turnovers
d2$half <- ifelse(d2$week <= 9, 'first', 'second')
s <- aggregate(tomargin ~ season + team + half, d2, mean); w <- reshape(s, idvar=c('season','team'), timevar='half', direction='wide'); w <- w[complete.cases(w),]
pt <- t.test(w$tomargin.first, w$tomargin.second, paired=TRUE)
cat('paired t-test, first-half vs second-half turnover margin per game:', round(pt$estimate,3), ' p =', signif(pt$p.value,2), ' (n team-seasons =', nrow(w), ')\n')
cat('one-tool verdict: no significant change between halves -> "turnover margins are stable; good ball-hawking teams stay good".\n')
r <- cor(w$tomargin.first, w$tomargin.second); ci <- tanh(atanh(r) + c(-1.96,1.96)/sqrt(nrow(w)-3))
cat('what the paired t-test cannot see: correlation first half -> second half r =', round(r,2), '[', round(ci[1],2), ',', round(ci[2],2), ']\n')
w$g <- cut(w$tomargin.first, quantile(w$tomargin.first, 0:3/3), include.lowest=TRUE, labels=c('worst third','middle','best third'))
print(round(sapply(split(w, w$g), function(x) c(first=mean(x$tomargin.first), second=mean(x$tomargin.second))),2))
