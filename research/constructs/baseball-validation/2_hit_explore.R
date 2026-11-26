# Hitters 2015-2025, 300+ PA. Box-score primitives plus Statcast. Explore on half A (by player).
suppressMessages({library(psych); library(GPArotation)})
h <- read.csv('data/hitters.csv')
V <- c('single','double','triple','hr','ubb','hbp','so','sbatt','gidp','pitches','goao','ev','la','chase','zswing','whiff','sprint')
# ibb and sac are manager's calls (they break era invariance), left out; barrel/hard-hit are EV/LA composites
h$half <- ifelse(h$pid %% 2 == 0, 'A', 'B'); write.csv(h, 'data/hitters.csv', row.names=FALSE)
X <- h[h$half=='A', V]; cat('half A player-seasons', nrow(X), '\n')
cat('scree:', round(eigen(cor(X))$values[1:8],2), '\n')
pa <- fa.parallel(X, fa='fa', plot=FALSE); cat('parallel:', pa$nfact, ' MAP:', which.min(VSS(X,8,plot=FALSE)$map), '\n')
for(k in 4:6){ f <- fa(X, k, rotate='oblimin', fm='ml'); cat('\n--', k, 'factors RMSEA', round(f$RMSEA[1],3), 'TLI', round(f$TLI,2), '\n')
  L <- unclass(f$loadings); L[abs(L)<.3] <- NA; print(round(L,2), na.print='.'); print(round(f$Phi,2)) }
