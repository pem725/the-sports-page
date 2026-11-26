# Today's WRs: target-weighted construct over 2024-2026 (to date), shrunk by Spearman-Brown.
d <- read.csv('data/rec_scored.csv'); h <- d[d$year<=2025,]
nx <- merge(h, transform(h, year=year-1), by=c('gsis','year')); rho <- cor(nx$construct.x, nx$construct.y)
avg <- mean(h$tgt); sdc <- sd(h$construct); cat('season reliability', round(rho,2), ' avg targets', round(avg), '\n')
t <- d[d$year>=2024,]
P <- do.call(rbind, lapply(split(t, t$gsis), function(z) data.frame(name=z$name[1], last=max(z$year), tgt=sum(z$tgt), yds=sum(z$yds),
  raw=sum(z$construct*z$tgt)/sum(z$tgt), yps=sum(z$yds)/sum(z$snaps))))
P <- P[P$last==2026,]; k <- P$tgt/avg; P$rel <- k*rho/(1+(k-1)*rho); P$score <- P$rel*P$raw
P$se <- sqrt(rho*sdc^2*(1-P$rel)); P$lo <- P$score-1.96*P$se; P$hi <- P$score+1.96*P$se
o <- P[order(-P$score), c('name','tgt','yds','yps','rel','score','lo','hi')]; o[,4:8] <- round(o[,4:8],2)
print(head(o,15), row.names=FALSE); print(tail(o,5), row.names=FALSE); write.csv(o, 'data/rec_today.csv', row.names=FALSE)
cat('distinguishable from average:', sum(o$lo>0), 'above,', sum(o$hi<0), 'below, of', nrow(o), '\n')
