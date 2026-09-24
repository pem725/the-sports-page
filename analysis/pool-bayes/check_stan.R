#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(rstan))
files <- sort(list.files(file.path("analysis", "pool-bayes", "stan"),
                         pattern = "[.]stan$", full.names = TRUE))
failed <- character()
for (f in files) {
  parsed <- tryCatch(rstan::stanc(file = f), error = identity)
  ok <- !inherits(parsed, "error") && isTRUE(parsed$status)
  cat(sprintf("%-48s %s\n", basename(f), if (ok) "OK" else "FAIL"))
  if (!ok) {
    failed <- c(failed, f)
    if (inherits(parsed, "error")) message(conditionMessage(parsed))
  }
}
if (length(failed)) quit(status = 1)
