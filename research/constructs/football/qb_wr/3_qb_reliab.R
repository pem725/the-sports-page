# Same QB, next season: which measures are the player? Exports pairs for the SVG plots.
suppressMessages(library(lavaan)); m <- readRDS('data/qb_model.rds')
d <- read.csv('data/qb.csv'); V <- names(m$mu)
# 2026 has no PFR throwaway counts yet; fill with the 2025 mean. Throwaways load only on 'holds',
# which is not used in the ranking (holds correlates about -.1 with accuracy and chains).
d$throwaway[d$year==2026 & is.na(d$throwaway)] <- mean(d$throwaway[d$year==2025], na.rm=TRUE)
ok <- complete.cases(d[,V]); d <- d[ok,]
p <- as.data.frame(lavPredict(m$f, newdata=as.data.frame(scale(d[,V], m$mu, m$sdv))))
d <- cbind(d, p)
h <- d[d$year<=2025,]
nx <- merge(h, transform(h, year=year-1), by=c('gsis','year'), suffixes=c('','.n'))
cat('pairs', nrow(nx), '\n')
set.seed(4); out <- NULL
for(v in c('comp','cpoe','bad','ttt','scr','throwaway','td','fd','sack','int','adot','aggr','yac','accuracy','holds','chains','ypa','anya','epa_db')){
  r <- cor(nx[[v]], nx[[paste0(v,'.n')]]); b <- replicate(2000,{i<-sample(nrow(nx),replace=TRUE); cor(nx[[v]][i], nx[[paste0(v,'.n')]][i])})
  out <- rbind(out, data.frame(v=v, r=round(r,2), lo=round(quantile(b,.025),2), hi=round(quantile(b,.975),2))) }
print(out, row.names=FALSE); write.csv(out, 'data/qb_reliability.csv', row.names=FALSE)
write.csv(nx[,c('name','year','accuracy','accuracy.n','chains','chains.n','int','int.n','epa_db','epa_db.n','scr','scr.n')], 'data/qb_pairs.csv', row.names=FALSE)
write.csv(d, 'data/qb_scored.csv', row.names=FALSE)
