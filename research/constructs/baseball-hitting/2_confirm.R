suppressMessages(library(lavaan))
p <- read.csv('data/players.csv'); B <- p[p$half=='B',]; A <- p[p$half=='A',]
z <- function(d){ for(v in c('single','double','triple','hr','ubb','ibb','hbp','so','sbatt','gidp','sac','sf','pitches','goao')) d[[v]] <- as.numeric(scale(d[[v]])); d }
B <- z(B); A <- z(A)
m5 <- '
 patience =~ ubb + pitches
 contact  =~ single + so
 speed    =~ sbatt + triple + gidp + sac
 power    =~ hr + ibb + sac
 launch   =~ goao + sf'
m1 <- ' hitting =~ ubb + pitches + single + so + sbatt + triple + gidp + sac + hr + ibb + goao + sf'
m3 <- '
 eye   =~ ubb + pitches + so + hr + ibb
 speed =~ sbatt + triple + gidp + sac
 bip   =~ single + goao + sf'
for(nm in c('m1','m3','m5')){
  f <- cfa(get(nm), data=B, estimator='MLR', std.lv=TRUE)
  fm <- fitMeasures(f, c('cfi.robust','tli.robust','rmsea.robust','srmr','bic'))
  cat(nm, 'n=',nobs(f), paste(names(fm), round(fm,3), collapse='  '), '\n')
}
f <- cfa(m5, data=B, estimator='MLR', std.lv=TRUE)
s <- standardizedSolution(f); print(s[s$op %in% c('=~','~~') & s$lhs!=s$rhs, c('lhs','op','rhs','est.std','ci.lower','ci.upper')], digits=2)
mi <- modindices(f); print(head(mi[order(-mi$mi), c('lhs','op','rhs','mi')], 6))
