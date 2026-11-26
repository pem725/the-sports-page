# Reliability, MVP validation, and pooled 2023-25 ranking for hitters.
suppressMessages(library(lavaan))
h <- read.csv('data/hitters.csv'); m <- readRDS('data/hit_model.rds'); v <- read.csv('data/votes.csv')
Z <- as.data.frame(scale(h[,m$V], m$mu, m$sdv)); fs <- as.data.frame(lavPredict(m$f, newdata=Z)); h <- cbind(h, fs)
# a single "offense" construct score for ranking: power + lift + (-miss) + (-eager) + speed, equally weighted.
# Stated as a convenience, not a finding (omega_h .47 says there is no strong general factor).
h$construct <- (h$power + 0.5*h$lift - h$miss - h$eager + 0.5*h$speed)/4
write.csv(h, 'data/hitters_scored.csv', row.names=FALSE)
# same player, next season
nx <- merge(h, transform(h, year=year-1), by=c('pid','year')); nx <- nx[nx$year != 2019 & nx$year != 2020,]  # skip pairs touching 2020
cat('pairs', nrow(nx), '\n')
for(k in c('so','ubb','hr','single','sbatt','ev','chase','whiff','sprint','la','eager','miss','power','lift','speed','construct','avg','obp','ops','hr_n','rbi_n'))
  cat(sprintf('%-9s r = %.2f\n', k, cor(nx[[paste0(k,'.x')]], nx[[paste0(k,'.y')]])))
write.csv(nx[,c('name.x','year','so.x','so.y','avg.x','avg.y','construct.x','construct.y','ev.x','ev.y','ops.x','ops.y')], 'data/hit_pairs.csv', row.names=FALSE)
# MVP: did the player get any votes / top-5? AUC of volume, rate, and construct
norm <- function(x) tolower(gsub('[^A-Za-z]','', iconv(sub(' Jr\\.?$','',x), to='ASCII//TRANSLIT')))
vm <- v[v$award=='mvp',]; vm$key <- paste(vm$year, norm(vm$name)); h$key <- paste(h$year, norm(h$name))
h$mvp_share <- vm$share[match(h$key, vm$key)]; h$mvp_share[is.na(h$mvp_share)] <- 0
cat('MVP candidates matched:', sum(h$mvp_share>0), 'of', nrow(vm), '\n')
h$top5 <- h$key %in% vm$key[ave(-vm$points, vm$year, vm$league, FUN=rank) <= 5]
auc <- function(s, y){ r <- rank(s); n1 <- sum(y); n0 <- sum(!y); (sum(r[y]) - n1*(n1+1)/2)/(n1*n0) }
set.seed(5)
for(k in c('hr_n','rbi_n','runs_n','hits_n','pa','avg','obp','ops','power','construct')){
  a <- auc(h[[k]], h$top5); b <- replicate(1000, { i <- sample(nrow(h), replace=TRUE); auc(h[[k]][i], h$top5[i]) })
  cat(sprintf('top-5 MVP: %-10s AUC %.2f [%.2f, %.2f]   rank-corr with vote share %.2f\n', k, a, quantile(b,.025), quantile(b,.975),
      cor(h[[k]], h$mvp_share, method='spearman'))) }
g0 <- glm(top5 ~ scale(ops) + scale(pa), binomial, h); g1 <- update(g0, . ~ . + scale(construct))
cat('construct adds to OPS + PA? p =', signif(anova(g0,g1,test='Chisq')[2,5],2), '\n')
# pooled 2023-25, shrunk
rho <- cor(nx$construct.x, nx$construct.y); avgpa <- mean(h$pa); sdc <- sd(h$construct)
t <- h[h$year>=2023,]; agg <- aggregate(cbind(pa, construct_w=construct*pa) ~ pid, t, sum)
agg$raw <- agg$construct_w/agg$pa; k <- agg$pa/avgpa; agg$rel <- k*rho/(1+(k-1)*rho)
agg$score <- agg$rel*agg$raw; tv <- rho*sdc^2; agg$se <- sqrt(tv*(1-agg$rel)); agg$lo <- agg$score-1.96*agg$se; agg$hi <- agg$score+1.96*agg$se
last <- t[order(t$year),]; last <- last[!duplicated(last$pid, fromLast=TRUE),c('pid','name','year')]; agg <- merge(agg, last); agg <- agg[agg$year==2025,]
agg <- agg[order(-agg$score), c('name','pa','raw','rel','score','lo','hi')]; agg[,3:7] <- round(agg[,3:7],2)
write.csv(agg, 'data/hit_rank_2025.csv', row.names=FALSE)
cat('\nseason reliability of construct:', round(rho,2), '\n2025 hitters ranked (pooled 2023-25):', nrow(agg), ' above average (interval > 0):', sum(agg$lo>0), ' below:', sum(agg$hi<0), '\n')
print(head(agg,12), row.names=FALSE); print(tail(agg,4), row.names=FALSE)
