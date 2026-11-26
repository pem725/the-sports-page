# Do the constructs agree with human judges? AP All-Pro running backs 2016-2025 (Wikipedia; one source).
suppressMessages(library(lavaan))
m <- readRDS('data/rb_model.rds'); ap <- read.csv('data/allpro_rb.csv')
d <- read.csv('data/rb_nfl.csv'); d <- d[d$year>=2016 & d$year<=2025 & d$car>=100 & !is.na(d$ryoe),]
Xn <- data.frame(ryoe=d$ryoe, r10=d$r10/d$car, r20=d$r20/d$car, fd=d$fd/d$car, rtd=d$rtd/d$car)
p <- as.data.frame(lavPredict(m$f, newdata=as.data.frame(scale(Xn, m$mu, m$sdv))))
d$breakaway <- p$breakaway; d$chains <- p$chains; d$rate <- (p$breakaway+p$chains)/2
d$ypc <- d$yds/d$car; d$scrim <- d$yds + d$recyds; d$tds <- d$rtd + d$rectd
d$allpro <- paste(d$year,d$name) %in% paste(ap$year,ap$name)
cat('All-Pro backs found in data:', sum(d$allpro), 'of', nrow(ap), '\n')
auc <- function(s, y){ r <- rank(s); n1 <- sum(y); n0 <- sum(!y); (sum(r[y]) - n1*(n1+1)/2)/(n1*n0) }
set.seed(5)
for(v in c('yds','scrim','tds','car','ypc','breakaway','chains','rate')){
  a <- auc(d[[v]], d$allpro)
  b <- replicate(2000, { i <- sample(nrow(d), replace=TRUE); auc(d[[v]][i], d$allpro[i]) })
  cat(sprintf('%-10s AUC %.2f [%.2f, %.2f]\n', v, a, quantile(b,.025), quantile(b,.975))) }
# volume x rate: does adding the construct to volume help?
g0 <- glm(allpro ~ scale(scrim), binomial, d); g1 <- glm(allpro ~ scale(scrim) + scale(rate), binomial, d)
print(round(coef(summary(g1)),2)); cat('LR test p =', signif(anova(g0,g1,test='Chisq')[2,5],2), '\n')
# where did each All-Pro rank in his season on volume and on rate?
d$rk_scrim <- ave(-d$scrim, d$year, FUN=rank); d$rk_rate <- ave(-d$rate, d$year, FUN=rank); d$nyr <- ave(d$scrim, d$year, FUN=length)
print(d[d$allpro, c('year','name','car','ypc','rk_scrim','rk_rate','nyr')], row.names=FALSE, digits=2)
