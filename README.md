# Histopathological AIH prediction with CatBoost

A frozen CatBoost model that estimates the probability of autoimmune hepatitis (AIH)
from two histopathological features, together with the analysis code used to build,
validate and apply it.

- `MUM1` — average MUM1-positive cells per portal area (continuous)
- `PAS_Macrophages` — PAS-positive macrophages (0 absent, 1 scattered, 2 clustered)

## Quickstart (no dependencies)

```bash
git clone https://github.com/849160181-design/Catboost-model-for-AIH-prediction-from-DILI.git
cd Catboost-model-for-AIH-prediction-from-DILI
./quickstart/run_demo.sh
```

The script scores the synthetic cohort with the frozen model and prints an AUC table
(AUC with 95% CI, sensitivity, specificity, accuracy, PPV, NPV, F1) to `results/`, which
is git-ignored. Only Python 3.8+ is required: the model is also exported as a
standard-library scorer (`model/catboost_model_pure.py`), validated against CatBoost
1.2.5 on 48 grid points and on the full synthetic cohort (maximum absolute difference
4.9 × 10⁻⁷).

## Applying the model in R

```r
library(catboost)
model <- catboost.load_model("model/catboost_model.cbm")

newdata <- data.frame(
  PAS_.Macrophages = factor("1", levels = c("0", "1", "2")),    # 0 absent, 1 scattered, 2 clustered
  MUM1 = 120
)
catboost.predict(model, catboost.load_pool(newdata), prediction_type = "Probability")
```

The model's internal categorical feature name is `PAS_.Macrophages`; the public schema uses
`PAS_Macrophages`. The adapter is in `R/utils.R`. To run the whole pipeline, use
`Rscript run_all.R` (R ≥ 4.4, CatBoost ≥ 1.2.5, pROC).

## Repository map

| Path | Purpose |
|---|---|
| `01_qc/` | Schema, missingness, duplicate-ID and split-integrity checks |
| `02_quantification.ijm` | Documented ImageJ macro for PAS/MUM1 quantification (template only; images not shared) |
| `03_features/` | Build the model-ready feature table |
| `04_regression/` | Univariable and multivariable logistic-regression benchmarks |
| `05_model/` | Train CatBoost on the synthetic split; apply the frozen model |
| `06_thresholds/` | Threshold sweep and fixed-threshold sensitivity analysis |
| `07_subgroups/` | Exploratory subgroup analyses |
| `08_figures/` | ROC, calibration, decision-curve and feature-importance figures |
| `model/` | Frozen model, pure-Python scorer, manifest, model card |
| `data/` | Synthetic cohort (180 rows), generator and data note |
| `data_dictionary.csv` | Field definitions |
| `quickstart/` | Dependency-free demo and model-parity check |
| `tests/` | Schema, policy, parity and end-to-end tests |
| `run_all.R` | Run 01, 03–08 in order |

## Model

| Item | Value |
|---|---|
| Artifact | `model/catboost_model.cbm` |
| SHA-256 | `3fd1c8e9d396b44b0873c72b94aaee202849a5908e4fe1c42415b95f5b8f6e9a` |
| Type | CatBoost binary classifier (CatBoost 1.2.5, R interface) |
| Inputs | `PAS_Macrophages` (0/1/2), `MUM1` (continuous) |
| Output | P(AIH), from 0 to 1 |
| Trees | 6 (best-AUC prefix; see `model/model_card.md`) |

Intended use, limitations and selection metadata: `model/model_card.md`.

## Data availability

The repository contains **no patient-level data, pathology images, whole-slide images
or medical records**, and none of the datasets used to develop or validate the model.
Histopathology images and linked clinical records are identifiable, and the ethics
approvals and informed consent under which they were collected do not permit open
deposition.

What is provided instead:

1. a synthetic cohort of 180 rows matching `data_dictionary.csv`, generated from a
   transparent latent-class model with fixed seeds;
2. the frozen model and a dependency-free scorer;
3. the analysis code, which runs end to end on the synthetic cohort.

The synthetic cohort is not a de-identified copy of any study data and must not be used
to estimate clinical performance, prevalence or subgroup effects. See
`DATA_AVAILABILITY.md`.

## Reproducibility checks

```bash
python3 -m unittest discover -s tests -v      # all tests
python3 tests/test_model_parity.py            # model parity only
Rscript 05_model/05_apply_final_model.R       # R vs Python predictions (tolerance 1e-6)
Rscript run_all.R                             # full R pipeline
```

Determinism: synthetic data use fixed seeds; CatBoost uses `random_seed = 42`;
bootstrap CIs use seed `20240501` with 2,000 resamples; the model SHA-256 is pinned in
`model/model_manifest.json` and checked by the tests.

## License

Code (R, Python, ImageJ macro, shell) is released under the MIT licence (`LICENSE`);
data, documentation and figures under CC BY 4.0 (`LICENSE-DATA`). The model is released
for research reproducibility on the same terms as the code. It is not a medical device
and is not intended for clinical decision-making.
