# Do QB constructs agree with human judges? AP All-Pro QBs 2018-2025 (Wikipedia, one source).
d <- read.csv('data/qb_scored.csv'); d <- d[d$year<=2025,]
ap <- read.csv('data/allpro.csv'); ap <- ap[ap$pos=='QB',]
nrm <- function(x) gsub("[^a-z]", "", tolower(iconv(x, to='ASCII//TRANSLIT')))
d$allpro <- paste(d$year, nrm(d$name)) %in% paste(ap$year, nrm(ap$name))
cat('QB-seasons', nrow(d), ' All-Pro found', sum(d$allpro), 'of', nrow(ap), '\n')
d$tds <- d$td*d$att; d$construct <- (d$accuracy + d$chains)/2
auc <- function(s,y){ r<-rank(s); n1<-sum(y); n0<-sum(!y); (sum(r[y])-n1*(n1+1)/2)/(n1*n0) }
set.seed(6); out <- NULL
for(v in c('yds','tds','db','ypa','anya','epa_db','accuracy','chains','holds','construct','int')){
  a <- auc(d[[v]], d$allpro); b <- replicate(2000,{i<-sample(nrow(d),replace=TRUE); auc(d[[v]][i], d$allpro[i])})
  out <- rbind(out, data.frame(v=v, auc=round(a,2), lo=round(quantile(b,.025,na.rm=TRUE),2), hi=round(quantile(b,.975,na.rm=TRUE),2))) }
print(out, row.names=FALSE); write.csv(out, 'data/qb_auc.csv', row.names=FALSE)
g0 <- glm(allpro ~ scale(yds), binomial, d); g1 <- update(g0, . ~ . + scale(construct))
cat('construct beyond passing yards: LR p =', signif(anova(g0,g1,test='Chisq')[2,5],2), '\n')
d$rk_c <- ave(-d$construct, d$year, FUN=rank); d$rk_y <- ave(-d$yds, d$year, FUN=rank); d$n <- ave(d$yds, d$year, FUN=length)
print(d[d$allpro, c('year','name','rk_y','rk_c','n')], row.names=FALSE)
