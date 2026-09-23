#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(jsonlite)
  library(rstan)
})

rstan_options(auto_write = TRUE)
options(mc.cores = max(1L, parallel::detectCores(logical = FALSE)))

args <- commandArgs(trailingOnly = TRUE)
repo <- normalizePath(if (length(args)) args[[1]] else ".", mustWork = TRUE)
root <- file.path(repo, "analysis", "pool-bayes")
stan_dir <- file.path(root, "stan")
result_dir <- file.path(root, "results")
dir.create(result_dir, recursive = TRUE, showWarnings = FALSE)

seed <- 20260923L
chains <- 4L
iter <- 3000L
warmup <- 1000L

raw <- fromJSON(file.path(repo, "data", "pool-crowd-backtest.json"),
                simplifyVector = FALSE)
picks <- do.call(rbind, lapply(raw$weeks, function(w) {
  do.call(rbind, lapply(w$picks, function(p) {
    data.frame(week = w$week, side = p$side, actual = p$weight,
               public = p$public, correct = as.integer(p$correct),
               stringsAsFactors = FALSE)
  }))
}))

strategy_weights <- function(d) {
  d$nonfavorite_first <- NA_integer_
  d$least_popular_first <- NA_integer_
  for (wk in unique(d$week)) {
    ix <- which(d$week == wk)
    a <- ix[order(d$public[ix] >= 50, -d$actual[ix])]
    d$nonfavorite_first[a] <- 15:1
    b <- ix[order(d$public[ix], d$side[ix])]
    d$least_popular_first[b] <- 15:1
  }
  d
}
picks <- strategy_weights(picks)

observed <- c(
  actual = sum(picks$actual * picks$correct),
  nonfavorite_first = sum(picks$nonfavorite_first * picks$correct),
  least_popular_first = sum(picks$least_popular_first * picks$correct)
)
stopifnot(all(unname(observed) == c(202, 213, 219)))
stopifnot(sum(picks$correct) == 28L)

nf <- picks$public < 50
group_data <- list(
  y_nonfavorite = sum(picks$correct[nf]),
  n_nonfavorite = sum(nf),
  y_favorite = sum(picks$correct[!nf]),
  n_favorite = sum(!nf),
  prior_alpha_nonfavorite = 1,
  prior_beta_nonfavorite = 1,
  prior_alpha_favorite = 1,
  prior_beta_favorite = 1,
  future_n_nonfavorite = 40L,
  future_n_favorite = 40L
)

sampling_args <- list(chains = chains, iter = iter, warmup = warmup,
                      seed = seed, refresh = 0,
                      control = list(adapt_delta = 0.95))

group_model <- stan_model(file.path(stan_dir, "crowd_group_beta_binomial.stan"))
group_fit <- do.call(sampling, c(list(object = group_model, data = group_data),
                                 sampling_args))

score_data <- list(
  N = nrow(picks), W = length(unique(picks$week)), week = picks$week,
  popularity_10 = (picks$public - 50) / 10,
  correct = picks$correct, S = 3L,
  weight = as.matrix(picks[c("actual", "nonfavorite_first",
                             "least_popular_first")]),
  alpha_prior_mean = 0, alpha_prior_sd = 1,
  beta_prior_mean = 0, beta_prior_sd = 0.5,
  week_sd_prior = 0.5
)
score_model <- stan_model(file.path(stan_dir, "crowd_popularity_score.stan"))
score_fit <- do.call(sampling, c(list(object = score_model, data = score_data),
                                 sampling_args))

summ <- function(fit, pars) {
  x <- summary(fit, pars = pars, probs = c(.025, .25, .5, .75, .975))$summary
  data.frame(parameter = rownames(x), x, row.names = NULL, check.names = FALSE)
}

group_summary <- summ(group_fit, c("theta_nonfavorite", "theta_favorite",
                                  "risk_difference", "risk_ratio", "odds_ratio",
                                  "nonfavorite_better", "future_rate_difference"))
score_summary <- summ(score_fit, c("alpha", "beta_popularity", "sigma_week",
                                  "probability_at_25", "probability_at_50",
                                  "probability_at_75",
                                  "probability_slope_25_to_75",
                                  "expected_score", "replicated_score"))
write.csv(group_summary, file.path(result_dir, "group_model_summary.csv"),
          row.names = FALSE)
