#!/usr/bin/env Rscript
# 05_train_catboost.R -- retrain the CatBoost pipeline on the synthetic cohort.
#
# This is a *demonstration* of the training procedure, not the final model.
# The locked model supplied with the manuscript is model/catboost_model.cbm and
# is applied by 05_apply_final_model.R.  The retrained artifact is written to
# model/demo_retrained.cbm and is intentionally git-ignored.

suppressPackageStartupMessages({
  library(catboost)
  library(pROC)
})

source(file.path(
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) REPO_ROOT else ".",
  "R", "utils.R"
))

df <- read_cohort()
splits <- split_cohort(df)
train <- splits$train

# The public feature names are used for the retrained demo model; the locked
# model's adapter is in 05_apply_final_model.R.
train_pool <- catboost.load_pool(
  data = data.frame(
    PAS_Macrophages = factor(train$PAS_Macrophages, levels = c(0, 1, 2)),
    MUM1 = train$MUM1
  ),
  label = train$Group
)

params <- list(
  iterations = 500,
  learning_rate = 0.05,
  depth = 6,
  loss_function = "Logloss",
  eval_metric = "AUC",
  l2_leaf_reg = 3.0,
  random_strength = 1.0,
  random_seed = 42,
  verbose = 0,
  logging_level = "Silent"
)

set.seed(42)
cv <- catboost.cv(
  pool = train_pool,
  params = params,
  fold_count = 5,
  stratified = TRUE,
  shuffle = TRUE,
  partition_random_seed = 42,
  early_stopping_rounds = 50
)

auc_col <- grep("^test[.-]AUC[.-]mean$", names(cv), value = TRUE)
if (length(auc_col) != 1) {
  stop("Unexpected catboost.cv output columns: ", paste(names(cv), collapse = ", "))
}
best_iter <- which.max(cv[[auc_col]]) - 1L  # CV rows are iterations 0..N
best_iter <- max(1L, min(500L, as.integer(best_iter)))

write_csv(cv, "catboost_cv.csv")

final_params <- params
final_params$iterations <- best_iter
final_params$od_type <- NULL
final_params$od_wait <- NULL
final_params$verbose <- 0
final_params$logging_level <- "Silent"

demo_model <- catboost.train(learn_pool = train_pool, params = final_params)
demo_path <- file.path(MODEL_DIR, "demo_retrained.cbm")
catboost.save_model(demo_model, demo_path)
message("wrote: ", demo_path, " (", best_iter, " trees)")

# Evaluate the retrained demo model on all splits.
performance <- do.call(rbind, lapply(SPLITS, function(s) {
  part <- splits[[s]]
  pool <- catboost.load_pool(
    data = data.frame(
      PAS_Macrophages = factor(part$PAS_Macrophages, levels = c(0, 1, 2)),
      MUM1 = part$MUM1
    )
  )
  p <- as.numeric(catboost.predict(demo_model, pool, prediction_type = "Probability"))
  ci <- auc_with_ci(part$Group, p)
  data.frame(
    split = s,
    n = nrow(part),
    events = sum(part$Group == 1L),
    auc = ci[["auc"]],
    ci_lower = ci[["lower"]],
    ci_upper = ci[["upper"]],
    trees = best_iter,
    stringsAsFactors = FALSE
  )
}))
write_csv(performance, "catboost_demo_performance.csv")

importance <- catboost.get_feature_importance(demo_model, pool = train_pool)
importance_df <- data.frame(
  feature = c("PAS_Macrophages", "MUM1"),
  importance = as.numeric(importance)
)
importance_df$importance <- importance_df$importance / sum(importance_df$importance)
write_csv(importance_df, "catboost_demo_feature_importance.csv")

cat("\nCatBoost 5-fold CV best iteration:", best_iter, "\n")
cat("Retrained demo model performance (synthetic data):\n")
print(performance, row.names = FALSE)
cat("\nFeature importance:\n")
print(importance_df, row.names = FALSE)
