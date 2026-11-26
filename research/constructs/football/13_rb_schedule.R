# Is college ypc mis-measured because it ignores who the defenses were?
c <- read.csv('data/rb_cfb.csv'); d <- read.csv('data/rb_link.csv'); d <- d[d$cfb_car>=200 & d$nfl_car>=200,]
P5 <- c('SEC','Big Ten','Big 12','ACC','Pac-12','FBS Independents')
c$p5 <- c$conf %in% P5
# each college season relative to backs in the same conference and year (a crude schedule adjustment)
cm <- aggregate(cbind(yds,car) ~ conf + year, c, sum); cm$conf_ypc <- cm$yds/cm$car
c <- merge(c, cm[,c('conf','year','conf_ypc')], by=c('conf','year'))
c$rel <- c$yds/c$car - c$conf_ypc
# pool per player: carries-weighted
key <- function(x) tapply(x*c$car, c$pid, sum)/tapply(c$car, c$pid, sum)
pp <- data.frame(pid=names(key(c$rel)), rel=as.numeric(key(c$rel)), p5=as.numeric(key(c$p5)))
# link d (espn id or name fallback) -> pid via name+college ypc match
d$pid <- NA
for(i in seq_len(nrow(d))){ m <- unique(c$pid[c$name==d$name[i]]); if(length(m)==1) d$pid[i] <- m; if(d$espn[i] %in% c$pid) d$pid[i] <- d$espn[i] }
d <- merge(d, pp, by='pid'); cat('linked with conference info:', nrow(d), '\n')
cat('raw college ypc -> NFL ypc: r =', round(cor(d$cfb_ypc,d$nfl_ypc),2), '\n')
cat('conference-relative college ypc -> NFL ypc: r =', round(cor(d$rel,d$nfl_ypc),2), '\n')
cat('share of college carries in Power conferences, mean:', round(mean(d$p5),2), '\n')
print(round(coef(summary(lm(nfl_ypc ~ cfb_ypc + p5, d))),2))
set.seed(2); b <- replicate(4000, { i <- sample(nrow(d), replace=TRUE); cor(d$rel[i], d$nfl_ypc[i]) }); cat('95% interval:', round(quantile(b,c(.025,.975)),2), '\n')
o <- d[order(-d$cfb_ypc), c('name','college','cfb_ypc','rel','p5','nfl_ypc')]; o[,3:6] <- round(o[,3:6],1); print(head(o,8), row.names=FALSE)
# figures: see 17_figures.py (house-style SVG)
