data {
  int<lower=1> N;
  int<lower=1> W;
  array[N] int<lower=1, upper=W> week;
  vector[N] popularity_10;  // (CBS percentage - 50) / 10
  array[N] int<lower=0, upper=1> correct;

  int<lower=1> S;
  matrix[N, S] weight;

  // Editable priors. beta is a log-odds change per 10 percentage points.
  real alpha_prior_mean;
  real<lower=0> alpha_prior_sd;
  real beta_prior_mean;
  real<lower=0> beta_prior_sd;
  real<lower=0> week_sd_prior;
}

parameters {
  real alpha;
  real beta_popularity;
  real<lower=0> sigma_week;
  vector[W] z_week;
}

transformed parameters {
  vector[W] alpha_week = sigma_week * z_week;
  vector[N] eta;
  vector[N] p_correct;
  for (i in 1:N) {
    eta[i] = alpha + alpha_week[week[i]] +
             beta_popularity * popularity_10[i];
  }
  p_correct = inv_logit(eta);
}

model {
  alpha ~ normal(alpha_prior_mean, alpha_prior_sd);
  beta_popularity ~ normal(beta_prior_mean, beta_prior_sd);
  sigma_week ~ normal(0, week_sd_prior);
  z_week ~ std_normal();
  correct ~ bernoulli_logit(eta);
}

generated quantities {
  vector[N] log_lik;
  vector[S] expected_score = rep_vector(0, S);
  vector[S] replicated_score = rep_vector(0, S);
  real probability_at_25 = inv_logit(alpha - 2.5 * beta_popularity);
  real probability_at_50 = inv_logit(alpha);
  real probability_at_75 = inv_logit(alpha + 2.5 * beta_popularity);
  real probability_slope_25_to_75 = probability_at_75 - probability_at_25;
  array[N] int y_rep;

  for (i in 1:N) {
    log_lik[i] = bernoulli_logit_lpmf(correct[i] | eta[i]);
    y_rep[i] = bernoulli_rng(p_correct[i]);
    for (s in 1:S) {
      expected_score[s] += weight[i, s] * p_correct[i];
      replicated_score[s] += weight[i, s] * y_rep[i];
    }
  }
}
