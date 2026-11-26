# What does a running back's stat line measure? NFL RB-seasons 2016-2025, 100+ carries.
# Cattell's scree + parallel analysis + MAP, then oblique EFA, then omega.
suppressMessages({library(psych); library(GPArotation)})
n <- read.csv('data/rb_nfl.csv'); n <- n[n$year>=2016 & n$year<=2025 & !is.na(n$ryoe),]
touch <- n$car + n$rec
X <- data.frame(ypc=n$yds/n$car, ryoe=n$ryoe, fd=n$fd/n$car, r10=n$r10/n$car, r20=n$r20/n$car,
  epa=n$epa/n$car, rtd=n$rtd/n$car, fum=n$fum/touch, carg=n$car/n$games, tgtg=n$tgt/n$games,
  catch=ifelse(n$tgt>0,n$rec/n$tgt,NA), ypr=ifelse(n$rec>0,n$recyds/n$rec,NA), yac=ifelse(n$rec>0,n$yac/n$rec,NA),
  box8=n$box8, ttl=n$ttl, eff=n$eff)
ok <- complete.cases(X); X <- X[ok,]; n <- n[ok,]
cat('RB-seasons:', nrow(X), ' players:', length(unique(n$gsis)), '\n')
ev <- eigen(cor(X))$values; cat('eigenvalues (scree):', round(ev[1:8],2), '\n')
pa <- fa.parallel(X, fa='fa', plot=FALSE); cat('parallel analysis:', pa$nfact, '  MAP:', which.min(VSS(X,8,plot=FALSE,rotate='oblimin')$map), '\n')
for(k in 3:5){ f <- fa(X, k, rotate='oblimin', fm='ml'); cat('\n--', k, 'factors; RMSEA', round(f$RMSEA[1],3), ' TLI', round(f$TLI,2), '\n')
  L <- unclass(f$loadings); L[abs(L)<.3] <- NA; print(round(L,2), na.print='.'); print(round(f$Phi,2)) }
saveRDS(list(X=X, n=n), 'data/rb_nfl_X.rds')  # needed by 7-10
