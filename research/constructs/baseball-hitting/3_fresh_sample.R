suppressMessages(library(lavaan))
V <- c('single','double','triple','hr','ubb','ibb','hbp','so','sbatt','gidp','sac','sf','pitches','goao')
z <- function(d){ for(v in V) d[[v]] <- as.numeric(scale(d[[v]])); d }
p <- read.csv('data/players.csv'); B <- z(p[p$half=='B',])
o <- read.csv('data/old.csv'); C <- z(o[!(o$pid %in% p$pid),])
m5b <- '
 patience =~ ubb + pitches
 contact  =~ single + so
 speed    =~ sbatt + triple + gidp + sac
 power    =~ hr + ibb + sac + so
 launch   =~ 1*goao
 goao ~~ 0.29*goao'
m4 <- '
 patience =~ ubb + pitches
 contact  =~ single + so
 speed    =~ sbatt + triple + gidp + sac
 power    =~ hr + ibb + sac + so'
for(d in c('B','C')) for(nm in c('m4','m5b')){
  f <- cfa(get(nm), data=get(d), estimator='MLR', std.lv=TRUE)
  fm <- fitMeasures(f, c('cfi.robust','tli.robust','rmsea.robust','srmr'))
  cat(d, nm, 'n=',nobs(f), paste(names(fm), round(fm,3), collapse='  '), '\n')
}
f <- cfa(m5b, data=C, estimator='MLR', std.lv=TRUE)
s <- standardizedSolution(f); print(s[s$op %in% c('=~','~~') & s$lhs!=s$rhs, c('lhs','op','rhs','est.std','ci.lower','ci.upper')], digits=2)
# what do runs and RBI measure? regress on factor scores (sample C)
fs <- as.data.frame(lavPredict(f)); C2 <- cbind(C, fs)
for(y in c('runs','rbi')){ m <- lm(scale(C2[[y]]) ~ patience+contact+speed+power+launch, data=C2); cat('\n',y,' R2=',round(summary(m)$r.squared,2),'\n'); print(round(coef(m)[-1],2)) }
