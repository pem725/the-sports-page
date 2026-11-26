# Second feed for the box-score repeat rates in What Repeats Parts 1 and 3: the Lahman database
# (R package Lahman 14.0.0, through 2025), same rules as 1_build.py. Stints are summed per
# player-season (the MLB API file can split a traded player by team, so small differences are expected).
suppressMessages(library(Lahman))
fz <- function(x, y){ ok <- is.finite(x) & is.finite(y); r <- cor(x[ok], y[ok]); n <- sum(ok); s <- 1/sqrt(n-3)
  c(r=r, lo=tanh(atanh(r)-1.96*s), hi=tanh(atanh(r)+1.96*s), n=n) }
pairs <- function(d, vars){ d$key <- paste(d$playerID, d$yearID); nx <- d; nx$yearID <- nx$yearID - 1
  m <- merge(d, nx, by=c('playerID','yearID')); m <- m[!(m$yearID %in% c(2019, 2020)),]
  t(sapply(vars, function(v) fz(m[[paste0(v,'.x')]], m[[paste0(v,'.y')]]))) }
B <- aggregate(cbind(AB,R,H,X2B,X3B,HR,RBI,BB,SO,IBB,HBP,SH,SF) ~ playerID + yearID, Batting[Batting$yearID %in% 2015:2025,], sum)
B$PA <- with(B, AB+BB+HBP+SH+SF); sc <- ifelse(B$yearID==2020, 60/162, 1); B <- B[B$PA >= 300*sc,]
r <- function(x) sqrt(x/B$PA); s1 <- with(B, H-X2B-X3B-HR)
B$single <- r(s1); B$double <- r(B$X2B); B$triple <- r(B$X3B); B$hr <- r(B$HR); B$so <- r(B$SO); B$ubb <- r(B$BB-B$IBB)
B$avg <- B$H/B$AB; B$obp <- with(B,(H+BB+HBP)/(AB+BB+HBP+SF)); B$slg <- with(B,(s1+2*X2B+3*X3B+4*HR)/AB); B$ops <- B$obp+B$slg
B$runs_n <- B$R; B$rbi_n <- B$RBI
cat('hitter-seasons', nrow(B), '\n'); print(round(pairs(B, c('so','ubb','single','hr','double','triple','avg','obp','slg','ops','runs_n','rbi_n')),2))
P <- aggregate(cbind(G,GS,IPouts,H,HR,BB,SO,IBB,HBP,BFP,ER) ~ playerID + yearID, Pitching[Pitching$yearID %in% 2015:2025,], sum)
P$ip <- P$IPouts/3; sc <- ifelse(P$yearID==2020, 60/162, 1)
P$role <- ifelse(P$GS >= P$G/2 & P$ip >= 100*sc, 'SP', ifelse(P$GS <= 2 & P$ip >= 40*sc, 'RP', NA)); P <- P[!is.na(P$role),]
rp <- function(x) sqrt(x/P$BFP); P$so <- rp(P$SO); P$ubb <- rp(P$BB-P$IBB); P$hr <- rp(P$HR)
P$hbip <- with(P, (H-HR)/pmax(BFP-SO-BB-HBP-HR,1)); P$era <- 9*P$ER/P$ip
for(ro in c('SP','RP')){ d <- P[P$role==ro,]; cat('\n', ro, 'seasons', nrow(d), '\n'); print(round(pairs(d, c('so','ubb','hr','hbip','era')),2)) }
