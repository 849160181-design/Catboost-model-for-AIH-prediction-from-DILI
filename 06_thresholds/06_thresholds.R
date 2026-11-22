#!/usr/bin/env Rscript
# 06_thresholds.R -- operating-point selection and sensitivity analysis.
#
# The locked model outputs a probability.  This script:
#   1. sweeps a threshold grid for each split;
#   2. selects the training-set Youden threshold;
#   3. applies that threshold unchanged to the held-out splits;
#   4. reports the fixed 0.50 threshold for comparison.
#
# Threshold selection on the training set only avoids optimistic use of the
# held-out cohorts.

suppressPackageStartupMessages({
  library(catboost)
  library(pROC)
})

source(file.path(
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) REPO_ROOT else ".",
  "R", "utils.R"
))

model <- catboost.load_model(file.path(MODEL_DIR, "catboost_model.cbm"))
df <- read_cohort()
splits <- split_cohort(df)
probs <- lapply(splits, function(part) predict_locked(model, part))

grid <- seq(0.05, 0.95, by = 0.01)
threshold_grid <- do.call(rbind, lapply(SPLITS, function(s) {
  y <- splits[[s]]$Group
  p <- probs[[s]]
  do.call(rbind, lapply(grid, function(t) {
    m <- metrics_at(y, p, t)
    data.frame(
      cohort = s,
      threshold = t,
      sensitivity = m[["sensitivity"]],
      specificity = m[["specificity"]],
      accuracy = m[["accuracy"]],
      youden = m[["youden"]],
      stringsAsFactors = FALSE
    )
  }))
}))
write_csv(threshold_grid, "threshold_grid.csv")

youden <- youden_threshold(splits$train$Group, probs$train)

selected <- do.call(rbind, lapply(SPLITS, function(s) {
  y <- splits[[s]]$Group
  p <- probs[[s]]
  rows <- list()
  for (method in c("Youden_training", "fixed_0.5", "fixed_0.63")) {
    t <- switch(method,
      "Youden_training" = youden,
      "fixed_0.5" = 0.50,
      "fixed_0.63" = 0.63
    )
    m <- metrics_at(y, p, t)
    rows[[length(rows) + 1]] <- data.frame(
      cohort = s,
      threshold_method = method,
      threshold = t,
      n = m[["n"]],
      events = m[["events"]],
      sensitivity = m[["sensitivity"]],
      specificity = m[["specificity"]],
      accuracy = m[["accuracy"]],
      ppv = m[["ppv"]],
      npv = m[["npv"]],
      f1 = m[["f1"]],
      youden = m[["youden"]],
      stringsAsFactors = FALSE
    )
  }
  do.call(rbind, rows)
}))
write_csv(selected, "TableS3_thresholds.csv")

# A compact recommended-operating-point table for the manuscript.
recommended <- selected[selected$threshold_method == "Youden_training", ]
recommended$note <- "Training-set Youden threshold applied unchanged to held-out data"
write_csv(recommended, "threshold_recommended.csv")

cat(sprintf("Training-derived Youden threshold: %.4f\n\n", youden))
print(selected[, c("cohort", "threshold_method", "threshold", "sensitivity", "specificity", "youden")],
      row.names = FALSE)
