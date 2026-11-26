# Today's QBs: dropback-weighted construct over 2024-2026 (to date), shrunk by Spearman-Brown.
d <- read.csv('data/qb_scored.csv'); d$construct <- (d$accuracy + d$chains)/2
h <- d[d$year<=2025,]; nx <- merge(h, transform(h, year=year-1), by=c('gsis','year'))
rho <- cor(nx$construct.x, nx$construct.y); avgdb <- mean(h$db); sdc <- sd(h$construct)
cat('season reliability of construct', round(rho,2), ' pairs', nrow(nx), ' avg dropbacks', round(avgdb), '\n')
t <- d[d$year>=2024,]
P <- do.call(rbind, lapply(split(t, t$gsis), function(z) data.frame(gsis=z$gsis[1], name=z$name[1], last=max(z$year), db=sum(z$db),
   raw=sum(z$construct*z$db)/sum(z$db), acc=sum(z$accuracy*z$db)/sum(z$db), chains=sum(z$chains*z$db)/sum(z$db), anya=sum(z$anya*z$db)/sum(z$db))))
P <- P[P$last==2026,]
k <- P$db/avgdb; P$rel <- k*rho/(1+(k-1)*rho); P$score <- P$rel*P$raw
P$se <- sqrt(rho*sdc^2*(1-P$rel)); P$lo <- P$score-1.96*P$se; P$hi <- P$score+1.96*P$se
o <- P[order(-P$score), c('name','db','anya','acc','chains','rel','score','lo','hi')]; o[,3:9] <- round(o[,3:9],2)
print(o, row.names=FALSE); write.csv(o, 'data/qb_today.csv', row.names=FALSE)
cat('distinguishable from average:', sum(o$lo>0), 'above,', sum(o$hi<0), 'below, of', nrow(o), '\n')
