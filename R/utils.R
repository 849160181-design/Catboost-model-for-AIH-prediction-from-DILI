# Shared helpers for the 01-08 pipeline.
#
# All scripts are designed to be run from the repository root:
#   Rscript 01_qc/01_qc.R
# or through:
#   Rscript run_all.R
#
# The helpers use base R plus pROC (already a dependency of the modelling code).
# CatBoost is loaded only by the scripts that need it.

find_repo_root <- function() {
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) {
    return(get("REPO_ROOT", envir = .GlobalEnv))
  }
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    script <- normalizePath(sub("^--file=", "", file_arg[[1]]))
    return(normalizePath(file.path(dirname(script), "..")))
  }
  normalizePath(".")
}

REPO_ROOT <- find_repo_root()
DATA_DIR <- file.path(REPO_ROOT, "data")
DERIVED_DIR <- file.path(DATA_DIR, "derived")
RESULTS_DIR <- file.path(REPO_ROOT, "results")
FIGURES_DIR <- file.path(RESULTS_DIR, "figures")
MODEL_DIR <- file.path(REPO_ROOT, "model")

ensure_dir <- function(path) {
  if (!dir.exists(path)) dir.create(path, recursive = TRUE, showWarnings = FALSE)
  invisible(path)
}

ensure_dir(RESULTS_DIR)
ensure_dir(FIGURES_DIR)
ensure_dir(DERIVED_DIR)

COHORT_PATH <- file.path(DATA_DIR, "synthetic_cohort.csv")
REQUIRED_COLUMNS <- c("sample_id", "PAS_Macrophages", "MUM1", "Group", "split")
SPLITS <- c("train", "internal_test", "external_test")

read_cohort <- function(path = COHORT_PATH) {
  if (!file.exists(path)) {
    stop("Missing cohort file: ", path, call. = FALSE)
  }
  df <- read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  missing <- setdiff(REQUIRED_COLUMNS, names(df))
  if (length(missing) > 0) {
    stop("Missing columns: ", paste(missing, collapse = ", "), call. = FALSE)
  }
  df <- df[, REQUIRED_COLUMNS, drop = FALSE]
  df$sample_id <- trimws(as.character(df$sample_id))
  df$PAS_Macrophages <- as.integer(df$PAS_Macrophages)
  df$MUM1 <- as.numeric(df$MUM1)
  df$Group <- as.integer(df$Group)
  df$split <- as.character(df$split)
  validate_cohort(df)
  df
}

validate_cohort <- function(df) {
  if (nrow(df) == 0) stop("Cohort is empty", call. = FALSE)
  if (anyDuplicated(df$sample_id)) stop("Duplicate sample_id values", call. = FALSE)
  if (any(!df$PAS_Macrophages %in% c(0L, 1L, 2L))) {
    stop("PAS_Macrophages must be 0, 1, or 2", call. = FALSE)
  }
  if (any(!df$Group %in% c(0L, 1L))) stop("Group must be 0 or 1", call. = FALSE)
  if (any(!df$split %in% SPLITS)) {
    stop("split must be one of: ", paste(SPLITS, collapse = ", "), call. = FALSE)
  }
  if (any(!is.finite(df$MUM1)) || any(df$MUM1 <= 0)) {
    stop("MUM1 must be positive and finite", call. = FALSE)
  }
  for (s in SPLITS) {
    part <- df[df$split == s, , drop = FALSE]
    if (nrow(part) == 0) stop("No rows for split: ", s, call. = FALSE)
    if (length(unique(part$Group)) != 2L) {
      stop("Split ", s, " must contain both outcome classes", call. = FALSE)
    }
  }
  invisible(TRUE)
}

split_cohort <- function(df) {
  setNames(lapply(SPLITS, function(s) df[df$split == s, , drop = FALSE]), SPLITS)
}

# The locked model was trained with the R column name "PAS_.Macrophages".  The
# public schema uses a plain underscore; this adapter keeps the two in sync.
locked_features <- function(df) {
  data.frame(
    PAS_.Macrophages = factor(df$PAS_Macrophages, levels = c(0, 1, 2)),
    MUM1 = as.numeric(df$MUM1),
    check.names = FALSE
  )
}

