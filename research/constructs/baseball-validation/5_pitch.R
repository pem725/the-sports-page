# Pitchers 2015-2025: starters and relievers separately. Primitives per batter faced + Statcast.
suppressMessages({library(psych); library(GPArotation); library(lavaan)})
p <- read.csv('data/pitchers.csv'); p$half <- ifelse(p$pid %% 2 == 0, 'A', 'B')
V <- c('so','ubb','hbp','hr','wp','hbip','goao','velo','whiff','chase','zswing','ev','gb')
for(r in c('SP','RP')){
  X <- p[p$role==r & p$half=='A', V]; cat('\n=====', r, 'half A n =', nrow(X), '\n'); cat('scree:', round(eigen(cor(X))$values[1:7],2), '\n')
  pa <- fa.parallel(X, fa='fa', plot=FALSE); cat('parallel:', pa$nfact, ' MAP:', which.min(VSS(X,7,plot=FALSE)$map), '\n')
  for(k in 3:4){ f <- fa(X, k, rotate='oblimin', fm='ml'); cat('--',k,'factors RMSEA', round(f$RMSEA[1],3), 'TLI', round(f$TLI,2), '\n')
    L <- unclass(f$loadings); L[abs(L)<.3] <- NA; print(round(L,2), na.print='.'); print(round(f$Phi,2)) } }
write.csv(p, 'data/pitchers.csv', row.names=FALSE)
