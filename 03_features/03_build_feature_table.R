#!/usr/bin/env Rscript
# 03_features.R -- assemble the analysis-ready feature table.
#
# In the full study, this script joins the image-quantification output from
# 02_quantification.ijm to the clinical/outcome table.  The public repository
# starts from the synthetic analysis-ready table; this script validates it,
# writes one file per split, and produces descriptive feature summaries.

source(file.path(
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) REPO_ROOT else ".",
  "R", "utils.R"
))

df <- read_cohort()
splits <- split_cohort(df)

# Write one file per split so downstream scripts never need to re-implement
# the split logic.
for (s in SPLITS) {
  write_derived(splits[[s]], s)
}

# Feature completeness and distribution summary.
feature_summary <- do.call(rbind, lapply(SPLITS, function(s) {
  part <- splits[[s]]
  data.frame(
    split = s,
    n = nrow(part),
    mum1_min = min(part$MUM1),
    mum1_q1 = quantile(part$MUM1, 0.25, names = FALSE),
    mum1_median = median(part$MUM1),
    mum1_q3 = quantile(part$MUM1, 0.75, names = FALSE),
    mum1_max = max(part$MUM1),
    pas_absent = sum(part$PAS_Macrophages == 0L),
    pas_scattered = sum(part$PAS_Macrophages == 1L),
    pas_clustered = sum(part$PAS_Macrophages == 2L),
    stringsAsFactors = FALSE
  )
}))
feature_summary[, 3:7] <- round(feature_summary[, 3:7], 2)

write_csv(feature_summary, "feature_summary.csv")

# A compact, model-ready table with the public feature names.  The locked model
# adapter in R/utils.R renames PAS_Macrophages to its internal name.
model_ready <- df[, c("sample_id", "PAS_Macrophages", "MUM1", "Group", "split")]
write_csv(model_ready, "model_ready_features.csv")

cat("Feature table assembled.\n")
print(feature_summary)
cat("\nDerived splits:\n")
for (s in SPLITS) cat(sprintf("  %-14s %s\n", s, file.path("data", "derived", paste0(s, ".csv"))))
