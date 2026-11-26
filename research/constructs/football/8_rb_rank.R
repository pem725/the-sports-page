# Two rushing constructs, confirmed on split halves, then scored and ranked.
suppressMessages(library(lavaan))
o <- readRDS('data/rb_nfl_X.rds'); X <- o$X; n <- o$n
V <- c('ryoe','r10','r20','fd','rtd'); mu <- colMeans(X[,V]); sdv <- apply(X[,V],2,sd)
Z <- as.data.frame(scale(X[,V], mu, sdv))
M <- 'breakaway =~ ryoe + r10 + r20
      chains    =~ fd + rtd'
set.seed(11); ids <- unique(n$gsis); A <- n$gsis %in% sample(ids, length(ids)/2)
FM <- c('cfi.robust','rmsea.robust','srmr')
for(h in c('A','B')){ f <- cfa(M, Z[if(h=='A') A else !A,], estimator='MLR', std.lv=TRUE)
  cat('half', h, 'n=', nobs(f), round(fitMeasures(f,FM),3), '\n') }
f <- cfa(M, Z, estimator='MLR', std.lv=TRUE); cat('all n=', nobs(f), round(fitMeasures(f,FM),3), '\n')
s <- standardizedSolution(f); print(s[s$op=='=~',c('lhs','rhs','est.std','ci.lower','ci.upper')], digits=2, row.names=FALSE)
cat('construct correlation', round(lavInspect(f,'cor.lv')[1,2],2), '\n')
fs <- as.data.frame(lavPredict(f)); n$breakaway <- fs$breakaway; n$chains <- fs$chains; n$ypc <- X$ypc
# Is it the player? Same back, consecutive seasons.
nn <- n[order(n$gsis,n$year),]; nx <- merge(nn, transform(nn, year=year-1), by=c('gsis','year'), suffixes=c('','.next'))
cat('\nyear-to-year (same back, n=', nrow(nx), '): breakaway', round(cor(nx$breakaway,nx$breakaway.next),2),
    ' chains', round(cor(nx$chains,nx$chains.next),2), ' ypc', round(cor(nx$ypc,nx$ypc.next),2),
    ' ryoe', round(cor(nx$ryoe,nx$ryoe.next),2), ' rushing yds', round(cor(nx$yds,nx$yds.next),2), '\n')
# Score any season (2025 full; 2026 to date) on the 2016-2025 scale
score <- function(yr, mincar){
  d <- read.csv('data/rb_nfl.csv'); d <- d[d$year==yr & d$car>=mincar & !is.na(d$ryoe),]
  Xn <- data.frame(ryoe=d$ryoe, r10=d$r10/d$car, r20=d$r20/d$car, fd=d$fd/d$car, rtd=d$rtd/d$car)
  p <- as.data.frame(lavPredict(f, newdata=as.data.frame(scale(Xn, mu, sdv))))
  r <- data.frame(name=d$name, team=d$team, car=d$car, ypc=round(d$yds/d$car,1), yds=d$yds,
                  breakaway=round(p$breakaway,1), chains=round(p$chains,1))
  r$rush_score <- round((r$breakaway + r$chains)/2, 1)
  r[order(-r$rush_score),]
}
r25 <- score(2025, 100); r26 <- score(2026, 60)
write.csv(r25, 'data/rb_rank_2025.csv', row.names=FALSE); write.csv(r26, 'data/rb_rank_2026.csv', row.names=FALSE)
cat('\n2025 (100+ carries), top 12 and bottom 4, of', nrow(r25), '\n'); print(head(r25,12), row.names=FALSE); print(tail(r25,4), row.names=FALSE)
cat('\n2026 to date (60+ carries), top 12 of', nrow(r26), '\n'); print(head(r26,12), row.names=FALSE); print(tail(r26,4), row.names=FALSE)
cat('\nrank agreement 2025: rush_score vs ypc', round(cor(r25$rush_score, r25$ypc, method='spearman'),2),
    ' vs rushing yards', round(cor(r25$rush_score, r25$yds, method='spearman'),2), '\n')
saveRDS(list(f=f, mu=mu, sdv=sdv), 'data/rb_model.rds')
