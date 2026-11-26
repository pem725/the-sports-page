# Theory-based revision, made on half A, then tested unchanged on half B.
suppressMessages({library(lavaan); library(psych)})
h <- read.csv('data/hitters.csv'); m <- readRDS('data/hit_model.rds')
V <- setdiff(m$V, 'double'); Z <- as.data.frame(scale(h[,V], m$mu[V], m$sdv[V]))
M2 <- '
 eager  =~ chase + zswing + ubb + pitches
 miss   =~ so + whiff + single + pitches
 power  =~ ev + hr
 lift   =~ la + goao + hr + single
 speed  =~ sprint + sbatt + triple + gidp
 so ~~ whiff'
FM <- c('cfi.robust','tli.robust','rmsea.robust','srmr')
fA <- cfa(M2, Z[h$half=='A',], estimator='MLR', std.lv=TRUE); fB <- cfa(M2, Z[h$half=='B',], estimator='MLR', std.lv=TRUE)
cat('revised, half A', round(fitMeasures(fA,FM),3), '\nrevised, half B', round(fitMeasures(fB,FM),3), '\n')
s <- standardizedSolution(fB); print(s[s$op=='=~',c('lhs','rhs','est.std','ci.lower','ci.upper')], digits=2, row.names=FALSE)
print(round(lavInspect(fB,'cor.lv'),2))
om <- omega(Z[h$half=='B',], nfactors=5, fm='ml', plot=FALSE); cat('omega total', round(om$omega.tot,2), ' omega_h', round(om$omega_h,2), '\n')
fall <- cfa(M2, Z, estimator='MLR', std.lv=TRUE)
saveRDS(list(f=fall, mu=m$mu[V], sdv=m$sdv[V], M=M2, V=V), 'data/hit_model.rds')
