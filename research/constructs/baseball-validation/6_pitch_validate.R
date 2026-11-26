# Confirm three pitching constructs on half B; reliability; Cy Young; pooled 2023-25 ranking of starters.
suppressMessages({library(lavaan); library(psych)})
p <- read.csv('data/pitchers.csv'); v <- read.csv('data/votes.csv')
V <- c('so','ubb','hr','wp','goao','velo','whiff','chase','gb','hbip','ev')
M <- '
 stuff     =~ so + whiff + velo + chase
 command   =~ ubb + wp + chase
 grounders =~ gb + goao + hr
 so ~~ whiff'
FM <- c('cfi.robust','tli.robust','rmsea.robust','srmr'); out <- list()
for(r in c('SP','RP')){
  A <- p$role==r & p$half=='A'; mu <- colMeans(p[A,V]); sdv <- apply(p[A,V],2,sd)
  Z <- as.data.frame(scale(p[p$role==r,V], mu, sdv)); hf <- p$half[p$role==r]
  fA <- cfa(M, Z[hf=='A',], estimator='MLR', std.lv=TRUE); fB <- cfa(M, Z[hf=='B',], estimator='MLR', std.lv=TRUE)
  cat('\n', r, 'half A', round(fitMeasures(fA,FM),3), ' half B', round(fitMeasures(fB,FM),3), '\n')
  s <- standardizedSolution(fB); print(s[s$op=='=~',c('lhs','rhs','est.std')], digits=2, row.names=FALSE); print(round(lavInspect(fB,'cor.lv'),2))
  om <- omega(Z[hf=='B', c('so','ubb','hr','wp','goao','velo','whiff','chase','gb')], nfactors=3, fm='ml', plot=FALSE)
  cat('omega total', round(om$omega.tot,2), ' omega_h', round(om$omega_h,2), '\n')
  f <- cfa(M, Z, estimator='MLR', std.lv=TRUE); fs <- as.data.frame(lavPredict(f))
  q <- cbind(p[p$role==r,], fs); q$construct <- (q$stuff - q$command + 0.5*q$grounders)/2.5   # command factor: high = more walks
  out[[r]] <- q }
q <- rbind(out$SP, out$RP); write.csv(q, 'data/pitchers_scored.csv', row.names=FALSE)
nx <- merge(q, transform(q, year=year-1), by=c('pid','year','role')); nx <- nx[nx$year!=2019 & nx$year!=2020,]
for(r in c('SP','RP')){ z <- nx[nx$role==r,]; cat('\n', r, 'same pitcher next season, pairs', nrow(z), '\n')
  for(k in c('so','ubb','hr','hbip','ev','gb','velo','whiff','chase','stuff','command','grounders','construct','era'))
    cat(sprintf('  %-9s r = %.2f\n', k, cor(z[[paste0(k,'.x')]], z[[paste0(k,'.y')]], use='complete'))) }
write.csv(nx[,c('name.x','role','year','era.x','era.y','hbip.x','hbip.y','so.x','so.y','construct.x','construct.y')], 'data/pitch_pairs.csv', row.names=FALSE)
# Cy Young (starters): top-5
norm <- function(x) tolower(gsub('[^A-Za-z]','', iconv(sub(' Jr\\.?$','',x), to='ASCII//TRANSLIT')))
vc <- v[v$award=='cy',]; vc$key <- paste(vc$year, norm(vc$name)); s <- out$SP; s$key <- paste(s$year, norm(s$name))
top5 <- vc$key[ave(-vc$points, vc$year, vc$league, FUN=rank) <= 5]; s$top5 <- s$key %in% top5
s$cy_share <- vc$share[match(s$key, vc$key)]; s$cy_share[is.na(s$cy_share)] <- 0
cat('\nCy Young top-5 matched among starters:', sum(s$top5), 'of', length(top5), '\n')
auc <- function(sc, y){ rr <- rank(sc); n1 <- sum(y); n0 <- sum(!y); (sum(rr[y]) - n1*(n1+1)/2)/(n1*n0) }
set.seed(6); s$ip_ <- s$ip; s$negera <- -s$era
for(k in c('ip_','so_n','w_n','negera','stuff','construct')){
  a <- auc(s[[k]], s$top5); b <- replicate(1000, { i <- sample(nrow(s), replace=TRUE); auc(s[[k]][i], s$top5[i]) })
  cat(sprintf('  %-9s AUC %.2f [%.2f, %.2f]  rank-corr with share %.2f\n', k, a, quantile(b,.025), quantile(b,.975), cor(s[[k]], s$cy_share, method='spearman'))) }
g0 <- glm(top5 ~ scale(era) + scale(ip), binomial, s); g1 <- update(g0, . ~ . + scale(construct)); cat('  construct adds to ERA + IP? p =', signif(anova(g0,g1,test='Chisq')[2,5],2), '\n')
# pooled 2023-25 starters, shrunk
z <- nx[nx$role=='SP',]; rho <- cor(z$construct.x, z$construct.y); sp <- out$SP; avgbf <- mean(sp$bf); sdc <- sd(sp$construct)
t <- sp[sp$year>=2023,]; agg <- aggregate(cbind(bf, cw=construct*bf) ~ pid, t, sum); agg$raw <- agg$cw/agg$bf
k <- agg$bf/avgbf; agg$rel <- k*rho/(1+(k-1)*rho); agg$score <- agg$rel*agg$raw; agg$se <- sqrt(rho*sdc^2*(1-agg$rel))
agg$lo <- agg$score-1.96*agg$se; agg$hi <- agg$score+1.96*agg$se
last <- t[order(t$year),]; last <- last[!duplicated(last$pid, fromLast=TRUE),c('pid','name','year')]; agg <- merge(agg,last); agg <- agg[agg$year==2025,]
agg <- agg[order(-agg$score), c('name','bf','raw','rel','score','lo','hi')]; agg[,3:7] <- round(agg[,3:7],2); write.csv(agg,'data/sp_rank_2025.csv',row.names=FALSE)
cat('\nSP construct reliability', round(rho,2), '; 2025 starters', nrow(agg), ' above avg:', sum(agg$lo>0), ' below:', sum(agg$hi<0), '\n'); print(head(agg,10), row.names=FALSE)
