suppressMessages(library(lavaan)); m <- readRDS('data/rec_model.rds')
d <- read.csv('data/rec.csv'); d <- d[d$pos=='WR',]; V <- names(m$mu); d <- d[complete.cases(d[,V]),]
p <- as.data.frame(lavPredict(m$f, newdata=as.data.frame(scale(d[,V], m$mu, m$sdv)))); d <- cbind(d, p)
h <- d[d$year<=2025,]
# validity weights: which constructs carry yards per offensive snap? (criterion, composite, kept out of
# the model). Yards per TARGET was tried first and gives depth nearly all the weight, because yards per
# target rises with depth by arithmetic; yards per snap also rewards earning targets and catching them.
print(round(coef(summary(lm(scale(ypt) ~ after + open + hands + deep, h))),2))
g <- lm(scale(yps) ~ after + open + hands + deep, h); print(round(coef(summary(g)),2)); cat('R2', round(summary(g)$r.squared,2), '\n')
w <- coef(g)[-1]; d$construct <- as.numeric(as.matrix(d[,c('after','open','hands','deep')]) %*% w); h <- d[d$year<=2025,]
nx <- merge(h, transform(h, year=year-1), by=c('gsis','year'), suffixes=c('','.n')); cat('pairs', nrow(nx), '\n')
set.seed(8); out <- NULL
for(v in c('tps','catch','drop','adot','yac','yacoe','brk','sep','cush','td','fd','after','open','hands','deep','construct','ypt','yps','epa_t','yds')){
  r <- cor(nx[[v]], nx[[paste0(v,'.n')]], use='complete.obs'); b <- replicate(2000,{i<-sample(nrow(nx),replace=TRUE); cor(nx[[v]][i], nx[[paste0(v,'.n')]][i], use='complete.obs')})
  out <- rbind(out, data.frame(v=v, r=round(r,2), lo=round(quantile(b,.025),2), hi=round(quantile(b,.975),2))) }
print(out, row.names=FALSE); write.csv(out, 'data/rec_reliability.csv', row.names=FALSE)
write.csv(nx[,c('name','year','catch','catch.n','sep','sep.n','yacoe','yacoe.n','construct','construct.n','ypt','ypt.n','drop','drop.n')], 'data/rec_pairs.csv', row.names=FALSE)
# judges: AP All-Pro WRs 2018-2025
ap <- read.csv('data/allpro.csv'); ap <- ap[ap$pos=='WR',]
nrm <- function(x) gsub("[^a-z]", "", tolower(iconv(x, to='ASCII//TRANSLIT')))
h$allpro <- paste(h$year, nrm(h$name)) %in% paste(ap$year, nrm(ap$name)); cat('All-Pro WR found', sum(h$allpro), 'of', nrow(ap), '\n')
auc <- function(s,y){ r<-rank(s); n1<-sum(y); n0<-sum(!y); (sum(r[y])-n1*(n1+1)/2)/(n1*n0) }
au <- NULL; for(v in c('yds','tgt','tps','ypt','yps','epa_t','after','open','hands','deep','construct')){
  a <- auc(h[[v]], h$allpro); b <- replicate(2000,{i<-sample(nrow(h),replace=TRUE); auc(h[[v]][i], h$allpro[i])})
  au <- rbind(au, data.frame(v=v, auc=round(a,2), lo=round(quantile(b,.025,na.rm=TRUE),2), hi=round(quantile(b,.975,na.rm=TRUE),2))) }
print(au, row.names=FALSE); write.csv(au, 'data/rec_auc.csv', row.names=FALSE)
g0 <- glm(allpro ~ scale(yds), binomial, h); g1 <- update(g0, . ~ . + scale(construct)); cat('construct beyond yards: LR p =', signif(anova(g0,g1,test='Chisq')[2,5],2), '\n')
write.csv(d, 'data/rec_scored.csv', row.names=FALSE); saveRDS(w, 'data/rec_weights.rds')