predict_locked <- function(model, df) {
  pool <- catboost::catboost.load_pool(locked_features(df))
  as.numeric(catboost::catboost.predict(model, pool, prediction_type = "Probability"))
}

# AUC with an explicit positive class.  Returns NA when a split has one class.
safe_auc <- function(y, p) {
  if (length(unique(y)) < 2L) return(NA_real_)
  as.numeric(pROC::auc(pROC::roc(y, p, levels = c(0, 1), direction = "<", quiet = TRUE)))
}

auc_with_ci <- function(y, p) {
  if (length(unique(y)) < 2L) {
    return(c(auc = NA_real_, lower = NA_real_, upper = NA_real_))
  }
  r <- pROC::roc(y, p, levels = c(0, 1), direction = "<", quiet = TRUE)
  ci <- suppressWarnings(as.numeric(pROC::ci.auc(r, method = "delong")))
  c(auc = as.numeric(pROC::auc(r)), lower = ci[1], upper = ci[3])
}

metrics_at <- function(y, p, threshold) {
  pred <- as.integer(p >= threshold)
  tp <- sum(pred == 1L & y == 1L)
  tn <- sum(pred == 0L & y == 0L)
  fp <- sum(pred == 1L & y == 0L)
  fn <- sum(pred == 0L & y == 1L)
  sens <- if ((tp + fn) > 0) tp / (tp + fn) else NA_real_
  spec <- if ((tn + fp) > 0) tn / (tn + fp) else NA_real_
  ppv <- if ((tp + fp) > 0) tp / (tp + fp) else NA_real_
  npv <- if ((tn + fn) > 0) tn / (tn + fn) else NA_real_
  f1 <- if ((2 * tp + fp + fn) > 0) 2 * tp / (2 * tp + fp + fn) else NA_real_
  c(
    n = length(y),
    events = sum(y == 1L),
    sensitivity = sens,
    specificity = spec,
    accuracy = (tp + tn) / length(y),
    ppv = ppv,
    npv = npv,
    f1 = f1,
    youden = sens + spec - 1
  )
}

youden_threshold <- function(y, p) {
  if (length(unique(y)) < 2L) return(0.5)
  r <- pROC::roc(y, p, levels = c(0, 1), direction = "<", quiet = TRUE)
  best <- pROC::coords(
    r, "best", best.method = "youden", ret = "threshold", transpose = FALSE
  )
  as.numeric(best$threshold[[1]])
}

fmt <- function(x, digits = 3) {
  ifelse(is.na(x), "NA", formatC(x, format = "f", digits = digits))
}

fmt_p <- function(p, digits = 3) {
  ifelse(is.na(p), "NA", ifelse(p < 0.001, "<0.001", formatC(p, format = "f", digits = digits)))
}

write_csv <- function(df, filename, row.names = FALSE) {
  path <- file.path(RESULTS_DIR, filename)
  utils::write.csv(df, path, row.names = row.names, na = "NA")
  message("wrote: ", path)
  invisible(path)
}

write_derived <- function(df, split) {
  path <- file.path(DERIVED_DIR, paste0(split, ".csv"))
  utils::write.csv(df, path, row.names = FALSE)
  invisible(path)
}

# A small base-R ROC object for plotting without ggplot2.
roc_curve <- function(y, p) {
  r <- pROC::roc(y, p, levels = c(0, 1), direction = "<", quiet = TRUE)
  coords <- pROC::coords(
    r, "all",
    ret = c("specificity", "sensitivity"),
    transpose = FALSE
  )
  d <- data.frame(
    fpr = 1 - coords$specificity,
    tpr = coords$sensitivity
  )
  d <- d[order(d$fpr, d$tpr), , drop = FALSE]
  d$tpr <- cummax(d$tpr)
  d <- d[!duplicated(d$fpr), , drop = FALSE]
  d
}

message("repo root: ", REPO_ROOT)
