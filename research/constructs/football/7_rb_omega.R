# Omega: how much of a running back's rushing line is ONE general ability?
suppressMessages({library(psych); library(GPArotation); library(lavaan)})
o <- readRDS('data/rb_nfl_X.rds'); X <- o$X; n <- o$n
R <- X[,c('ypc','ryoe','r10','r20','fd','epa','rtd','fum')]
om <- omega(R, nfactors=3, fm='ml', plot=FALSE)
cat('rushing items: omega total', round(om$omega.tot,2), ' omega hierarchical', round(om$omega_h,2),
    ' alpha', round(om$alpha,2), '\n'); print(round(om$schmid$sl[,1:4],2))
# split-half check: explore half A (by player), confirm a 5-factor CFA in half B
set.seed(11); ids <- unique(n$gsis); A <- n$gsis %in% sample(ids, length(ids)/2)
M <- '
 breakaway =~ ypc + ryoe + r10 + r20
 chains    =~ fd + epa + rtd + fum
 receiving =~ ypr + yac
 patience  =~ ttl + eff
 role      =~ box8 + tgtg + carg'
Z <- as.data.frame(scale(X)); FM <- c('cfi.robust','rmsea.robust','srmr')
for(h in c('A','B')){ f <- cfa(M, Z[if(h=='A') A else !A,], estimator='MLR', std.lv=TRUE); cat('CFA half', h, 'n=', nobs(f), round(fitMeasures(f,FM),3), '\n') }
f <- cfa(M, Z, estimator='MLR', std.lv=TRUE); s <- standardizedSolution(f)
print(s[s$op=='=~',c('lhs','rhs','est.std')], digits=2, row.names=FALSE)
print(round(lavInspect(f,'cor.lv'),2))
saveRDS(f, 'data/rb_cfa.rds')
