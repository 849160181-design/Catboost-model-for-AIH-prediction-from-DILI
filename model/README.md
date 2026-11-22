# Model directory

| File | Purpose |
|---|---|
| `catboost_model.cbm` | Locked CatBoost 1.2.5 model |
| `catboost_model_pure.py` | Dependency-free Python export, used by the five-minute demo |
| `model_card.md` | Intended use, inputs, training metadata, limitations, ethics |
| `model_manifest.json` | SHA-256 hashes, feature mapping, hyperparameters, selection metadata |

## Important selection metadata

The artifact is the **best-AUC prefix** of a 56-iteration, early-stopped run: iteration 5,
6 trees, selected with the internal test cohort as CatBoost's `test_pool` and
`use_best_model = TRUE`. Internal-test performance is therefore selection-optimistic;
external-test performance is the primary held-out estimate. See `model_card.md` §6 and
`model_manifest.json` (`selection_pool`, `best_iteration_zero_based`).

## Checksums

```text
catboost_model.cbm       3fd1c8e9d396b44b0873c72b94aaee202849a5908e4fe1c42415b95f5b8f6e9a
catboost_model_pure.py   31929854995273f6931d64b1413141d27f5fe538d0d6dcb87f1ac587195b1679
```

## Why there is a pure-Python export

The reviewer path must work on a machine without R or CatBoost. CatBoost 1.2.5 can
export a model to standalone Python. The R exporter leaves the categorical hash table
empty, so the three hashes for PAS levels 0/1/2 were restored in
`catboost_model_pure.py`. The restoration is validated against CatBoost on 48 grid
points (`tests/fixtures/model_expected.csv`).

## Regenerate the Python export

```r
library(catboost)
m <- catboost.load_model("model/catboost_model.cbm")
catboost.save_model(m, "model/catboost_model_pure.py", file_format = "python")
```

After regenerating the export, restore the `cat_features_hashes` block
(`18446744072271266578`, `1121341681`, `18446744072424761207` for levels `0`, `1`, `2`)
and the `predict_proba` helper, then run `python3 -m unittest discover -s tests -v`.

## Important

The `.cbm` contains learned tree parameters only. It does **not** contain row-level
patient records, images, or identifiers. The training data are not redistributed; see
`../DATA_AVAILABILITY.md`.
