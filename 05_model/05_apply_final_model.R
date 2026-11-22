#!/usr/bin/env Rscript
# 05_apply_final_model.R -- apply the locked model and reproduce Table 3.
#
# This is the R reference implementation for the locked .cbm model.  It is
# expected to agree with quickstart/run_demo.py; the Python path is the
# dependency-free reviewer entry point.

suppressPackageStartupMessages({
  library(catboost)
  library(pROC)
})

source(file.path(
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) REPO_ROOT else ".",
  "R", "utils.R"
))

model_path <- file.path(MODEL_DIR, "catboost_model.cbm")
if (!file.exists(model_path)) stop("Missing locked model: ", model_path, call. = FALSE)
model <- catboost.load_model(model_path)

df <- read_cohort()
splits <- split_cohort(df)

predicted <- lapply(SPLITS, function(s) {
  part <- splits[[s]]
  p <- predict_locked(model, part)
  data.frame(
    sample_id = part$sample_id,
    split = s,
    PAS_Macrophages = part$PAS_Macrophages,
    MUM1 = part$MUM1,
    Group = part$Group,
    predicted_probability = p,
    stringsAsFactors = FALSE
  )
})
predicted_df <- do.call(rbind, predicted)
write_csv(predicted_df, "predictions_locked_model.csv")

# Training-derived Youden threshold, applied unchanged to all splits.
youden <- youden_threshold(splits$train$Group, predicted[[1]]$predicted_probability)

table3 <- do.call(rbind, lapply(seq_along(SPLITS), function(i) {
  s <- SPLITS[[i]]
  y <- predicted[[i]]$Group
  p <- predicted[[i]]$predicted_probability
  ci <- auc_with_ci(y, p)
  m <- metrics_at(y, p, 0.5)
  data.frame(
    cohort = s,
    n = m[["n"]],
    events = m[["events"]],
    auc = ci[["auc"]],
    ci_lower = ci[["lower"]],
    ci_upper = ci[["upper"]],
    threshold = 0.5,
    sensitivity = m[["sensitivity"]],
    specificity = m[["specificity"]],
    accuracy = m[["accuracy"]],
    ppv = m[["ppv"]],
    npv = m[["npv"]],
    f1 = m[["f1"]],
    youden = m[["youden"]],
    ci_method = "DeLong",
    stringsAsFactors = FALSE
  )
}))
write_csv(table3, "Table3_locked_model_R.csv")

threshold_table <- do.call(rbind, lapply(seq_along(SPLITS), function(i) {
  s <- SPLITS[[i]]
  y <- predicted[[i]]$Group
  p <- predicted[[i]]$predicted_probability
  for (method in c("Youden_training", "fixed_0.5")) {
    t <- if (method == "Youden_training") youden else 0.5
    m <- metrics_at(y, p, t)
    data.frame(
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
}))
write_csv(threshold_table, "TableS3_thresholds_R.csv")

# Compare with the Python demo if it has already been run.
demo_path <- file.path(RESULTS_DIR, "predictions_demo.csv")
if (file.exists(demo_path)) {
  demo <- read.csv(demo_path, stringsAsFactors = FALSE)
  merged <- merge(
    predicted_df[, c("sample_id", "predicted_probability")],
    demo[, c("sample_id", "predicted_probability")],
    by = "sample_id", suffixes = c("_R", "_python")
  )
  parity <- data.frame(
    n_compared = nrow(merged),
    max_abs_difference = max(abs(merged$predicted_probability_R - merged$predicted_probability_python)),
    tolerance = 1e-6,
    pass = max(abs(merged$predicted_probability_R - merged$predicted_probability_python)) <= 1e-6
  )
  write_csv(parity, "model_parity_R_vs_python.csv")
  cat(sprintf("R vs Python parity: max |diff| = %.3g (n=%d)\n",
              parity$max_abs_difference, parity$n_compared))
}

cat("\nTable 3 (locked model, R/CatBoost; synthetic demo):\n")
print(table3, row.names = FALSE)
cat(sprintf("\nTraining-derived Youden threshold: %.4f\n", youden))