write.csv(score_summary, file.path(result_dir, "popularity_score_summary.csv"),
          row.names = FALSE)

group_draws <- rstan::extract(group_fit, pars = c("theta_nonfavorite",
                                                 "theta_favorite",
                                                 "risk_difference",
                                                 "nonfavorite_better"))
score_draws <- rstan::extract(score_fit, pars = c("beta_popularity",
                                                 "expected_score",
                                                 "replicated_score"))

diagnostics <- function(fit, label) {
  s <- summary(fit)$summary
  sampler <- get_sampler_params(fit, inc_warmup = FALSE)
  data.frame(
    model = label,
    max_rhat = max(s[, "Rhat"], na.rm = TRUE),
    min_bulk_ess = min(s[, "n_eff"], na.rm = TRUE),
    divergences = sum(vapply(sampler, function(x) sum(x[, "divergent__"]), 0)),
    max_treedepth_hits = sum(vapply(sampler,
      function(x) sum(x[, "treedepth__"] >= 10), 0))
  )
}
diag <- rbind(diagnostics(group_fit, "group_beta_binomial"),
              diagnostics(score_fit, "hierarchical_popularity_score"))
write.csv(diag, file.path(result_dir, "diagnostics.csv"), row.names = FALSE)

qtxt <- function(x, digits = 3) {
  q <- quantile(x, c(.025, .5, .975))
  sprintf(paste0("%.", digits, "f [%.", digits, "f, %.", digits, "f]"),
          q[[2]], q[[1]], q[[3]])
}
pct <- function(x) sprintf("%.1f%%", 100 * mean(x))

expected <- score_draws$expected_score
replicated <- score_draws$replicated_score
report <- c(
  "# Bayesian audit results",
  "",
  sprintf("Generated %s with seed %d; %d chains, %d post-warmup draws per chain.",
          format(Sys.time(), "%Y-%m-%d %H:%M %Z"), seed, chains, iter - warmup),
  "",
  "## Bottom line",
  "",
  sprintf("The observed sample is 7/12 correct on crowd non-favorites and 21/33 on crowd favorites. Under independent Beta(1,1) priors, the posterior probability that the non-favorite rate is higher is **%s**.", pct(group_draws$nonfavorite_better)),
  sprintf("The posterior risk difference (non-favorite minus favorite) is **%s**.", qtxt(group_draws$risk_difference)),
  sprintf("In the continuous model, the log-odds slope per 10 percentage points of CBS support is **%s**.", qtxt(score_draws$beta_popularity)),
  "",
  "These results do not confirm a durable contrarian accuracy edge. They quantify substantial uncertainty around a small, post-hoc, three-week sample.",
  "",
  "## Score implications under the fitted popularity model",
  "",
  sprintf("Posterior expected score, actual weights: **%s**.", qtxt(expected[, 1], 1)),
  sprintf("Posterior expected score, non-favorites first: **%s**.", qtxt(expected[, 2], 1)),
  sprintf("Posterior expected score, least popular first: **%s**.", qtxt(expected[, 3], 1)),
  sprintf("P(expected non-favorites-first score > actual order): **%s**.", pct(expected[, 2] > expected[, 1])),
  sprintf("P(expected least-popular-first score > actual order): **%s**.", pct(expected[, 3] > expected[, 1])),
  sprintf("Posterior predictive P(non-favorites-first realized score > actual order): **%s**.", pct(replicated[, 2] > replicated[, 1])),
  sprintf("Posterior predictive P(least-popular-first realized score > actual order): **%s**.", pct(replicated[, 3] > replicated[, 1])),
  "",
  "The expected-score comparisons are in-sample and exploratory. The replicated-score comparisons use the same simulated game outcomes for all three rankings, preserving the paired design.",
  "",
  "## Sampling diagnostics",
  "",
  paste(capture.output(print(diag, row.names = FALSE)), collapse = "\n"),
  "",
  "See `CLAIM-AUDIT.md` for the deterministic checks and the claims that cannot be identified from the stored data."
)
writeLines(report, file.path(result_dir, "POSTERIOR-REPORT.md"))

saveRDS(group_fit, file.path(result_dir, "group_fit.rds"))
saveRDS(score_fit, file.path(result_dir, "popularity_score_fit.rds"))
cat(paste(report, collapse = "\n"), "\n")
