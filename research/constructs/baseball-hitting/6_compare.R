# Does calibrating help? Raw rates against history percentiles and within-season normal
# scores, on (1) year-to-year stability, (2) the four-factor model inside one era, and
# (3) the same model on a sample spanning 1988-2025, where the era should matter.
suppressMessages(library(lavaan))
V <- c('single','double','triple','hr','ubb','ibb','hbp','so','sbatt','gidp','sac','sf','pitches','goao')
cal <- read.csv('data/calibrated.csv'); cal <- cal[cal$year >= 1988, ]
cal$pid <- as.character(cal$pid)

# (1) stability: same player, consecutive seasons, no pairs across the short 2020 season
s <- cal[cal$year != 2020 & cal$year != 2019, ]
a <- merge(s, transform(s, year = year - 1), by = c('pid','year'), suffixes = c('.t','.n'))
r <- function(v) cor(a[[paste0(v,'.t')]], a[[paste0(v,'.n')]], use = 'pair')
rt <- t(sapply(c(V,'runs','rbi'), function(v) c(raw = r(v), history = r(paste0(v,'_hp')), season = r(paste0(v,'_sz')))))
cat('Year-to-year stability,', nrow(a), 'pairs\n'); print(round(rt[order(-rt[,1]), ], 2))

m4 <- '
 patience =~ ubb + pitches
 contact  =~ single + so
 speed    =~ sbatt + triple + gidp + sac
 power    =~ hr + ibb + sac + so'
fit <- function(d, label){ f <- suppressWarnings(cfa(m4, data = as.data.frame(scale(d[, V])), estimator = 'MLR', std.lv = TRUE))
  fm <- fitMeasures(f, c('cfi.robust','rmsea.robust','srmr'))
  cat(sprintf('%-22s n=%4d  CFI %.3f  RMSEA %.3f  SRMR %.3f\n', label, nobs(f), fm[1], fm[2], fm[3])) }
pick <- function(suf, rows){ d <- rows[, c('pid', paste0(V, suf))]; names(d) <- c('pid', V)
  aggregate(. ~ pid, data = d, FUN = mean) }

# (2) inside one era: the same samples B and C as 2_confirm.R and 3_fresh_sample.R
p <- read.csv('data/players.csv'); p$pid <- as.character(p$pid)
inB <- cal$pid %in% p$pid[p$half == 'B'] & cal$year %in% 2021:2025 & cal$pa >= 300
inC <- !(cal$pid %in% p$pid) & cal$year %in% 2016:2019 & cal$pa >= 300
cat('\nInside one era\n')
for (suf in c('', '_hp', '_sz')) { lab <- c('raw' = '', 'history pct' = '_hp', 'season calibrated' = '_sz'); n <- names(lab)[lab == suf]
  fit(pick(suf, cal[inB, ]), paste('B', n)); fit(pick(suf, cal[inC, ]), paste('C', n)) }

# (3) across eras: one random season per player, 1988-2025
e <- cal[cal$year != 2020 & complete.cases(cal[, V]), ]
set.seed(7); e <- e[sample(nrow(e)), ]; e <- e[!duplicated(e$pid), ]
cat('\nAcross eras, 1988-2025\n')
fit(pick('', e), 'raw'); fit(pick('_sz', e), 'season calibrated')
cat('\nShare of each stat explained by the year alone (raw):\n')
print(round(sort(sapply(V, function(v) summary(lm(e[[v]] ~ factor(e$year)))$r.squared), decreasing = TRUE), 2))
