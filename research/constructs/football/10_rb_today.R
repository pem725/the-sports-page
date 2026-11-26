# Today's backs: pool 2024-2026 (to date), score, then shrink each toward average by how
# reliable his pooled score is (Spearman-Brown on the season-to-season correlation).
suppressMessages(library(lavaan))
m <- readRDS('data/rb_model.rds')
d <- read.csv('data/rb_nfl.csv'); d <- d[!is.na(d$ryoe),]
X <- function(z) data.frame(ryoe=z$ryoe, r10=z$r10/z$car, r20=z$r20/z$car, fd=z$fd/z$car, rtd=z$rtd/z$car)
sc <- function(z){ p <- as.data.frame(lavPredict(m$f, newdata=as.data.frame(scale(X(z), m$mu, m$sdv)))); (p$breakaway+p$chains)/2 }
# season-to-season reliability of the rate score, 2018-2025 seasons with 100+ carries
h <- d[d$year>=2018 & d$year<=2025 & d$car>=100,]; h$rate <- sc(h)
hx <- merge(h, transform(h, year=year-1), by=c('gsis','year')); rho <- cor(hx$rate.x, hx$rate.y)
avgcar <- mean(h$car); sdrate <- sd(h$rate)
cat('season reliability of rate:', round(rho,2), ' (n pairs', nrow(hx), ')  average carries', round(avgcar), '\n')
# pool 2024-2026: carry-weighted indicators
t <- d[d$year>=2024,]
w <- function(v) tapply(v*t$car, t$gsis, sum)/tapply(t$car, t$gsis, sum)
P <- data.frame(gsis=names(tapply(t$car,t$gsis,sum)), car=as.numeric(tapply(t$car,t$gsis,sum)))
P$ryoe <- as.numeric(w(t$ryoe)); P$r10 <- as.numeric(tapply(t$r10,t$gsis,sum)); P$r20 <- as.numeric(tapply(t$r20,t$gsis,sum))
P$fd <- as.numeric(tapply(t$fd,t$gsis,sum)); P$rtd <- as.numeric(tapply(t$rtd,t$gsis,sum)); P$yds <- as.numeric(tapply(t$yds,t$gsis,sum))
last <- t[order(t$year),]; last <- last[!duplicated(last$gsis, fromLast=TRUE),]
P <- merge(P, last[,c('gsis','name','team','year')], by='gsis')
P <- P[P$year==2026,]                     # active this season
P$raw <- sc(P); k <- P$car/avgcar; P$rel <- k*rho/(1+(k-1)*rho)
P$score <- P$rel*P$raw; tv <- rho*sdrate^2; P$se <- sqrt(tv*(1-P$rel))
P$lo <- P$score-1.96*P$se; P$hi <- P$score+1.96*P$se
P$ypc <- P$yds/P$car
o <- P[order(-P$score), c('name','team','car','ypc','raw','rel','score','lo','hi')]
o[,4:9] <- round(o[,4:9],2); cat('\nactive 2026 backs, pooled 2024-26 (', nrow(o), ')\n'); print(o, row.names=FALSE)
write.csv(o, 'data/rb_today.csv', row.names=FALSE)
cat('\nhow many backs can be told apart from average (interval excludes 0):', sum(o$lo>0), 'above,', sum(o$hi<0), 'below\n')
