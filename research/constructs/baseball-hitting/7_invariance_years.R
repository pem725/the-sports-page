# Does the four-construct hitting model hold across eras, 1988-2025?
# Multi-group CFA by era: configural -> metric -> scalar, then which intercepts drift.
# Per-season groups (38 of ~270 hitters) ran away on the two-indicator patience factor,
# so seasons are grouped into eras of ~1,300 player-seasons. 2020 (60 games) is dropped.
# Caveat: one hitter appears in several seasons, so rows are not independent.
suppressMessages(library(lavaan))
d <- read.csv('data/calibrated.csv')
d <- d[d$year>=1988 & d$year<=2025 & d$year!=2020,]
V <- c('single','triple','hr','ubb','ibb','so','sbatt','gidp','sac','pitches')
for(v in setdiff(V,'pitches')) d[[v]] <- sqrt(d[[v]])*10
d$pitches <- d$pitches*4          # put it on the same variance scale as the rest
d <- d[complete.cases(d[,V]),]
d$era <- cut(d$year, c(1987,1994,2005,2014,2019,2025),
             labels=c('1988-94','1995-2005','2006-14','2015-19','2021-25'))
print(table(d$era))
m4 <- '
 patience =~ ubb + pitches
 contact  =~ single + so
 speed    =~ sbatt + triple + gidp + sac
 power    =~ hr + ibb + sac + so'
FM <- c('cfi.robust','tli.robust','rmsea.robust','srmr')
for(e in levels(d$era)){ f<-cfa(m4,d[d$era==e,],estimator='MLR', bounds='pos.var'); cat(e, round(fitMeasures(f,FM),3),
  if(any(diag(lavInspect(f,'est')$theta)<0)) 'NEG-VAR' else '', '\n') }
f0 <- cfa(m4, d, group='era', estimator='MLR', bounds='pos.var')
f1 <- cfa(m4, d, group='era', estimator='MLR', bounds='pos.var', group.equal='loadings')
f2 <- cfa(m4, d, group='era', estimator='MLR', bounds='pos.var', group.equal=c('loadings','intercepts'))
cat('\n'); for(nm in c('f0','f1','f2')) cat(nm, round(fitMeasures(get(nm),FM),3), '\n')
for(fx in list(list(f1,'metric'),list(f2,'scalar'))){
  st <- lavTestScore(fx[[1]], epc=FALSE)$uni; pt <- parTable(fx[[1]])
  st$par <- sapply(st$lhs, function(p){ i<-which(pt$plabel==p); paste(pt$lhs[i],pt$op[i],pt$rhs[i]) })
  a <- aggregate(X2 ~ par, st, sum); cat('\n', fx[[2]], ': summed score test by parameter\n'); print(head(a[order(-a$X2),],8), row.names=FALSE)
}
# (fits not saved: about 5 minutes to rerun)
