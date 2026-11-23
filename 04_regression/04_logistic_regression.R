#!/usr/bin/env Rscript
# 04_regression.R -- conventional logistic-regression benchmarks.
#
# These models are reported alongside the CatBoost model.  They are fitted on
# the synthetic demonstrator data only; the estimates illustrate the pipeline
# and are not effect estimates for a specific cohort.

source(file.path(
  if (exists("REPO_ROOT", envir = .GlobalEnv, inherits = FALSE)) REPO_ROOT else ".",
  "R", "utils.R"
))

df <- read_cohort()
df$PAS_Macrophages <- factor(df$PAS_Macrophages, levels = c(0, 1, 2))

# The synthetic fixture can produce quasi-separation; suppress the fitted-
# probability warnings (the estimates are still reported and flagged in the
# README as illustrative).
fit_models <- list(
  "Univariable MUM1" = suppressWarnings(glm(Group ~ MUM1, data = df, family = binomial())),
  "Univariable PAS" = suppressWarnings(glm(Group ~ PAS_Macrophages, data = df, family = binomial())),
  "Multivariable" = suppressWarnings(glm(Group ~ MUM1 + PAS_Macrophages, data = df, family = binomial()))
)

extract_terms <- function(fit, model_name) {
  sm <- summary(fit)$coefficients
  beta <- sm[, "Estimate"]
  se <- sm[, "Std. Error"]
  p <- sm[, "Pr(>|z|)"]
  ci <- tryCatch(
    suppressWarnings(suppressMessages(confint(fit))),
    error = function(e) suppressWarnings(confint.default(fit))
  )
  data.frame(
    model = model_name,
    term = rownames(sm),
    beta = beta,
    std_error = se,
    odds_ratio = exp(beta),
    or_lower_95 = exp(ci[, 1]),
    or_upper_95 = exp(ci[, 2]),
    p_value = p,
    p_value_formatted = fmt_p(p),
    row.names = NULL,
    stringsAsFactors = FALSE
  )
}

coef_table <- do.call(rbind, lapply(names(fit_models), function(n) extract_terms(fit_models[[n]], n)))

fit_table <- data.frame(
  model = names(fit_models),
  n = sapply(fit_models, function(m) length(m$y)),
  events = sapply(fit_models, function(m) sum(m$y == 1)),
  aic = sapply(fit_models, AIC),
  null_deviance = sapply(fit_models, function(m) m$null.deviance),
  residual_deviance = sapply(fit_models, function(m) m$deviance),
  row.names = NULL,
  stringsAsFactors = FALSE
)

write_csv(coef_table, "logistic_regression.csv")
write_csv(fit_table, "logistic_model_fit.csv")

cat("Logistic regression (synthetic demonstrator data):\n")
print(coef_table[, c("model", "term", "odds_ratio", "or_lower_95", "or_upper_95", "p_value_formatted")],
      row.names = FALSE)
cat("\nModel fit:\n")
print(fit_table, row.names = FALSE)
