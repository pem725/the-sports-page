# Your model, tested on the samples it has not seen.
#
# The four-factor model below was revised on sample B, so only sample C counts as a real
# test of it. Write YOUR hypothesis of what hitting stats measure in `mine` and it is fit
# on B and C beside it. If you specify it before looking at B, B counts as a real test too.
#
# Variables available (all per plate appearance, square-rooted, z-scored):
#   single double triple hr ubb ibb hbp so sac sf gidp   plus
#   sbatt (steal tries per time on base), pitches (per PA), goao (log ground/air outs)
# Outcomes kept out of the model: runs, rbi.
suppressMessages(library(lavaan))
V <- c('single','double','triple','hr','ubb','ibb','hbp','so','sbatt','gidp','sac','sf','pitches','goao')
z <- function(d){ for(v in V) d[[v]] <- as.numeric(scale(d[[v]])); d }
p <- read.csv('data/players.csv'); B <- z(p[p$half=='B',])
o <- read.csv('data/old.csv');     C <- z(o[!(o$pid %in% p$pid),])

ours <- '
 patience =~ ubb + pitches
 contact  =~ single + so
 speed    =~ sbatt + triple + gidp + sac
 power    =~ hr + ibb + sac + so'

# TODO(editor): your constructs. A bipolar "swing" factor (hr and so up, single down) in
# place of separate contact and power? Doubles and sac flies treated as noise? Your call.
mine <- '
'

for(d in c('B','C')) for(nm in c('ours','mine')){
  if(!nzchar(trimws(get(nm)))) next
  f <- cfa(get(nm), data=get(d), estimator='MLR', std.lv=TRUE)
  fm <- fitMeasures(f, c('cfi.robust','rmsea.robust','srmr','bic'))
  cat(d, nm, 'n =', nobs(f), paste(names(fm), round(fm, 3), collapse='  '), '\n')
}
