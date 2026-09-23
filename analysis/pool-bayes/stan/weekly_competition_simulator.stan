data {
  int<lower=1> G;
  int<lower=1> K;
  int<lower=1> S;
  array[G] int<lower=0, upper=1> user_pick;
  vector<lower=0, upper=1>[G] true_probability_side_one;
  vector<lower=0, upper=1>[G] opponent_probability_side_one;
  matrix<lower=0>[G, S] user_weight;
  matrix<lower=0>[G, K] opponent_weight;
}

// This is a fixed-parameter simulator: all substantive assumptions arrive in
// the data block, and each draw is created in generated quantities.
model {
}

generated quantities {
  array[G] int<lower=0, upper=1> outcome;
  matrix[G, K] opponent_pick;
  vector[S] user_score = rep_vector(0, S);
  vector[K] opponent_score = rep_vector(0, K);
  vector[S] win_credit = rep_vector(0, S);
  vector[S] margin_over_best = rep_vector(0, S);

  for (g in 1:G) {
    outcome[g] = bernoulli_rng(true_probability_side_one[g]);
    for (k in 1:K) {
      opponent_pick[g, k] = bernoulli_rng(opponent_probability_side_one[g]);
      if (opponent_pick[g, k] == outcome[g]) {
        opponent_score[k] += opponent_weight[g, k];
      }
    }
    for (s in 1:S) {
      if (user_pick[g] == outcome[g]) {
        user_score[s] += user_weight[g, s];
      }
    }
  }

  for (s in 1:S) {
    int tied_for_first = 1;
    int strictly_beaten = 0;
    real best_opponent = max(opponent_score);
    for (k in 1:K) {
      if (opponent_score[k] > user_score[s]) strictly_beaten = 1;
      if (opponent_score[k] == user_score[s]) tied_for_first += 1;
    }
    margin_over_best[s] = user_score[s] - best_opponent;
    if (strictly_beaten == 0) win_credit[s] = 1.0 / tied_for_first;
  }
}
