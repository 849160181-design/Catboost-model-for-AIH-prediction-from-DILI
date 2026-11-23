#!/usr/bin/env Rscript
# 07_subgroups.R -- exploratory subgroup performance.
#
# Subgroups are defined by PAS category and by training-set MUM1 tertiles.
# These analyses are descriptive and exploratory: the synthetic cohort is small,
# and the confidence intervals are wide.  They are not intended to support
# claims of differential effectiveness.

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

# Training-set MUM1 tertiles, applied unchanged to held-out splits.
mum1_breaks <- quantile(splits$train$MUM1, probs = c(0, 1 / 3, 2 / 3, 1), names = FALSE)
mum1_breaks[1] <- -Inf
mum1_breaks[4] <- Inf
mum1_labels <- c("T1_low", "T2_mid", "T3_high")

assign_subgroups <- function(part) {
  part$PAS_group <- factor(part$PAS_Macrophages, levels = c(0, 1, 2))
  part$MUM1_tertile <- cut(
    part$MUM1, breaks = mum1_breaks, labels = mum1_labels, include.lowest = TRUE
  )
  part
}

rows <- list()
for (s in SPLITS) {
  part <- assign_subgroups(splits[[s]])
  p <- probs[[s]]
  for (type in c("PAS_category", "MUM1_tertile")) {
    var <- if (type == "PAS_category") "PAS_group" else "MUM1_tertile"
    for (level in levels(part[[var]])) {
      idx <- which(part[[var]] == level)
      if (length(idx) == 0) next
      y <- part$Group[idx]
      pp <- p[idx]
      ci <- auc_with_ci(y, pp)
      m <- metrics_at(y, pp, 0.5)
      rows[[length(rows) + 1]] <- data.frame(
        split = s,
        subgroup_type = type,
        subgroup = level,
        n = length(idx),
        events = sum(y == 1L),
        auc = ci[["auc"]],
        ci_lower = ci[["lower"]],
        ci_upper = ci[["upper"]],
        sensitivity = m[["sensitivity"]],
        specificity = m[["specificity"]],
        note = if (length(unique(y)) < 2L) "single-class subgroup; AUC undefined" else "",
        stringsAsFactors = FALSE
      )
    }
  }
}
subgroups <- do.call(rbind, rows)
write_csv(subgroups, "subgroups.csv")

cat("Exploratory subgroup performance (synthetic demo):\n")
print(subgroups[, c("split", "subgroup_type", "subgroup", "n", "events", "auc", "ci_lower", "ci_upper")],
      row.names = FALSE)
cat("\nMUM1 tertile cut points (training):", paste(round(mum1_breaks[2:3], 2), collapse = ", "), "\n")
cat("Caution: subgroup analyses are exploratory; the synthetic cohort is small.\n")
