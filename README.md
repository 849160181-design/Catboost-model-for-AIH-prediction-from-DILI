# Histopathological AIH prediction with CatBoost

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](#reproducibility-checks)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](#five-minute-quickstart)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data%20%26%20docs-CC%20BY%204.0-lightgrey)](LICENSE-DATA)
[![DOI](https://img.shields.io/badge/DOI-pending-orange)](#zenodo-doi)

This repository accompanies the manuscript's final **CatBoost** model for predicting
AIH from two histopathological features:

- `MUM1` — average MUM1-positive cells per portal area (continuous);
- `PAS_Macrophages` — PAS-positive macrophages (categorical: absent / scattered / clustered).

It contains the locked model, the analysis code, and a fully synthetic demonstrator
cohort. **It does not contain the study's training, internal-validation, or
external-validation data, and it does not contain article-level result tables,
manuscript text, pathology images, or medical records.** See
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) for the data policy.

> **The five-minute acceptance test is
> [`./quickstart/run_demo.sh`](quickstart/run_demo.sh). It needs only Python 3.8+ and
> prints a Table 3-style AUC table in about one second. You do not need R, CatBoost, or
> any third-party Python package.

---

## Five-minute quickstart

```bash
git clone https://github.com/849160181-design/Catboost-model-for-AIH-prediction-from-DILI.git
cd Catboost-model-for-AIH-prediction-from-DILI
./quickstart/run_demo.sh
```

The script scores the synthetic cohort with the locked model and writes a
Table 3-style table (AUC, 95% CI, sensitivity, specificity, accuracy, PPV, NPV, F1) to
`results/` **on your machine**. `results/` is git-ignored; no result file is stored in
the repository.

Expected shape of the output:

```text
========================================================================
Table 3 — SYNTHETIC DEMO (not clinical performance)
========================================================================
Cohort             n  Events         AUC (95% CI)   Sens   Spec
Training          ..      ..  ... (...)             ...    ...
Internal test     ..      ..  ... (...)             ...    ...
External test     ..      ..  ... (...)             ...    ...
========================================================================
```

The exact AUC values depend only on the deterministic synthetic fixture and the locked
model. They are **software-verification outputs**, not the study's reported results.

**Why this is fast:** the locked `.cbm` model is exported to
[`model/catboost_model_pure.py`](model/catboost_model_pure.py), a standard-library-only
CatBoost scorer. The export is validated against CatBoost 1.2.5 on 48 grid points and on
the full synthetic cohort (maximum absolute difference `4.9 × 10⁻⁷`; see
[`tests/test_model_parity.py`](tests/test_model_parity.py)).

### Prefer R?

```r
library(catboost)
model <- catboost.load_model("model/catboost_model.cbm")
d <- read.csv("data/synthetic_cohort.csv")
d$PAS_.Macrophages <- factor(d$PAS_Macrophages, levels = c(0, 1, 2))
pool <- catboost.load_pool(d[, c("PAS_.Macrophages", "MUM1")])
d$p <- catboost.predict(model, pool, prediction_type = "Probability")
```

Or run the full pipeline: [`Rscript run_all.R`](run_all.R) (requires R ≥ 4.4,
CatBoost ≥ 1.2.5, and pROC).

---

## Repository map

| Path | Purpose |
|---|---|
| [`01_qc/01_qc.R`](01_qc/01_qc.R) | Schema, missingness, range, duplicate-ID, split-integrity, and class-balance QC |
| [`02_quantification.ijm`](02_quantification.ijm) | Documented ImageJ macro for PAS/MUM1 quantification; **template only** because images are not shared |
| [`03_features/03_build_feature_table.R`](03_features/03_build_feature_table.R) | Assemble the model-ready feature table; write derived splits and feature summaries |
| [`04_regression/04_logistic_regression.R`](04_regression/04_logistic_regression.R) | Univariable and multivariable logistic-regression benchmarks |
| [`05_model/05_train_catboost.R`](05_model/05_train_catboost.R) | Retrain CatBoost with stratified 5-fold CV on the synthetic training split (demonstration model; git-ignored) |
| [`05_model/05_apply_final_model.R`](05_model/05_apply_final_model.R) | Apply the locked `.cbm`; write predictions and a Table 3-style table locally |
| [`06_thresholds/06_thresholds.R`](06_thresholds/06_thresholds.R) | Threshold sweep, training-only Youden selection, fixed-threshold sensitivity analysis |
| [`07_subgroups/07_subgroups.R`](07_subgroups/07_subgroups.R) | Exploratory PAS-category and training-MUM1-tertile subgroups |
| [`08_figures/08_figures.R`](08_figures/08_figures.R) | ROC, calibration, DCA, AUC forest, and feature-importance figures |
| [`model/`](model/) | Locked model, pure-Python export, manifest, model card |
| [`data/`](data/) | Synthetic cohort, generator, and data note |
| [`data_dictionary.csv`](data_dictionary.csv) | Authoritative field definitions |
| [`quickstart/`](quickstart/) | Dependency-free Table 3-style reproduction and model-parity check |
| [`tests/`](tests/) | Schema, policy, parity, and end-to-end tests |
| [`zenodo/`](zenodo/) | Deposition metadata and DOI publication script |
| [`scripts/`](scripts/) | GitHub push helper, DOI finalisation, repository hygiene check |
| [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md) | Short public data policy (the full manuscript statement is kept private) |
| [`run_all.R`](run_all.R) | Run 01, 03–08 in order (02 is skipped because images are not shared) |

---

## Model

| Item | Value |
|---|---|
| Artifact | [`model/catboost_model.cbm`](model/catboost_model.cbm) |
| SHA-256 | `3fd1c8e9d396b44b0873c72b94aaee202849a5908e4fe1c42415b95f5b8f6e9a` |
| Type | CatBoost binary classifier (CatBoost 1.2.5, R interface) |
| Inputs | `PAS_Macrophages` (0/1/2), `MUM1` (continuous) |
| Output | `P(Group = 1)`, where 1 = case (AIH) and 0 = control |
| Trees in artifact | 6 (best-AUC prefix; see model card) |
| Training | Study development cohort; not redistributed |

Full intended use, limitations, selection metadata, and ethical notes:
[`model/model_card.md`](model/model_card.md). Machine-readable hashes and
hyperparameters: [`model/model_manifest.json`](model/model_manifest.json).

### Load the model in R

```r
library(catboost)
model <- catboost.load_model("model/catboost_model.cbm")
newdata <- data.frame(
  PAS_.Macrophages = factor(c(0, 2), levels = c(0, 1, 2)),
  MUM1 = c(15, 120)
)
catboost.predict(
  model,
  catboost.load_pool(newdata),
  prediction_type = "Probability"
)
```

The model's internal categorical feature name is `PAS_.Macrophages`; the public schema
uses `PAS_Macrophages`. The adapter is in [`R/utils.R`](R/utils.R).

---

## Data availability and privacy

**No patient-level data, pathology images, whole-slide images, image metadata, or
medical records are in this repository.** The study's training, internal-validation, and
external-validation datasets are also **not** included. This is a deliberate
restriction:

- histopathology images and linked clinical records are identifiable;
- the original ethics approvals and informed-consent documents cover the study
  analyses only, not open deposition;
- public deposition would breach the participants' consent and applicable
  data-protection rules.

The repository therefore provides:

1. a **synthetic cohort** (180 rows) whose fields match
   [`data_dictionary.csv`](data_dictionary.csv);
2. the **locked model** and a dependency-free scorer;
3. the **analysis code** that can be run on the synthetic cohort.

The synthetic cohort is **not** a de-identified copy of the study data. It is generated
from a transparent latent-class model with fixed seeds and is calibrated to produce a
realistic AUC for software verification. It must not be used to estimate clinical
performance, prevalence, or subgroup effects. Full wording:
[`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md).

Record-level study data may be available only under a controlled-access agreement,
where the original consent and ethics approval permit, and after review by the data
access committee. The full manuscript Data sharing statement is maintained privately
and is not part of this repository.

---

## Reproducibility checks

```bash
# Python tests: schema, policy, model parity, publication tools, end-to-end demo
python3 -m unittest discover -s tests -v

# Model parity only
python3 tests/test_model_parity.py

# Full R pipeline (requires R + CatBoost + pROC)
Rscript run_all.R

# R vs Python prediction parity on the synthetic cohort
Rscript 05_model/05_apply_final_model.R
# -> results/model_parity_R_vs_python.csv (tolerance 1e-6)
```

Determinism:

- synthetic data: fixed seeds in [`data/generate_synthetic_data.py`](data/generate_synthetic_data.py);
- CatBoost: `random_seed = 42`;
- bootstrap CI: seed `20240501`, 2,000 resamples;
- model artifact: SHA-256 pinned in the manifest and checked by the tests.

Environment used to build the release: R 4.4.0, CatBoost 1.2.5, pROC 1.19.0.1,
Python 3.9.6, macOS 15.1. The Python path has no third-party dependencies and is
tested in GitHub Actions on Python 3.11.

---

## Zenodo DOI

A Zenodo DOI is planned. The DOI is **not yet published**; the current value is the
placeholder `10.5281/zenodo.XXXXXXX`. The repository stores the DOI in
[`CITATION.cff`](CITATION.cff), [`README.md`](README.md), the model card, and
[`zenodo/deposition_metadata.json`](zenodo/deposition_metadata.json). The three
manuscript locations (Data sharing statement, Methods–Reproducibility, reference 41)
are maintained in a **private** manuscript folder outside this repository and are not
published here.

After publication:

```bash
python3 scripts/finalize_doi.py --doi 10.5281/zenodo.XXXXXXX
python3 -m unittest discover -s tests -v
```

To update the private manuscript insert files at the same time:

```bash
python3 scripts/finalize_doi.py \
  --doi 10.5281/zenodo.XXXXXXX \
  --manuscript-dir /path/to/private/manuscript
```

---

## Citation

Before the DOI is assigned, cite the manuscript. After the Zenodo release, use the
metadata in [`CITATION.cff`](CITATION.cff):

```text
[Authors]. (2026). Histopathological AIH prediction with CatBoost (v1.0.0)
[Computer software]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX
```

---

## License

- **Code** (R, Python, ImageJ macro, shell): [MIT](LICENSE).
- **Data, documentation, and figures**: [CC BY 4.0](LICENSE-DATA).

The model artifact is released for research reproducibility under the same terms as the
code. It is not a medical device and is not intended for clinical decision-making.

---

## Reviewer checklist

- [ ] Clone the repository into a clean directory.
- [ ] Run `./quickstart/run_demo.sh`; confirm a three-row AUC table is printed in under 5 minutes.
- [ ] Confirm `results/` is created locally and is not tracked by Git.
- [ ] Run `python3 -m unittest discover -s tests -v`; confirm all tests pass.
- [ ] Read [`DATA_AVAILABILITY.md`](DATA_AVAILABILITY.md); confirm the raw-data restriction is explicit.
- [ ] Confirm `git ls-files` contains no `train_data.csv`, `test_data.csv`, `external_test_data.csv`, pathology images, medical records, manuscript text, or article result tables.
- [ ] Compare only the **synthetic demo** output with the paper's reported results as a software check; the demo is not a validation cohort.

---

## Contact

Corresponding author: `[name, affiliation, email]`.
For data-access requests, contact the data access committee at `[email]`.
Please open a GitHub issue for code problems; do not include patient information in
issues or pull requests.
