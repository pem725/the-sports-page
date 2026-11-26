suppressMessages({library(psych); library(GPArotation)})
d <- read.csv('data/rec.csv'); d <- d[d$year<=2025,]
cat('missing:\n'); print(colSums(is.na(d[,c('tps','catch','adot','yac','td','fd','drop','brk','sep','cush','yacoe')])))
V <- c('tps','catch','adot','yac','td','drop','brk','sep','cush','yacoe')
for(pos in c('WR','TE')){ X <- d[d$pos==pos, V]; X <- X[complete.cases(X),]
  cat('\n=====', pos, 'n =', nrow(X), '\n scree:', round(eigen(cor(X))$values[1:6],2), '\n')
  pa <- fa.parallel(X, fa='fa', plot=FALSE); cat(' parallel', pa$nfact, ' MAP', which.min(VSS(X,6,plot=FALSE)$map), '\n')
  for(k in 2:4){ f <- fa(X, k, rotate='oblimin', fm='ml'); cat('--',k,'RMSEA',round(f$RMSEA[1],3),'TLI',round(f$TLI,2),'\n'); L<-unclass(f$loadings); L[abs(L)<.3]<-NA; print(round(L,2),na.print='.'); print(round(f$Phi,2)) } }
