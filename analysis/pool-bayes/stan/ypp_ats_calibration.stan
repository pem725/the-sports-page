data {
  int<lower=1> N;
  array[N] int<lower=0, upper=1> ypp_side_covered;
  vector[N] abs_ypp_market_disagreement;
  real alpha_prior_mean;
  real<lower=0> alpha_prior_sd;
  real beta_prior_mean;
  real<lower=0> beta_prior_sd;
}

parameters {
  real alpha;
  real beta_disagreement;
}

transformed parameters {
  vector[N] eta = alpha + beta_disagreement * abs_ypp_market_disagreement;
}

model {
  alpha ~ normal(alpha_prior_mean, alpha_prior_sd);
  beta_disagreement ~ normal(beta_prior_mean, beta_prior_sd);
  ypp_side_covered ~ bernoulli_logit(eta);
}

generated quantities {
  real cover_probability_at_zero = inv_logit(alpha);
  real probability_above_coinflip = inv_logit(alpha) > 0.5;
  real probability_above_breakeven = inv_logit(alpha) > 0.524;
  vector[N] log_lik;
  array[N] int cover_rep;
  for (i in 1:N) {
    log_lik[i] = bernoulli_logit_lpmf(ypp_side_covered[i] | eta[i]);
    cover_rep[i] = bernoulli_logit_rng(eta[i]);
  }
}
