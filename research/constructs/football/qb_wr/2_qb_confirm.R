suppressMessages({library(lavaan); library(psych); library(GPArotation)})
d <- read.csv('data/qb.csv'); h <- d[d$year<=2025,]
V <- c('cpoe','bad','ttt','scr','throwaway','td','fd','sack')
h <- h[complete.cases(h[,V]),]; mu <- colMeans(h[,V]); sdv <- apply(h[,V],2,sd); Z <- as.data.frame(scale(h[,V],mu,sdv))
# Dropped after testing: 'downfield' (aggr, adot, yac) does not cohere in a CFA (adot loads 2.2);
# PFR pressure includes sacks (composite) and is partly the line; pocket time duplicates time to throw.
M <- '
 accuracy =~ cpoe + bad
 holds    =~ ttt + scr + throwaway
 chains   =~ td + fd + sack
 scr ~~ sack    # bookkeeping: a dropback ends as an attempt, a sack or a scramble'
FM <- c('cfi.robust','rmsea.robust','srmr')
set.seed(21); ids <- unique(h$gsis); A <- h$gsis %in% sample(ids, length(ids)/2)
for(s in c('A','B','all')){ dd <- if(s=='A') Z[A,] else if(s=='B') Z[!A,] else Z
  f <- cfa(M, dd, estimator='MLR', std.lv=TRUE, bounds='pos.var'); cat(s, nobs(f), lavInspect(f,'converged'), round(fitMeasures(f,FM),3), '\n') }
s <- standardizedSolution(f); print(s[s$op=='=~',c('lhs','rhs','est.std','ci.lower','ci.upper')], digits=2, row.names=FALSE)
print(round(lavInspect(f,'cor.lv'),2))
mi <- modindices(f, sort.=TRUE); print(head(mi[,c('lhs','op','rhs','mi')],5), row.names=FALSE)
om <- omega(h[,c('cpoe','bad','td','fd','sack','ttt','scr','throwaway')], nfactors=3, fm='ml', plot=FALSE)
cat('omega total', round(om$omega.tot,2), ' omega hierarchical', round(om$omega_h,2), '\n')
saveRDS(list(f=f, mu=mu, sdv=sdv, M=M), 'data/qb_model.rds')
