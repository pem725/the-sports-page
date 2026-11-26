# The editor's challenge: are the RB correlations attenuated by short careers? Plot them first.
h <- read.csv('data/rb_hist.csv')
# --- career length: seasons with 100+ carries
h100 <- h[h$car>=100,]; nseas <- table(h100$gsis)
first <- tapply(h100$year, h100$gsis, min); done <- names(first)[first<=2015]   # careers that had time to finish
cat('backs with a 100-carry season (first one 1999-2015):', length(done), '\n')
print(round(prop.table(table(pmin(nseas[done],6))),2))
cat('median number of 100-carry seasons:', median(nseas[done]), '\n')
# --- a "1,000-yard" season, scaled to the schedule: 1,000 per 16 games (1,063 in 17)
h$big <- h$yds >= 1000*h$sched/16
b <- h[h$big,]; cat('\nbig seasons:', nrow(b), ' by', length(unique(b$gsis)), 'backs\n')
nx <- merge(h[,c('gsis','year','yds','car','big','games')], transform(h[,c('gsis','year','yds','car','big','games')], year=year-1), by=c('gsis','year'), all.x=TRUE, suffixes=c('','.n'))
bb <- nx[nx$big & nx$year<=2024,]; bb$big.n[is.na(bb$big.n)] <- FALSE
p <- mean(bb$big.n); se <- sqrt(p*(1-p)/nrow(bb))
cat('after a big season, big again next year:', round(p,2), '[', round(p-1.96*se,2), ',', round(p+1.96*se,2), '] n=', nrow(bb), '\n')
cat('  ...still a 100-carry back next year:', round(mean(!is.na(bb$car.n) & bb$car.n>=100),2), '\n')
# by count of prior big seasons: does a track record raise the odds?
bb <- bb[order(bb$gsis,bb$year),]; bb$k <- ave(bb$year, bb$gsis, FUN=seq_along)
print(aggregate(big.n ~ pmin(k,3), bb, function(x) c(p=round(mean(x),2), n=length(x))))
# by age
bb2 <- merge(bb, h[,c('gsis','year','age')], by=c('gsis','year')); bb2$ageb <- cut(bb2$age, c(0,24,26,28,40), labels=c('<=24','25-26','27-28','29+'))
print(aggregate(big.n ~ ageb, bb2, function(x) c(p=round(mean(x),2), n=length(x))))
# --- year-to-year ypc: everyone vs established backs (200+ carries both years), PLOTTED
nx$ypc <- nx$yds/nx$car; nx$ypc.n <- nx$yds.n/nx$car.n
A <- nx[!is.na(nx$car.n) & nx$car>=100 & nx$car.n>=100,]; E <- nx[!is.na(nx$car.n) & nx$car>=250 & nx$car.n>=250,]
cat('\nypc next year: 100+ both r=', round(cor(A$ypc,A$ypc.n),2), 'n=', nrow(A), ';  250+ both r=', round(cor(E$ypc,E$ypc.n),2), 'n=', nrow(E), '\n')
cat('rush yards per game next year (100+ both): r=', round(cor(A$yds/A$games, A$yds.n/A$games.n),2), '\n')
# reliability by volume: split-half style — Spearman-Brown says r rises with carries
for(lo in c(100,150,200,250,300)){ S <- A[A$car>=lo & A$car.n>=lo,]; cat(lo,'+ carries both years: r =', round(cor(S$ypc,S$ypc.n),2), ' n =', nrow(S), '\n') }
png('fig/ypc_next_year.png', 900, 450); par(mfrow=c(1,2), mar=c(4,4,2,1))
plot(A$ypc, A$ypc.n, pch=16, col=rgb(.17,.29,.43,.35), xlab='yards per carry, this season', ylab='next season', main=sprintf('100+ carries both seasons, r = %.2f', cor(A$ypc,A$ypc.n)), xlim=c(2.5,7), ylim=c(2.5,7)); abline(0,1,lty=3); abline(lm(ypc.n~ypc,A), col='#b83a1e', lwd=2)
plot(E$ypc, E$ypc.n, pch=16, col=rgb(.72,.23,.12,.5), xlab='yards per carry, this season', ylab='next season', main=sprintf('250+ carries both seasons, r = %.2f', cor(E$ypc,E$ypc.n)), xlim=c(2.5,7), ylim=c(2.5,7)); abline(0,1,lty=3); abline(lm(ypc.n~ypc,E), col='#2c4a6e', lwd=2)
dev.off()
# --- college -> NFL, plotted with names
d <- read.csv('data/rb_link.csv'); d <- d[d$cfb_car>=200 & d$nfl_car>=200,]
png('fig/college_to_nfl.png', 900, 600); par(mar=c(4,4,2,1))
plot(d$cfb_ypc, d$nfl_ypc, pch=16, col=rgb(.17,.29,.43,.5), cex=sqrt(d$nfl_car)/20, xlab='college yards per carry (2014+ seasons)', ylab='NFL yards per carry (career, through 2025)', main=sprintf('75 backs, r = %.2f  (dot size = NFL carries)', cor(d$cfb_ypc,d$nfl_ypc)))
abline(lm(nfl_ypc~cfb_ypc,d), col='#b83a1e', lwd=2); lab <- d$nfl_car>900 | d$cfb_ypc>7 | d$nfl_ypc>5 | d$nfl_ypc<3.8
text(d$cfb_ypc[lab], d$nfl_ypc[lab], d$name[lab], pos=4, cex=.75); dev.off()
cat('weighted by NFL carries r =', round(cov.wt(cbind(d$cfb_ypc,d$nfl_ypc), wt=d$nfl_car, cor=TRUE)$cor[1,2],2),
    '; 600+ NFL carries r =', round(with(d[d$nfl_car>=600,], cor(cfb_ypc,nfl_ypc)),2), ' n=', sum(d$nfl_car>=600), '\n')
