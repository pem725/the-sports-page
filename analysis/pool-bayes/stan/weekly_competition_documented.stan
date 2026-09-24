data {
  int<lower=1> G;
  int<lower=1> K;
  int<lower=1> S;
  array[G] int<lower=0, upper=1> user_pick;
  vector<lower=0, upper=1>[G] true_probability_side_one;
  vector<lower=0, upper=1>[G] opponent_probability_side_one;
  matrix<lower=0>[G, S] fixed_user_weight;
  array[S] int<lower=0, upper=1> randomize_user_weight;
  int<lower=0, upper=2> tie_policy; // 0=loss, 1=split, 2=full win
}

model {
}

generated quantities {
  vector[S] user_score = rep_vector(0, S);
  vector[K] opponent_score = rep_vector(0, K);
  vector[S] win_credit = rep_vector(0, S);
  vector[S] margin_over_best = rep_vector(0, S);

  {
    array[G] int outcome;
    matrix[G, K] opponent_pick;
    matrix[G, S] user_weight = fixed_user_weight;
    matrix[G, K] opponent_weight;

    // A fresh random confidence permutation for every opponent and every draw.
    for (k in 1:K) {
      vector[G] u;
      array[G] int order;
      for (g in 1:G) u[g] = uniform_rng(0, 1);
      order = sort_indices_asc(u);
      for (rank in 1:G) opponent_weight[order[rank], k] = rank;
    }

    // This makes the middle comparison a genuinely random user ordering.
    for (s in 1:S) {
      if (randomize_user_weight[s] == 1) {
        vector[G] u;
        array[G] int order;
        for (g in 1:G) u[g] = uniform_rng(0, 1);
        order = sort_indices_asc(u);
        for (rank in 1:G) user_weight[order[rank], s] = rank;
      }
    }

    for (g in 1:G) {
      outcome[g] = bernoulli_rng(true_probability_side_one[g]);
      for (k in 1:K) {
        opponent_pick[g, k] = bernoulli_rng(opponent_probability_side_one[g]);
        if (opponent_pick[g, k] == outcome[g]) {
          opponent_score[k] += opponent_weight[g, k];
        }
      }
      for (s in 1:S) {
        if (user_pick[g] == outcome[g]) user_score[s] += user_weight[g, s];
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
    if (strictly_beaten == 0) {
      if (tied_for_first == 1 || tie_policy == 2) win_credit[s] = 1;
      else if (tie_policy == 1) win_credit[s] = 1.0 / tied_for_first;
    }
  }
}
