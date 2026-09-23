data {
  int<lower=0> y_nonfavorite;
  int<lower=y_nonfavorite> n_nonfavorite;
  int<lower=0> y_favorite;
  int<lower=y_favorite> n_favorite;

  // Prior parameters are data so a critic can change assumptions without
  // editing or recompiling the model.
  real<lower=0> prior_alpha_nonfavorite;
  real<lower=0> prior_beta_nonfavorite;
  real<lower=0> prior_alpha_favorite;
  real<lower=0> prior_beta_favorite;
  int<lower=1> future_n_nonfavorite;
  int<lower=1> future_n_favorite;
}

parameters {
  real<lower=0, upper=1> theta_nonfavorite;
  real<lower=0, upper=1> theta_favorite;
}

model {
  theta_nonfavorite ~ beta(prior_alpha_nonfavorite,
                           prior_beta_nonfavorite);
  theta_favorite ~ beta(prior_alpha_favorite, prior_beta_favorite);
  y_nonfavorite ~ binomial(n_nonfavorite, theta_nonfavorite);
  y_favorite ~ binomial(n_favorite, theta_favorite);
}

generated quantities {
  real risk_difference = theta_nonfavorite - theta_favorite;
  real risk_ratio = theta_nonfavorite / theta_favorite;
  real odds_ratio = (theta_nonfavorite / (1 - theta_nonfavorite)) /
                    (theta_favorite / (1 - theta_favorite));
  int nonfavorite_better = theta_nonfavorite > theta_favorite;
  int future_y_nonfavorite = binomial_rng(future_n_nonfavorite,
                                           theta_nonfavorite);
  int future_y_favorite = binomial_rng(future_n_favorite, theta_favorite);
  real future_rate_difference =
      future_y_nonfavorite / (1.0 * future_n_nonfavorite) -
      future_y_favorite / (1.0 * future_n_favorite);
}
