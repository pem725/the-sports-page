suppressMessages({library(psych);library(GPArotation)})
d <- read.csv('data/teams.csv')
V <- c('ypc','rtd','ypa','comp','ptd','int','sack','fdpp','fum','runshare')
for(lg in c('CFB','NFL')){ x <- d[d$lg==lg,V]
  cat('\n==',lg,' n=',nrow(x),'\n'); pa <- fa.parallel(x,fa='fa',plot=FALSE); cat('parallel says',pa$nfact,' MAP:',which.min(VSS(x,8,plot=FALSE)$map),'\n')}
L <- list()
for(lg in c('CFB','NFL')){ f <- fa(d[d$lg==lg,V],3,rotate='oblimin',fm='ml'); L[[lg]] <- f$loadings; cat('\n',lg,'\n'); print(round(unclass(f$loadings),2)); print(round(f$Phi,2))}
cat('\nTucker congruence CFB vs NFL (3 factors):\n'); print(round(factor.congruence(L$CFB,L$NFL),2))
