#!/usr/bin/env Rscript
# 08_figures.R -- manuscript-style figures from the locked model.
#
# All figures are generated from the synthetic demonstrator cohort.  They are
# deliberately labelled "synthetic demo" so they cannot be mistaken for the
# study figures.  Outputs are written to results/figures/ and are git-ignored.

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
labels <- c(train = "Training", internal_test = "Internal test", external_test = "External test")
colors <- c(train = "#1f77b4", internal_test = "#d62728", external_test = "#2ca02c")

ensure_dir(FIGURES_DIR)

# ---------------------------------------------------------------------------
# 1. ROC curves
# ---------------------------------------------------------------------------
roc_data <- lapply(SPLITS, function(s) roc_curve(splits[[s]]$Group, probs[[s]]))
names(roc_data) <- SPLITS

pdf(file.path(FIGURES_DIR, "Figure_ROC_synthetic_demo.pdf"), width = 6, height = 6)
plot(NA, xlim = c(0, 1), ylim = c(0, 1), xlab = "1 - Specificity", ylab = "Sensitivity",
     main = "ROC curves (synthetic demo)", las = 1)
abline(0, 1, lty = 2, col = "grey60")
for (s in SPLITS) {
  d <- roc_data[[s]]
  lines(d$fpr, d$tpr, col = colors[[s]], lwd = 2)
}
legend("bottomright", legend = sprintf("%s (AUC %.3f)", labels[SPLITS],
       sapply(SPLITS, function(s) safe_auc(splits[[s]]$Group, probs[[s]]))),
       col = colors[SPLITS], lwd = 2, bty = "n", cex = 0.85)
dev.off()

png(file.path(FIGURES_DIR, "Figure_ROC_synthetic_demo.png"), width = 900, height = 900, res = 150)
plot(NA, xlim = c(0, 1), ylim = c(0, 1), xlab = "1 - Specificity", ylab = "Sensitivity",
     main = "ROC curves (synthetic demo)", las = 1)
abline(0, 1, lty = 2, col = "grey60")
for (s in SPLITS) lines(roc_data[[s]]$fpr, roc_data[[s]]$tpr, col = colors[[s]], lwd = 2)
legend("bottomright", legend = sprintf("%s (AUC %.3f)", labels[SPLITS],
       sapply(SPLITS, function(s) safe_auc(splits[[s]]$Group, probs[[s]]))),
       col = colors[SPLITS], lwd = 2, bty = "n", cex = 0.85)
dev.off()

# ---------------------------------------------------------------------------
# 2. Calibration (quantile bins)
# ---------------------------------------------------------------------------
calibration_table <- function(y, p, bins = 5) {
  q <- unique(quantile(p, probs = seq(0, 1, length.out = bins + 1), names = FALSE))
  if (length(q) < 3) return(NULL)
  group <- cut(p, breaks = q, include.lowest = TRUE, labels = FALSE)
  do.call(rbind, lapply(sort(unique(group)), function(g) {
    idx <- which(group == g)
    data.frame(
      bin = g,
      n = length(idx),
      mean_predicted = mean(p[idx]),
      observed = mean(y[idx]),
      stringsAsFactors = FALSE
    )
  }))
}

pdf(file.path(FIGURES_DIR, "Figure_calibration_synthetic_demo.pdf"), width = 6, height = 6)
plot(NA, xlim = c(0, 1), ylim = c(0, 1), xlab = "Mean predicted probability",
     ylab = "Observed proportion", main = "Calibration (synthetic demo)", las = 1)
abline(0, 1, lty = 2, col = "grey60")
for (s in SPLITS) {
  cal <- calibration_table(splits[[s]]$Group, probs[[s]])
  if (!is.null(cal)) lines(cal$mean_predicted, cal$observed, type = "b", pch = 19,
                           col = colors[[s]], lwd = 2)
}
legend("topleft", legend = labels[SPLITS], col = colors[SPLITS], lwd = 2, pch = 19,
       bty = "n", cex = 0.85)
dev.off()

