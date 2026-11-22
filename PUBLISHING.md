# Publishing this repository (GitHub + Zenodo)

This guide is for the author who will make the release public. The repository is
already complete and tested locally. Two external actions remain because they require
your accounts: creating the GitHub repository and publishing the Zenodo archive.

The archive must never contain patient-level data, pathology images, medical records,
manuscript text, or article-level result tables. The public repository is limited to
code, the synthetic example cohort, the locked model, and documentation. Run the
hygiene check before uploading:

```bash
python3 scripts/check_repo_hygiene.py
```

Both `scripts/publish_github.sh` and `zenodo/publish.py` run this check and abort if it
fails, so a forbidden study file cannot be pushed or archived by accident.

---

## Option A — GitHub web UI (no token)

1. Sign in to GitHub and use the existing empty public repository
   `849160181-design/Catboost-model-for-AIH-prediction-from-DILI`
   (or create a new empty repository with that name). Do **not** initialise it with a
   README or `.gitignore`.
2. Unzip `Catboost-model-for-AIH-prediction-from-DILI-clean.zip` (provided next to the repository folder).
3. On the new repository page, choose **uploading an existing file**.
4. Drag the **contents** of the unzipped `Catboost-model-for-AIH-prediction-from-DILI/` folder into the upload area
   (including hidden files such as `.github`, `.gitignore`, `.gitattributes`, and
   `.dockerignore`; on macOS press `Cmd+Shift+.` to show hidden files).
5. Commit with the message `Release v1.0.0`.
6. Open **Settings → Actions → General** and allow GitHub Actions.
7. Open the **Actions** tab and confirm the `CI` workflow passes.
8. Create a release: **Releases → Draft a new release → tag `v1.0.0`**, title
   `v1.0.0`, and attach `Catboost-model-for-AIH-prediction-from-DILI-v1.0.0.zip`.
9. The repository URL is already set to
   `https://github.com/849160181-design/Catboost-model-for-AIH-prediction-from-DILI`.
   If you rename or fork the repository, update it in `README.md`, `CITATION.cff`,
   and `zenodo/deposition_metadata.json`. The private manuscript inserts are not part
   of this repository.

> The web upload preserves file contents but **not** the Git commit history, tags, or
> executable bits. If you want the history and the `v1.0.0` tag preserved, use Option B.

## Option B — Git push (recommended)

### With the helper script

```bash
export GH_TOKEN='...'          # classic PAT with repo scope, or fine-grained
export GITHUB_REPO='849160181-design/Catboost-model-for-AIH-prediction-from-DILI'
export GITHUB_CREATE=1         # create the repository if it does not exist
./scripts/publish_github.sh
```

The script:

- initialises the repository if needed;
- commits the release;
- creates the GitHub repository (optional);
- pushes `main` and the `v1.0.0` tag using a one-shot credential helper (the token is
  not written to `.git/config`).

### Manually

```bash
git remote add origin https://github.com/849160181-design/Catboost-model-for-AIH-prediction-from-DILI.git
git push -u origin main
git push origin v1.0.0
```

If you have not created the tag yet:

```bash
git tag -a v1.0.0 -m "v1.0.0"
git push origin v1.0.0
```

## Option C — Clone from the bundle

A `Catboost-model-for-AIH-prediction-from-DILI-clean.bundle` file is provided next to the
repository folder. It contains the clean history and tag:

```bash
git clone Catboost-model-for-AIH-prediction-from-DILI-clean.bundle Catboost-model-for-AIH-prediction-from-DILI
cd Catboost-model-for-AIH-prediction-from-DILI
git remote set-url origin https://github.com/849160181-design/Catboost-model-for-AIH-prediction-from-DILI.git
git push -u origin main --tags
```

---

## Zenodo

### Web UI

1. Sign in at <https://zenodo.org>.
2. **New upload** → upload `zenodo/aih-catboost-v1.0.0.zip`.
3. Fill the metadata from `zenodo/deposition_metadata.json`:
   - title, authors (same order as the manuscript), description, keywords;
   - resource type: **Software**;
   - license: **MIT** (code) — mention CC BY 4.0 for data/docs in the description;
   - version `1.0.0`, publication date, language English;
   - related identifier: the GitHub URL.
4. Publish. Zenodo assigns the DOI.
5. Run:
   ```bash
   python3 scripts/finalize_doi.py --doi 10.5281/zenodo.XXXXXXX
   # if the private manuscript inserts are kept outside the repo:
   # python3 scripts/finalize_doi.py --doi 10.5281/zenodo.XXXXXXX \
   #   --manuscript-dir /path/to/private/manuscript
   python3 -m unittest discover -s tests -v
   ```
6. Commit the DOI update and re-tag if necessary:
   ```bash
   git add -A
   git commit -m "Add Zenodo DOI"
   git tag -a v1.0.0 -m "v1.0.0" --force
   git push origin main --tags --force
   ```

### API (one command)

Edit `zenodo/deposition_metadata.json` first (replace `[Authors]`; the GitHub URL is already set), then:

```bash
export ZENODO_TOKEN='...'      # deposit:write + deposit:actions
python3 zenodo/publish.py --finalize
```

`--finalize` publishes and writes the DOI into all seven locations. See
`zenodo/README.md` for the sandbox test and troubleshooting.

---

## Post-publication verification

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_repo_hygiene.py --strict-doi
git status
```

The strict hygiene check must report **no failures** and no placeholder DOI. Then:

- [ ] The GitHub repository is public and the CI workflow passes.
- [ ] The `v1.0.0` tag and release exist.
- [ ] The Zenodo record is public and the DOI resolves.
- [ ] If you maintain the private manuscript inserts, the DOI is identical in the Data
      sharing statement, Methods–Reproducibility, and reference 41.
- [ ] A colleague who did not build the project can run `./quickstart/run_demo.sh` from
      a fresh clone in under five minutes.
- [ ] No patient-level data, pathology image, medical record, manuscript text, or
      article-level result table is present in either the GitHub repository or the
      Zenodo archive.

## If something goes wrong

| Problem | Fix |
|---|---|
| GitHub Actions fails on `check_repo_hygiene.py` | Run it locally; it prints the exact failing file |
| `git push` asks for a password | Use a PAT as the password, or `scripts/publish_github.sh` |
| Zenodo rejects metadata | Check `creators` has a non-placeholder name and `upload_type` is `software` |
| DOI mismatch | Re-run `scripts/finalize_doi.py`; if using private inserts, pass `--manuscript-dir` |
| Web upload missed hidden files | Use `git archive`/Option B instead of drag-and-drop |

## Security

- Never commit `.env`, tokens, or `~/.config/dsh/*_token`.
- Do not upload the original study CSVs, images, or records. The repository's
  `.gitignore` and `scripts/check_repo_hygiene.py` are guardrails, not a substitute for
  checking before you upload.
- Zenodo publication is permanent. Test on `sandbox.zenodo.org` first if you are
  unsure.
