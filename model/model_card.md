# Model card — frozen CatBoost model

This card documents the frozen model distributed as `model/catboost_model.cbm`.
It is intended for research use and independent verification, **not** for diagnosis.

## 1. Model identity

| Item | Value |
|---|---|
| Artifact | `model/catboost_model.cbm` |
| SHA-256 | `3fd1c8e9d396b44b0873c72b94aaee202849a5908e4fe1c42415b95f5b8f6e9a` |
| Model type | CatBoost binary classifier (gradient-boosted decision trees) |
| Serialized with | CatBoost 1.2.5 (R interface) |
| Trees in artifact | 6 (best-AUC prefix; iteration 5 of a 56-iteration run) |
| Output | `P(Group = 1)`, where 1 = case and 0 = control |
| Inputs | `PAS_Macrophages` (categorical: 0/1/2) and `MUM1` (continuous) |

The training call requested up to 500 iterations with `early_stopping_rounds = 50`
and a test pool. The run stopped after 56 iterations; the best test AUC occurred at
iteration 5 (zero-based), and `use_best_model = TRUE` saved that 6-tree prefix. The
saved artifact is a deliberately truncated best-model prefix, not a model that stopped
training at 6 iterations. `model/model_manifest.json` records the requested
hyperparameters, the best iteration, the selection pool, and the artifact hash.

## 2. Intended use

- **Intended:** applying the model to new observations with the two inputs; independent
  verification of the scoring pipeline; research use with appropriate permissions.
- **Not intended:** diagnosis, treatment decisions, screening, or use as a medical
  device. The model has two histopathological inputs and has not been validated for
  prospective diagnostic use.

## 3. Inputs

| Field | Type | Definition | Allowed values |
|---|---|---|---|
| `PAS_Macrophages` | categorical | PAS-positive macrophages in the portal tract | `0` absent, `1` scattered, `2` clustered |
| `MUM1` | continuous | Average MUM1-positive cells per portal tract | positive number; observed range approximately 1–700 |

The model's internal name for the first feature is `PAS_.Macrophages`; the R wrapper
renames the data-frame column before creating a CatBoost pool. The pure-Python scorer
accepts the public name `PAS_Macrophages`.

## 4. Training data

The model was trained on a development cohort. The internal test cohort was held out
from training but was used as CatBoost's evaluation pool for early stopping and
best-model selection (`test_pool`; `use_best_model = TRUE`). The external test cohort
was not used for training or model selection.

Record-level training, internal-validation, and external-validation data are **not
redistributed**. No patient identifiers, pathology images, or medical records are
present in this repository or in the model artifact. The model contains learned tree
thresholds and leaf values only; it does not contain row-level records.

## 5. Hyperparameters

| Parameter | Value |
|---|---|
| Iterations (maximum) | 500 |
| Learning rate | 0.05 |
| Depth | 6 |
| Loss | Logloss |
| Evaluation metric | AUC |
| L2 leaf regularization | 3.0 |
| Random strength | 1.0 |
| Random seed | 42 |
| Early stopping | 50 rounds |
| Class weights | None |
| Categorical encoding | CatBoost internal (CTR / one-hot) |

Hyperparameter selection was performed within the development cohort. The run used
the internal test cohort as the CatBoost test pool; this is the model-selection step
that makes the internal-test performance optimistic. The external cohort was not used
for tuning or selection. The training-only 5-fold CV implementation in
`05_model/05_train_catboost.R` is the pattern to use for an unbiased internal estimate.

## 6. Model-selection caveat

The supplied `.cbm` was selected using the internal test cohort as CatBoost's
`test_pool` (`use_best_model = TRUE`). Internal-test performance is therefore
selection-optimistic, not a fully held-out estimate: the best internal-test AUC in the
training history is the value that chose the saved trees. External-test performance is
the primary held-out estimate because the external cohort was not used for selection.

For an unbiased internal estimate, retrain with a training-only validation split (or
nested CV) and evaluate once on the internal test cohort. This repository does not
distribute performance results.

## 7. How to apply the model

### Dependency-free

```bash
./quickstart/run_demo.sh
```

This uses `model/catboost_model_pure.py`, a standard-library-only export of the
`.cbm`, and writes a performance table to `results/` on the local machine.

### R / CatBoost

```r
library(catboost)
model <- catboost.load_model("model/catboost_model.cbm")
newdata <- read.csv("data/synthetic_cohort.csv")
newdata$PAS_.Macrophages <- factor(newdata$PAS_Macrophages, levels = c(0, 1, 2))
pool <- catboost.load_pool(newdata[, c("PAS_.Macrophages", "MUM1")])
newdata$predicted_probability <- catboost.predict(
  model, pool, prediction_type = "Probability"
)
```

The R path is wrapped by `05_model/05_apply_final_model.R` and `Rscript run_all.R`.

## 8. Reproducibility and parity

- `tests/test_model_parity.py` checks the pure-Python scorer against 48
  CatBoost-generated reference probabilities (tolerance `1e-6`).
- `tests/fixtures/model_expected.csv` contains those reference probabilities. They are
  model outputs for synthetic grid points, not patient records.
- `model/model_manifest.json` records SHA-256 hashes for the `.cbm` and the
  pure-Python export, plus the selection metadata.

## 9. Limitations

- The development cohort is modest; estimates have wide confidence intervals.
- Only two histopathological features are used; no other variables, laboratory values,
  or imaging features are included.
- The model assumes the same staining, scanning, and quantification protocol. Use with
  other scanners or protocols requires local validation.
- The 0.50 threshold is a reporting convention, not a prospectively validated operating
  point. Thresholds should be chosen and validated locally.
- The model outputs a probability, not a diagnosis.
