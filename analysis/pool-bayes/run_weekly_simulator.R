#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(rstan))
rstan_options(auto_write = TRUE)
options(mc.cores = max(1L, parallel::detectCores(logical = FALSE)))

args <- commandArgs(trailingOnly = TRUE)
repo <- normalizePath(if (length(args)) args[[1]] else ".", mustWork = TRUE)
root <- file.path(repo, "analysis", "pool-bayes")

G <- 15L
weights <- matrix(0, G, 3,
                  dimnames = list(NULL, c("contrarian_heavy", "random",
                                          "consensus_heavy")))
weights[1:8, 1] <- 15:8
weights[9:15, 1] <- 7:1
weights[, 2] <- 1:15  # replaced inside Stan on every draw
weights[1:8, 3] <- 1:8
weights[9:15, 3] <- 9:15

stan_data <- list(
  G = G, K = 9L, S = 3L,
  user_pick = c(rep(0L, 8), rep(1L, 7)),
  true_probability_side_one = rep(0.5, G),
  opponent_probability_side_one = rep(0.75, G),
  fixed_user_weight = weights,
  randomize_user_weight = c(0L, 1L, 0L),
  tie_policy = 0L
)

model <- stan_model(file.path(root, "stan",
                              "weekly_competition_documented.stan"))
fit <- sampling(model, data = stan_data, algorithm = "Fixed_param",
                chains = 4, iter = 30000, warmup = 0,
                seed = 20260923, refresh = 0)
draws <- rstan::extract(fit, pars = c("user_score", "win_credit",
                                     "margin_over_best"))
result <- data.frame(
  strategy = colnames(weights),
  mean_score = colMeans(draws$user_score),
  win_probability = colMeans(draws$win_credit),
  mean_margin_over_best = colMeans(draws$margin_over_best)
)
write.csv(result, file.path(root, "results", "weekly_simulation.csv"),
          row.names = FALSE)
print(result, row.names = FALSE, digits = 4)
