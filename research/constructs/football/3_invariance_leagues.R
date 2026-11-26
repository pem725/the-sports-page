suppressMessages({library(lavaan)})
d0 <- read.csv('data/teams.csv')
for(v in c('rtd','ptd','int','sack','fum')) d0[[v]] <- d0[[v]]*100
for(v in c('comp','runshare','fdpp')) d0[[v]] <- d0[[v]]*10
M <- 'pass =~ ypa + comp + ptd + int + sack
      run  =~ ypc + rtd
      ptd ~~ rtd
      comp ~~ int'
FM <- c('cfi.robust','tli.robust','rmsea.robust','srmr')
for(lg in c('CFB','NFL')){ f<-cfa(M,data=d0[d0$lg==lg,],estimator='MLR'); cat(lg, round(fitMeasures(f,FM),3),'\n')}
inv <- function(d,label){
  cat('\n####',label,'\n')
  f0<-cfa(M,d,group='lg',estimator='MLR'); f1<-cfa(M,d,group='lg',estimator='MLR',group.equal='loadings')
  f2<-cfa(M,d,group='lg',estimator='MLR',group.equal=c('loadings','intercepts'))
  for(nm in c('f0','f1','f2')) cat(nm,round(fitMeasures(get(nm),FM),3),'\n')
  print(lavTestLRT(f0,f1,f2))
  for(fx in list(list(f1,'metric'),list(f2,'scalar'))){
   st<-lavTestScore(fx[[1]])$uni; pt<-parTable(fx[[1]])
   st$par<-sapply(st$lhs,function(p){i<-which(pt$plabel==p);paste(pt$lhs[i],pt$op[i],pt$rhs[i])})
   cat(fx[[2]],'- constraints that hurt most:\n'); print(head(st[order(-st$X2),c('par','X2')],5),row.names=FALSE)}
  f0
}
f0a <- inv(d0,'A: college definition of a carry in both leagues')
d2<-d0; d2$ypc[d2$lg=='NFL']<-d2$ypc_nfl[d2$lg=='NFL']
f0b <- inv(d2,'B: each league its own definition')
cat('\nStandardized loadings, configural, run A:\n')
s<-standardizedSolution(f0a); s<-s[s$op=='=~',]; print(reshape(s[,c('lhs','rhs','group','est.std')],idvar=c('lhs','rhs'),timevar='group',direction='wide'),row.names=FALSE,digits=2)
