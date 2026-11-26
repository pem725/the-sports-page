suppressMessages({library(psych); library(GPArotation)})
d <- read.csv('data/qb.csv'); d <- d[d$year<=2025,]
V <- c('comp','cpoe','adot','yac','td','int','sack','scr','bad','press','pocket','throwaway','ttt','aggr','fd')
X <- d[,V]; ok <- complete.cases(X); X <- X[ok,]; cat('QB-seasons', nrow(X), 'of', nrow(d), ' players', length(unique(d$gsis[ok])), '\n')
cat('scree:', round(eigen(cor(X))$values[1:7],2), '\n'); pa <- fa.parallel(X, fa='fa', plot=FALSE); cat('parallel', pa$nfact, ' MAP', which.min(VSS(X,7,plot=FALSE)$map), '\n')
for(k in 3:5){ f <- fa(X, k, rotate='oblimin', fm='ml'); cat('--',k,'RMSEA',round(f$RMSEA[1],3),'TLI',round(f$TLI,2),'\n'); L<-unclass(f$loadings); L[abs(L)<.3]<-NA; print(round(L,2),na.print='.'); print(round(f$Phi,2)) }
