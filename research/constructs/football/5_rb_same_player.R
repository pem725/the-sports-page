# The same running back in both leagues: does his yards per carry travel?
d <- read.csv('data/rb_link.csv'); c <- read.csv('data/rb_cfb.csv'); n <- read.csv('data/rb_nfl.csv')
d <- d[d$cfb_car>=200 & d$nfl_car>=200,]
cat('backs with 200+ carries in each league:', nrow(d), '\n')
set.seed(3); B <- 4000
bs <- function(f){ v <- replicate(B, f(d[sample(nrow(d),replace=TRUE),])); round(c(f(d), quantile(v,c(.025,.975))),2) }
cat('college ypc', bs(function(x) mean(x$cfb_ypc)), '\nNFL ypc', bs(function(x) mean(x$nfl_ypc)),
    '\ndrop (same back)', bs(function(x) mean(x$cfb_ypc - x$nfl_ypc)),
    '\ncorrelation college->NFL ypc', bs(function(x) cor(x$cfb_ypc, x$nfl_ypc)), '\n')
cat('share of backs whose NFL ypc is lower:', mean(d$nfl_ypc < d$cfb_ypc), '\n')
# league context: all college RB-seasons vs all NFL RB-seasons, 100+ carries, 2014-2025
cl <- with(c, sum(yds)/sum(car)); nl <- with(n[n$year<2026,], sum(yds)/sum(car))
cat('all college RBs (100+ car) ypc', round(cl,2), ' all NFL RBs', round(nl,2), '\n')
# where in the college distribution were they? percentile of each back's college ypc among college RB-seasons
cat('median percentile of the linked backs among college RB-seasons:', round(median(sapply(d$cfb_ypc, function(v) mean(c$yds/c$car < v)))*100), '\n')
# regression toward the mean: predicted NFL ypc from college ypc
m <- lm(nfl_ypc ~ cfb_ypc, d); print(round(coef(summary(m)),2))
o <- d[order(-d$cfb_ypc), c('name','college','cfb_car','cfb_ypc','nfl_car','nfl_ypc')]; o$cfb_ypc<-round(o$cfb_ypc,1); o$nfl_ypc<-round(o$nfl_ypc,1)
print(head(o,8), row.names=FALSE); print(tail(o,5), row.names=FALSE)
