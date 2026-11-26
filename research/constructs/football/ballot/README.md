# Board ballot: running backs, 2026-11-26

**Purpose.** The construct model has to agree with what people who watch the games see, or it
will never persuade anyone (the editor, 2026-11-26). This ballot asks the board to rank 12 current
backs as runners, blind to the model, and measures the agreement.

**Pre-registration.** The model ranking was committed before the ballot went out: `data/rb_today.csv`
in commit 5f51e33, and the 12-back extract in `rb-2026-11-26-model.csv`. Nothing about the model
changes after votes arrive.

**The 12** span the model's range: its top four (Henry, Gibbs, Corum, Cook), five from the middle
(Robinson, Taylor, Walker, Williams, Barkley), and three from the bottom (Hall, McCaffrey, Jeanty).
They are listed alphabetically on the ballot.

**The question, as sent:** rank them 1–12 as *runners*, carrying the ball only (not catching),
on what you have seen in 2024–2026.

**Analysis, fixed in advance:**
1. Agreement within the board: Kendall's W.
2. Each judge against the model: Spearman's rho, with a permutation p-value (12 items, so expect
   wide intervals; rho ≈ .58 is needed for p < .05).
3. Board average against the model and against volume (rushing yards 2024–26). The All-Pro test
   predicts that the board will track volume more closely than rate.
4. The disagreements, by name: where the board and the model are 4+ places apart. Those are the story.

**Caveat:** the editor had seen the model's top two before ranking; his ballot is reported
separately as well as in the board average.
