#!/usr/bin/env Rscript
# 01_qc.R -- quality control of the analysis-ready feature table.
#
# The study's image-level QC is performed before quantification and is not
# reproducible from the public repository because the images are not shared.
# This script performs the QC that *can* be reproduced: schema, missingness,
# ranges, duplicates, split integrity, and class balance.

suppressPackageStartupMessages({
  library(pROC)
})

source(file.path(
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) REPO_ROOT else ".",
  "R", "utils.R"
))

df <- read_cohort()
splits <- split_cohort(df)

# ---------------------------------------------------------------------------
# 1. Structural checks
# ---------------------------------------------------------------------------
report <- data.frame(
  check = character(),
  split = character(),
  value = character(),
  pass = logical(),
  stringsAsFactors = FALSE
)

add_check <- function(check, split, value, pass) {
  report[nrow(report) + 1, ] <<- list(check, split, as.character(value), isTRUE(pass))
}

add_check("rows", "all", nrow(df), nrow(df) > 0)
add_check("unique_sample_id", "all", !anyDuplicated(df$sample_id), !anyDuplicated(df$sample_id))
add_check("missing_values", "all", sum(is.na(df)), sum(is.na(df)) == 0)
add_check("dictionary_columns_match", "all",
          paste(setdiff(names(df), read.csv(file.path(REPO_ROOT, "data_dictionary.csv"))$field), collapse = ","),
          setequal(names(df), read.csv(file.path(REPO_ROOT, "data_dictionary.csv"))$field))

for (s in SPLITS) {
  part <- splits[[s]]
  add_check("rows", s, nrow(part), nrow(part) > 0)
  add_check("events", s, sum(part$Group == 1L), sum(part$Group == 1L) > 0)
  add_check("controls", s, sum(part$Group == 0L), sum(part$Group == 0L) > 0)
  add_check("both_classes", s, length(unique(part$Group)) == 2L, length(unique(part$Group)) == 2L)
  add_check("pas_levels_valid", s, all(part$PAS_Macrophages %in% 0:2),
            all(part$PAS_Macrophages %in% 0:2))
  add_check("mum1_positive", s, all(part$MUM1 > 0), all(part$MUM1 > 0))
  add_check("mum1_range", s, sprintf("%.2f-%.2f", min(part$MUM1), max(part$MUM1)),
            all(is.finite(part$MUM1)))
}

# Split integrity: no participant may appear in more than one split.
id_split <- table(df$sample_id)
add_check("no_split_overlap", "all", sum(id_split > 1L), sum(id_split > 1L) == 0)

# ---------------------------------------------------------------------------
# 2. Baseline characteristics (Table 1)
# ---------------------------------------------------------------------------
baseline <- do.call(rbind, lapply(SPLITS, function(s) {
  part <- splits[[s]]
  data.frame(
    split = s,
    n = nrow(part),
    events = sum(part$Group == 1L),
    controls = sum(part$Group == 0L),
    mum1_median = median(part$MUM1),
    mum1_q1 = quantile(part$MUM1, 0.25, names = FALSE),
    mum1_q3 = quantile(part$MUM1, 0.75, names = FALSE),
    pas_0 = sum(part$PAS_Macrophages == 0L),
    pas_1 = sum(part$PAS_Macrophages == 1L),
    pas_2 = sum(part$PAS_Macrophages == 2L),
    stringsAsFactors = FALSE
  )
}))
baseline[, 5:7] <- round(baseline[, 5:7], 2)

by_group <- do.call(rbind, lapply(sort(unique(df$Group)), function(g) {
  part <- df[df$Group == g, , drop = FALSE]
  data.frame(
    group = if (g == 1L) "case" else "control",
    n = nrow(part),
    mum1_median = median(part$MUM1),
    mum1_q1 = quantile(part$MUM1, 0.25, names = FALSE),
    mum1_q3 = quantile(part$MUM1, 0.75, names = FALSE),
    pas_0 = sum(part$PAS_Macrophages == 0L),
    pas_1 = sum(part$PAS_Macrophages == 1L),
    pas_2 = sum(part$PAS_Macrophages == 2L),
    stringsAsFactors = FALSE
  )
}))
by_group[, 3:5] <- round(by_group[, 3:5], 2)

# ---------------------------------------------------------------------------
# 3. Write outputs
# ---------------------------------------------------------------------------
write_csv(report, "qc_report.csv")
write_csv(baseline, "Table1_baseline_by_split.csv")
write_csv(by_group, "Table1_baseline_by_group.csv")

summary_lines <- c(
  "QC summary -- synthetic demonstrator cohort",
  paste("repo root:", REPO_ROOT),
  paste("rows:", nrow(df)),
  paste("splits:", paste(sprintf("%s=%d", SPLITS, sapply(splits, nrow)), collapse = ", ")),
  paste("checks passed:", sum(report$pass), "/", nrow(report)),
  paste("missing values:", sum(is.na(df))),
  paste("duplicate IDs:", anyDuplicated(df$sample_id)),
  paste("split overlap:", sum(id_split > 1L)),
  "",
  "Note: image-level QC (focus, staining batch, ROI selection) is documented in",
  "02_quantification.ijm and the Methods; pathology images are not shared because",
  "they contain identifiable patient information."
)
writeLines(summary_lines, file.path(RESULTS_DIR, "qc_summary.txt"))

cat(paste(summary_lines, collapse = "\n"), "\n")
if (!all(report$pass)) {
  print(report[!report$pass, , drop = FALSE])
  stop("QC checks failed", call. = FALSE)
}