# ---------------------------------------------------------------------------
# 3. Decision-curve analysis (net benefit)
# ---------------------------------------------------------------------------
net_benefit <- function(y, p, thresholds = seq(0.05, 0.80, by = 0.01)) {
  n <- length(y)
  do.call(rbind, lapply(thresholds, function(pt) {
    pred <- p >= pt
    tp <- sum(pred & y == 1)
    fp <- sum(pred & y == 0)
    nb <- tp / n - fp / n * (pt / (1 - pt))
    data.frame(threshold = pt, net_benefit = nb, stringsAsFactors = FALSE)
  }))
}

pdf(file.path(FIGURES_DIR, "Figure_DCA_synthetic_demo.pdf"), width = 6, height = 5)
plot(NA, xlim = c(0.05, 0.80), ylim = c(-0.05, 0.55), xlab = "Threshold probability",
     ylab = "Net benefit", main = "Decision curve analysis (synthetic demo)", las = 1)
abline(h = 0, lty = 2, col = "grey60")
for (s in SPLITS) {
  nb <- net_benefit(splits[[s]]$Group, probs[[s]])
  lines(nb$threshold, nb$net_benefit, col = colors[[s]], lwd = 2)
}
legend("topright", legend = labels[SPLITS], col = colors[SPLITS], lwd = 2, bty = "n", cex = 0.85)
dev.off()

# ---------------------------------------------------------------------------
# 4. AUC forest plot
# ---------------------------------------------------------------------------
auc_rows <- do.call(rbind, lapply(SPLITS, function(s) {
  ci <- auc_with_ci(splits[[s]]$Group, probs[[s]])
  data.frame(split = s, label = labels[[s]], auc = ci[["auc"]],
             lower = ci[["lower"]], upper = ci[["upper"]], stringsAsFactors = FALSE)
}))

pdf(file.path(FIGURES_DIR, "Figure_AUC_forest_synthetic_demo.pdf"), width = 6, height = 3.6)
par(mar = c(4, 9, 3, 2))
plot(NA, xlim = c(0.75, 1.0), ylim = c(0.5, nrow(auc_rows) + 0.5),
     yaxt = "n", xlab = "AUC (95% CI)", ylab = "", main = "Discrimination (synthetic demo)", las = 1)
abline(v = 0.5, lty = 2, col = "grey60")
axis(2, at = seq_len(nrow(auc_rows)), labels = auc_rows$label, las = 1)
segments(auc_rows$lower, seq_len(nrow(auc_rows)), auc_rows$upper, seq_len(nrow(auc_rows)),
         col = colors[SPLITS], lwd = 2)
points(auc_rows$auc, seq_len(nrow(auc_rows)), pch = 18, cex = 1.8, col = colors[SPLITS])
dev.off()

# ---------------------------------------------------------------------------
# 5. Feature importance of the locked model
# ---------------------------------------------------------------------------
train_pool <- catboost.load_pool(
  data = data.frame(
    PAS_.Macrophages = factor(splits$train$PAS_Macrophages, levels = c(0, 1, 2)),
    MUM1 = splits$train$MUM1,
    check.names = FALSE
  )
)
importance <- as.numeric(catboost.get_feature_importance(model, pool = train_pool))
importance <- importance / sum(importance)
importance_df <- data.frame(
  feature = c("PAS_Macrophages", "MUM1"),
  importance = importance,
  stringsAsFactors = FALSE
)
write_csv(importance_df, "feature_importance_locked_model.csv")

pdf(file.path(FIGURES_DIR, "Figure_feature_importance_synthetic_demo.pdf"), width = 6, height = 3.6)
par(mar = c(4, 8, 3, 2))
barplot(importance_df$importance, names.arg = importance_df$feature, horiz = TRUE,
        las = 1, col = c("#6baed6", "#fd8d3c"), xlab = "Relative importance",
        main = "Locked model feature importance")
dev.off()

cat("Figures written to:", FIGURES_DIR, "\n")
print(auc_rows, row.names = FALSE)
print(importance_df, row.names = FALSE)
