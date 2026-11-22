# Synthetic demonstrator data

`data/synthetic_cohort.csv` is the only dataset in this repository. It is **fully
synthetic**. It is not a subset, transformation, or de-identification of the study
cohort, and it must not be analysed as if it were a clinical sample.

## Why synthetic data?

The study data contain identifiable patient information (histopathology images,
medical records, and linked clinical variables). The original consent and ethics
approvals cover the study analyses only; they do not cover open deposition. We
therefore do not deposit record-level data. The synthetic fixture lets reviewers run
the complete scoring and evaluation pipeline without access to those records. See
`../DATA_AVAILABILITY.md`.

## File and schema

One row per synthetic participant, 180 rows:

| Column | Type | Values |
|---|---|---|
| `sample_id` | string | `SYN-T-###` (training), `SYN-V-###` (internal test), `SYN-E-###` (external test) |
| `PAS_Macrophages` | integer | `0` absent, `1` scattered, `2` clustered |
| `MUM1` | float | positive cells per portal tract, clipped to 1–700 |
| `Group` | integer | `1` case, `0` control |
| `split` | string | `train`, `internal_test`, `external_test` |

The authoritative field definitions are in `../data_dictionary.csv`. The file is
UTF-8, comma-separated, with a header row and `\n` line endings.

## How it was generated

Run:

```bash
python3 data/generate_synthetic_data.py
```

The script uses only the Python standard library and a fixed random seed. For each
participant:

1. `Group ~ Bernoulli(0.5)`.
2. `MUM1` is drawn from a group-specific log-normal distribution and clipped to
   `[1, 700]` (controls: μ=2.00, σ=0.90; cases: μ=4.20–4.25, σ=1.05–1.10).
3. `PAS_Macrophages` is drawn from a group-specific categorical distribution
   (controls: 0.55/0.35/0.10; cases: 0.35/0.40/0.25).

The exact seeds and parameters are in `generate_synthetic_data.py`. The generator does
not read the study data and does not call the model.

### Calibration disclosure

The parameters and seeds were chosen **once** so that the locked model returns a
realistic AUC range on the synthetic fixture. This makes the fixture useful as a
software regression test: if a future code change breaks the scoring path, the demo
AUCs will move. It is **not** evidence of model performance, and no article-level
performance table or confidence interval is stored in this repository.

The internal test cohort was CatBoost's `test_pool` for `use_best_model`, so
internal-test performance is selection-optimistic. The synthetic fixture is a
software-verification convenience; it does not make the internal-test estimate
independent. See `model/model_card.md` §6.

## What is intentionally absent

- No study participant identifiers, dates, ages, sex, centre, or clinical variables.
- No pathology images, whole-slide images, or image metadata.
- No source `train_data.csv`, `test_data.csv`, or `external_test_data.csv`.
- No manuscript text, article result tables, or row-level predictions for study
  participants.

## Reproducibility checks

```bash
python3 -m unittest discover -s tests -v
./quickstart/run_demo.sh
```

The test suite checks the schema, the model parity fixture, and the demo output.
