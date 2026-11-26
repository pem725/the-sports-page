# Confirm the five hitting constructs on half B; omega; same-player reliability.
suppressMessages({library(lavaan); library(psych); library(GPArotation)})
h <- read.csv('data/hitters.csv')
V <- c('single','double','triple','hr','ubb','so','sbatt','gidp','pitches','goao','ev','la','chase','zswing','whiff','sprint')
mu <- colMeans(h[h$half=='A',V]); sdv <- apply(h[h$half=='A',V],2,sd)
Z <- as.data.frame(scale(h[,V], mu, sdv))
M <- '
 eager  =~ chase + zswing + ubb + pitches
 miss   =~ so + whiff + single
 power  =~ ev + hr + double
 lift   =~ la + goao
 speed  =~ sprint + sbatt + triple + gidp'
FM <- c('cfi.robust','tli.robust','rmsea.robust','srmr')
fA <- cfa(M, Z[h$half=='A',], estimator='MLR', std.lv=TRUE); fB <- cfa(M, Z[h$half=='B',], estimator='MLR', std.lv=TRUE)
cat('half A', round(fitMeasures(fA,FM),3), '\nhalf B', round(fitMeasures(fB,FM),3), '\n')
s <- standardizedSolution(fB); print(s[s$op=='=~',c('lhs','rhs','est.std','ci.lower','ci.upper')], digits=2, row.names=FALSE)
print(round(lavInspect(fB,'cor.lv'),2))
mi <- modindices(fB, sort.=TRUE); print(head(mi[,c('lhs','op','rhs','mi')],6), row.names=FALSE)
# omega on all 16 indicators (half B)
om <- omega(Z[h$half=='B',], nfactors=5, fm='ml', plot=FALSE)
cat('\nomega total', round(om$omega.tot,2), ' omega hierarchical', round(om$omega_h,2), '\n')
saveRDS(list(f=fB, mu=mu, sdv=sdv, M=M, V=V), 'data/hit_model.rds')
