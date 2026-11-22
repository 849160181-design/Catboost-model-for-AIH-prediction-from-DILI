# Zenodo archive and DOI

This directory contains the metadata and a one-command publication script for the
archived release. The archive is what reference 41 and the Data sharing statement cite.

## What is archived

- the locked CatBoost model (`model/catboost_model.cbm`) and its pure-Python/JSON exports;
- the `01_qc` → `08_figures` analysis code;
- the 180-row synthetic demonstrator cohort and its generator;
- `data_dictionary.csv`, the model card, the manifest, and this release tooling.

**Not archived:** patient-level data, pathology images, whole-slide images, image
metadata, medical records, study participant identifiers, manuscript text, and
article-level result tables. The publication script zips the repository as-is and
excludes `manuscript/` and `results/`; run `python3 scripts/check_repo_hygiene.py` first
to confirm that no forbidden file slipped in.

## 1. Create a token

1. Sign in at <https://zenodo.org>.
2. Open **Account → Applications → Personal access tokens → New token**.
3. Enable `deposit:write` and `deposit:actions`.
4. Store it outside the repository:

```bash
mkdir -p ~/.config/dsh && chmod 700 ~/.config/dsh
printf '%s' 'YOUR_TOKEN' > ~/.config/dsh/zenodo_token
chmod 600 ~/.config/dsh/zenodo_token
```

Alternatively, export `ZENODO_TOKEN` in the shell that runs the script. Never commit a
token or paste it into an issue.

## 2. Edit the metadata

Open `zenodo/deposition_metadata.json` and replace:

- `[Authors]` with the manuscript author list, in the same order as the paper;
- the title if the manuscript title differs;
- verify that `related_identifiers` points to
  `https://github.com/849160181-design/Catboost-model-for-AIH-prediction-from-DILI`
  (already set);
- `publication_date` if the release date differs.

The script refuses to publish while `[Authors]`, `XXXX`, `TODO`, `[Year]`, or
`[Journal]` remain (it also rejects any `OWNER` left in a URL), unless
`--allow-placeholders` is used for a sandbox smoke test.

## 3. Test against the sandbox (optional but recommended)

```bash
python3 zenodo/publish.py --sandbox --allow-placeholders
```

The sandbox DOI uses the `10.5072/zenodo.*` prefix and is not a production DOI. Do not
put it in the manuscript.

## 4. Publish to production

```bash
python3 scripts/check_repo_hygiene.py
python3 zenodo/publish.py --finalize
```

`--finalize` publishes the deposition and then runs
`scripts/finalize_doi.py --doi <DOI>`, which writes the DOI into the four public
repository locations:

1. `README.md`;
2. `CITATION.cff`;
3. `model/model_card.md`;
4. `zenodo/deposition_metadata.json`.

The three manuscript locations are kept private and are **not** part of the public
repository. If you maintain them in a private folder, pass it explicitly:

```bash
python3 zenodo/publish.py --finalize --manuscript-dir /path/to/private/manuscript
```

This also updates and verifies:

1. `data_sharing_statement.md` (Data sharing statement);
2. `methods_reproducibility.md` (Methods–Reproducibility);
3. `references.md` (reference 41).

If you prefer to publish from the web UI, use `--no-publish`, then run
`python3 scripts/finalize_doi.py --doi <DOI>` manually.

## 5. Verify

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_repo_hygiene.py --strict-doi
git diff
```

The strict hygiene check rejects the placeholder. If you maintain private manuscript
inserts, pass `--manuscript-dir` and verify the three locations manually. Commit the DOI
update and tag the release:

```bash
git add -A
git commit -m "Release v1.0.0: Zenodo DOI"
git tag -a v1.0.0 -m "v1.0.0"
git push origin main --tags
```

## 6. Create the GitHub release

Attach the same archive (`zenodo/aih-catboost-v1.0.0.zip`) to the GitHub release so the
repository and the archive are byte-identical. The GitHub release is a convenience
mirror; the Zenodo DOI is the persistent identifier.

## Versioning

Zenodo supports new versions of a deposition. For a code-only correction, publish a new
version (v1.0.1) and update the DOI in the public repository locations and, if used, the private manuscript inserts.
Do not overwrite the files of a published version.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No Zenodo token found` | Token not in env/file | Set `ZENODO_TOKEN` or write `~/.config/dsh/zenodo_token` |
| `metadata still contains placeholders` | Authors still `[Authors]` | Edit `deposition_metadata.json` |
| `Zenodo API error 401` | Token lacks `deposit:write`/`deposit:actions` | Create a new token with both scopes |
| `Zenodo API error 403` | Token not allowed to publish | Check the account is verified; use the web UI if needed |
| DOI not resolving immediately | Zenodo propagation | Wait a few minutes; the DOI URL is `https://doi.org/<DOI>` |
| `strict DOI requested but the placeholder is still present` | `finalize_doi.py` not run | Run it with the published DOI |

## Security

- The script prints the deposition URL, not the token.
- The token is read from the environment or a `chmod 600` file.
- The zip excludes `.git`, generated figures, derived data, and the demo model.
- Do not add patient data to the archive. The repository is deliberately limited to
  synthetic data, code, the model, and documentation.
