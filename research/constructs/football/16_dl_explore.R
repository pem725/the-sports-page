# What do a defensive lineman's stats measure? EFA by group, 2018-2025, 300+ snaps, per 100 snaps.
# Primitives only: PFR 'pressures' = hurries + knockdowns + sacks, so its parts go in, not it.
suppressMessages({library(psych); library(GPArotation)})
d <- read.csv('data/dl.csv')
V <- c('hrry','qbkd','sacks','tfl_run','tk_run','tk_pass','ff','pd','mtkl_pct')   # bats: 2024+ only, left out
for(g in c('edge','interior')){
  X <- d[d$grp==g, V]; X <- X[complete.cases(X),]
  cat('\n=====', g, ' n =', nrow(X), '\n'); cat('scree:', round(eigen(cor(X))$values[1:6],2), '\n')
  pa <- fa.parallel(X, fa='fa', plot=FALSE); cat('parallel:', pa$nfact, ' MAP:', which.min(VSS(X,6,plot=FALSE)$map), '\n')
  for(k in 2:3){ f <- fa(X, k, rotate='oblimin', fm='ml'); cat('--', k, 'factors  RMSEA', round(f$RMSEA[1],3), ' TLI', round(f$TLI,2), '\n')
    L <- unclass(f$loadings); L[abs(L)<.25] <- NA; print(round(L,2), na.print='.'); print(round(f$Phi,2)) }
  cat('correlations of run-TFL with:\n'); print(round(cor(X)['tfl_run',],2))
}
