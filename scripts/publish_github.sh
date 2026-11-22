#!/usr/bin/env bash
# Publish the repository to GitHub.
#
# Prerequisites:
#   export GH_TOKEN=...            # classic PAT with repo scope, or fine-grained
#                                  # Contents: read/write (+ Administration if creating)
#   export GITHUB_REPO=owner/repo
# Optional:
#   export GITHUB_CREATE=1         # create the repository if it does not exist
#   export GITHUB_PRIVATE=1        # create a private repository
#   export GITHUB_BRANCH=main
#
# The token is passed to git through a one-shot credential helper, not embedded
# in the remote URL or written to .git/config.
set -euo pipefail

: "${GH_TOKEN:?Set GH_TOKEN to a GitHub personal access token}"
: "${GITHUB_REPO:?Set GITHUB_REPO to owner/repo}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
BRANCH="${GITHUB_BRANCH:-main}"
TAG="${GITHUB_TAG:-v1.0.0}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

# Safety gate: refuse to push if study data, images, or documents are present.
if [ -f scripts/check_repo_hygiene.py ]; then
  python3 scripts/check_repo_hygiene.py
fi

if [ ! -d .git ]; then
  git init -q
  git symbolic-ref HEAD "refs/heads/${BRANCH}"
fi

if ! git config user.name >/dev/null; then
  git config user.name "${GIT_AUTHOR_NAME:-AIH CatBoost Release}"
fi
if ! git config user.email >/dev/null; then
  git config user.email "${GIT_AUTHOR_EMAIL:-release@example.invalid}"
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "Release ${TAG}: reproducible AIH CatBoost model and synthetic demo"
fi

# Create the repository if requested and it does not exist yet.
if ! git ls-remote "https://github.com/${GITHUB_REPO}.git" >/dev/null 2>&1; then
  if [ "${GITHUB_CREATE:-0}" != "1" ]; then
    echo "Repository https://github.com/${GITHUB_REPO} does not exist." >&2
    echo "Create it in the GitHub web UI, or re-run with GITHUB_CREATE=1." >&2
    exit 1
  fi
  echo "Creating https://github.com/${GITHUB_REPO} ..."
  PRIVATE="false"
  if [ "${GITHUB_PRIVATE:-0}" = "1" ]; then PRIVATE="true"; fi
  BODY="$(python3 - "$GITHUB_REPO" "$PRIVATE" <<'PY'
import json, sys
repo, private = sys.argv[1], sys.argv[2] == "true"
print(json.dumps({"name": repo.split("/")[-1], "private": private,
                  "description": "Reproducible AIH CatBoost model, analysis pipeline, and synthetic demo"}))
PY
)"
  HTTP_CODE="$(curl -sS -o /tmp/gh_create_repo.json -w '%{http_code}' \
    -X POST \
    -H "Authorization: Bearer ${GH_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/user/repos \
    -d "$BODY")"
  if [ "$HTTP_CODE" != "201" ]; then
    echo "GitHub repo creation failed (HTTP ${HTTP_CODE}):" >&2
    cat /tmp/gh_create_repo.json >&2
    exit 1
  fi
fi

git remote remove origin >/dev/null 2>&1 || true
git remote add origin "https://github.com/${GITHUB_REPO}.git"

echo "Pushing ${BRANCH} ..."
git -c credential.helper='!f() { echo username=x-access-token; echo "password=${GH_TOKEN}"; }; f' \
  push -u origin "${BRANCH}"

if ! git rev-parse "${TAG}" >/dev/null 2>&1; then
  git tag -a "${TAG}" -m "Release ${TAG}"
fi
git -c credential.helper='!f() { echo username=x-access-token; echo "password=${GH_TOKEN}"; }; f' \
  push origin "${TAG}"

echo "Repository: https://github.com/${GITHUB_REPO}"
echo "Tag:        ${TAG}"
echo "Next: enable the GitHub Actions workflow, then publish the Zenodo archive."
