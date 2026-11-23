#!/usr/bin/env Rscript
# run_all.R -- run the public analysis pipeline in order.
#
# Requirements: R >= 4.4, catboost (>= 1.2.5), pROC.
# The five-minute dependency-free path is ./quickstart/run_demo.sh and does not need R.
#
# Usage (from the repository root):
#   Rscript run_all.R
#   Rscript run_all.R --skip-figures
#
args <- commandArgs(trailingOnly = TRUE)
skip_figures <- "--skip-figures" %in% args

script_path <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE)[1])
REPO_ROOT <- if (!is.na(script_path)) {
  normalizePath(dirname(normalizePath(script_path)))
} else {
  normalizePath(".")
}
assign("REPO_ROOT", REPO_ROOT, envir = .GlobalEnv)
setwd(REPO_ROOT)

message("Repository root: ", REPO_ROOT)
message("R: ", R.version.string)

steps <- c(
  "01_qc/01_qc.R",
  "03_features/03_build_feature_table.R",
  "04_regression/04_logistic_regression.R",
  "05_model/05_train_catboost.R"
)

if (nzchar(Sys.which("python3"))) {
  message("\n=== quickstart Python scorer (for R-vs-Python parity) ===")
  status <- system2("python3", c("quickstart/run_demo.py", "--quiet"), stdout = TRUE, stderr = TRUE)
  if (!is.null(attr(status, "status")) && attr(status, "status") != 0) {
    warning("Python quickstart failed; continuing with the R pipeline.")
  }
}

steps <- c(steps, "05_model/05_apply_final_model.R", "06_thresholds/06_thresholds.R", "07_subgroups/07_subgroups.R")
if (!skip_figures) steps <- c(steps, "08_figures/08_figures.R")

for (step in steps) {
  message("\n================================================================")
  message("Running ", step)
  message("================================================================")
  t0 <- Sys.time()
  source(file.path(REPO_ROOT, step), echo = FALSE)
  dt <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  message(sprintf("Finished %s in %.1f s", step, dt))
}

message("\n================================================================")
message("Pipeline complete.")
message("Key outputs:")
for (f in c(
  "results/qc_report.csv",
  "results/baseline_by_split.csv",
  "results/logistic_regression.csv",
  "results/performance_locked_model_R.csv",
  "results/performance_demo.csv",
  "results/thresholds.csv",
  "results/subgroups.csv",
  "results/feature_importance_locked_model.csv",
  "results/model_parity_R_vs_python.csv"
)) {
  path <- file.path(REPO_ROOT, f)
  message(sprintf("  %-52s %s", f, if (file.exists(path)) "OK" else "missing"))
}
message("Figures: results/figures/")
