suppressMessages({library(psych);library(GPArotation)})
V <- c('single','double','triple','hr','ubb','ibb','hbp','so','sbatt','gidp','sac','sf','pitches','goao')
s <- read.csv('data/seasons.csv')
# test-retest: same player, consecutive seasons
a <- merge(s, transform(s, year=year-1), by=c('pid','year'), suffixes=c('.t','.t1'))
rt <- sapply(c(V,'runs','rbi'), function(v) cor(a[[paste0(v,'.t')]], a[[paste0(v,'.t1')]]))
cat('pairs', nrow(a), '\n'); print(round(sort(rt,decreasing=TRUE),2))
p <- read.csv('data/players.csv'); A <- p[p$half=='A',V]; B <- p[p$half=='B',V]
set.seed(1)
pa <- fa.parallel(A, fm='ml', fa='fa', plot=FALSE, n.iter=200)
cat('parallel analysis suggests', pa$nfact, 'factors\n')
vs <- VSS(A, n=6, fm='ml', plot=FALSE); cat('MAP min at', which.min(vs$map), '\n')
for(k in 3:5){ f <- fa(A, nfactors=k, fm='ml', rotate='oblimin')
  cat('\n==== k =',k,' RMSEA',round(f$RMSEA[1],3),' TLI',round(f$TLI,3),' BIC',round(f$BIC,1),'\n')
  print(f$loadings, cutoff=.3, sort=TRUE); if(k>1) print(round(f$Phi,2)) }
