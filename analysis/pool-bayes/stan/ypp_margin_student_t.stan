data {
  int<lower=1> N;
  vector[N] final_margin_home_minus_away;
  vector[N] prior_ypp_margin_home_minus_away;
  vector[N] home_field_indicator;
  real alpha_prior_mean;
  real<lower=0> alpha_prior_sd;
  real beta_ypp_prior_mean;
  real<lower=0> beta_ypp_prior_sd;
  real home_prior_mean;
  real<lower=0> home_prior_sd;
  real<lower=0> residual_scale_prior;
  real<lower=0> nu_rate;
}

parameters {
  real alpha;
  real beta_ypp;
  real home_field;
  real<lower=0> sigma;
  real<lower=2> nu;
}

transformed parameters {
  vector[N] mu = alpha +
                 beta_ypp * prior_ypp_margin_home_minus_away +
                 home_field * home_field_indicator;
}

model {
  alpha ~ normal(alpha_prior_mean, alpha_prior_sd);
  beta_ypp ~ normal(beta_ypp_prior_mean, beta_ypp_prior_sd);
  home_field ~ normal(home_prior_mean, home_prior_sd);
  sigma ~ normal(0, residual_scale_prior);
  nu - 2 ~ exponential(nu_rate);
  final_margin_home_minus_away ~ student_t(nu, mu, sigma);
}

generated quantities {
  vector[N] log_lik;
  vector[N] margin_rep;
  vector[N] residual;
  for (i in 1:N) {
    log_lik[i] = student_t_lpdf(final_margin_home_minus_away[i] |
                                nu, mu[i], sigma);
    margin_rep[i] = student_t_rng(nu, mu[i], sigma);
    residual[i] = final_margin_home_minus_away[i] - mu[i];
  }
}
