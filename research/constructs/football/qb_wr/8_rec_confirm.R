suppressMessages({library(lavaan); library(psych); library(GPArotation)})
d <- read.csv('data/rec.csv'); h <- d[d$year<=2025 & d$pos=='WR',]
V <- c('yacoe','brk','sep','cush','catch','drop','tps','adot','td')
h <- h[complete.cases(h[,V]),]; mu <- colMeans(h[,V]); sdv <- apply(h[,V],2,sd); Z <- as.data.frame(scale(h[,V],mu,sdv))
M <- '
 after   =~ yacoe + brk
 open    =~ sep + cush
 hands   =~ catch + drop + tps + adot   # deep targets are caught less often (mechanical)
 deep    =~ adot + td'
FM <- c('cfi.robust','rmsea.robust','srmr')
set.seed(31); ids <- unique(h$gsis); A <- h$gsis %in% sample(ids, length(ids)/2)
for(s in c('A','B','all')){ dd <- if(s=='A') Z[A,] else if(s=='B') Z[!A,] else Z
  f <- cfa(M, dd, estimator='MLR', std.lv=TRUE, bounds='pos.var'); cat(s, nobs(f), lavInspect(f,'converged'), round(fitMeasures(f,FM),3), '\n') }
s <- standardizedSolution(f); print(s[s$op=='=~',c('lhs','rhs','est.std','ci.lower','ci.upper')], digits=2, row.names=FALSE)
print(round(lavInspect(f,'cor.lv'),2)); mi <- modindices(f, sort.=TRUE); print(head(mi[,c('lhs','op','rhs','mi')],5), row.names=FALSE)
om <- omega(h[,V], nfactors=4, fm='ml', plot=FALSE); cat('omega total', round(om$omega.tot,2), ' omega hierarchical', round(om$omega_h,2), '\n')
saveRDS(list(f=f, mu=mu, sdv=sdv), 'data/rec_model.rds')
