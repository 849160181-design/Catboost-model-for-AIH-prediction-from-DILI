#!/usr/bin/env python3
"""Create a Zenodo deposition, upload the repository archive, and publish it.

Prerequisites
-------------
1. A Zenodo account and a personal access token with ``deposit:write`` and
   ``deposit:actions``:
       https://zenodo.org/account/settings/applications/tokens/new/
2. Edit ``zenodo/deposition_metadata.json``: replace ``[Authors]``, the GitHub
   ``OWNER`` placeholder, and the title if needed.
3. Provide the token in one of these ways (never commit it):
       export ZENODO_TOKEN=...
       printf '%s' '...' > ~/.config/dsh/zenodo_token && chmod 600 ~/.config/dsh/zenodo_token

Usage
-----
    python3 zenodo/publish.py --dry-run
    python3 zenodo/publish.py                 # publish to production
    python3 zenodo/publish.py --no-publish    # upload and reserve, do not publish
    python3 zenodo/publish.py --sandbox       # test against sandbox.zenodo.org
    python3 zenodo/publish.py --finalize      # publish, then run scripts/finalize_doi.py

The script refuses to publish while the metadata still contains obvious
placeholders (``[Authors]``, ``OWNER``, ``XXXX``).  Use ``--allow-placeholders``
only for a sandbox smoke test.

Publication is irreversible.  To change files after publication, create a new
version of the deposition on Zenodo.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "zenodo" / "deposition_metadata.json"
ZIP_PATH = ROOT / "zenodo" / "aih-catboost-v1.0.0.zip"
ARCHIVE_ROOT = "aih-catboost-v1.0.0"
VERSION = "1.0.0"

PRODUCTION_API = "https://zenodo.org/api"
SANDBOX_API = "https://sandbox.zenodo.org/api"

EXCLUDE_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
EXCLUDE_PREFIXES = {"data/derived", "results", "manuscript"}
EXCLUDE_FILES = {
    "model/demo_retrained.cbm", "model/catboost_model.json",
    "RELEASE_NOTES.md", "ACCEPTANCE_TEST.md", ".DS_Store", ".env",
    "zenodo/aih-catboost-v1.0.0.zip",
    "zenodo/aih-catboost-v1.0.0.tar.gz",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".token"}


def read_token() -> str:
    token = os.environ.get("ZENODO_TOKEN", "").strip()
    if token:
        return token
    for candidate in (Path.home() / ".config" / "dsh" / "zenodo_token", Path.home() / ".zenodo_token"):
        if candidate.exists():
            value = candidate.read_text(encoding="utf-8").strip()
            if value:
                return value
    raise SystemExit(
        "No Zenodo token found. Set ZENODO_TOKEN or write it to "
        "~/.config/dsh/zenodo_token (see zenodo/README.md)."
    )


def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        raise SystemExit(f"missing metadata file: {METADATA_PATH}")
    payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if "metadata" not in payload:
        raise SystemExit("metadata JSON must contain a top-level 'metadata' object")
    return payload["metadata"]


def placeholder_hits(metadata: dict) -> list[str]:
    text = json.dumps(metadata, ensure_ascii=False)
    hits = []
    for token in ("[Authors]", "OWNER", "XXXX", "TODO", "[Year]", "[Journal]"):
        if token in text:
            hits.append(token)
    return hits


def build_zip() -> tuple[Path, int, int]:
    """Zip the repository, excluding VCS, generated, and oversized artifacts."""
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            rel_posix = rel.as_posix()
            if any(part in EXCLUDE_PARTS for part in rel.parts):
                continue
            if any(rel_posix == prefix or rel_posix.startswith(prefix + "/") for prefix in EXCLUDE_PREFIXES):
                continue
            if rel_posix in EXCLUDE_FILES or path.suffix.lower() in EXCLUDE_SUFFIXES:
                continue
            if path.stat().st_size > 20_000_000:
                print(f"  skipping large file: {rel_posix}")
                continue
            archive.write(path, arcname=f"{ARCHIVE_ROOT}/{rel_posix}")
            count += 1
    size = ZIP_PATH.stat().st_size
    return ZIP_PATH, count, size


def request(method: str, url: str, token: str, payload=None, raw: bytes | None = None,
            content_type: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    data = raw
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Zenodo API error {exc.code} for {method} {url}:\n{detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Cannot reach Zenodo at {url}: {exc}") from exc
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", action="store_true", help="use sandbox.zenodo.org")
    parser.add_argument("--no-publish", action="store_true", help="create and upload but do not publish")
    parser.add_argument("--finalize", action="store_true", help="run scripts/finalize_doi.py after publishing")
    parser.add_argument("--manuscript-dir", type=Path, default=None,
                        help="private manuscript folder to update together with the public DOI files")
    parser.add_argument("--dry-run", action="store_true", help="validate metadata and build the zip only")
    parser.add_argument("--allow-placeholders", action="store_true", help="do not refuse placeholder metadata (sandbox only)")
    parser.add_argument("--token", default=None, help="Zenodo token (prefer env/file; visible in shell history)")
    args = parser.parse_args()

    # Safety gate: never build an archive containing study data or images.
    hygiene = ROOT / "scripts" / "check_repo_hygiene.py"
    if hygiene.exists():
        result = subprocess.run([sys.executable, str(hygiene)], cwd=ROOT)
        if result.returncode != 0:
            raise SystemExit("repository hygiene check failed; refusing to build the Zenodo archive")

    metadata = load_metadata()
    hits = placeholder_hits(metadata)
    if hits:
        message = f"metadata still contains placeholders: {', '.join(hits)}"
        if args.allow_placeholders or args.dry_run:
            print(f"WARNING: {message}")
        else:
            raise SystemExit(
                f"{message}\nEdit zenodo/deposition_metadata.json before publishing. "
                "Use --allow-placeholders only for a sandbox smoke test."
            )

    zip_path, count, size = build_zip()
    print(f"archive: {zip_path} ({count} files, {size / 1024:.1f} KiB)")

    if args.dry_run:
        print("dry run only; no network calls made")
        print(json.dumps(metadata, indent=2, ensure_ascii=False)[:2000])
        return 0

    token = args.token or read_token()
    api = SANDBOX_API if args.sandbox else PRODUCTION_API
    if args.sandbox:
        print("using Zenodo SANDBOX; the resulting DOI is not a production DOI")

    print("creating deposition...")
    deposition = request("POST", f"{api}/deposit/depositions", token, payload={})
    links = deposition.get("links", {})
    bucket = links.get("bucket")
    self_link = links.get("self")
    html = links.get("html") or links.get("latest_html")
    if not bucket or not self_link:
        raise SystemExit(f"unexpected deposition response: {json.dumps(deposition)[:1000]}")
    print(f"deposition: {html or self_link}")

    print("uploading archive...")
    filename = zip_path.name
    request(
        "PUT",
        f"{bucket.rstrip('/')}/{filename}",
        token,
        raw=zip_path.read_bytes(),
        content_type="application/octet-stream",
    )

    print("setting metadata...")
    request("PUT", self_link, token, payload={"metadata": metadata})

    if args.no_publish:
        doi = deposition.get("doi", "")
        print(f"uploaded but not published. deposition id: {deposition.get('id')}")
        if doi:
            print(f"reserved DOI (may not resolve until published): {doi}")
        print("Publish from the Zenodo web UI when ready.")
        return 0

    print("publishing...")
    published = request("POST", f"{self_link}/actions/publish", token, payload={})
    doi = published.get("doi") or ""
    doi_url = published.get("doi_url") or (f"https://doi.org/{doi}" if doi else "")
    print("=" * 72)
    if doi:
        print(f"PUBLISHED DOI: {doi}")
        print(f"DOI URL:       {doi_url}")
    else:
        print("Published, but the API did not return a DOI. Check the deposition page:")
        print(html or self_link)
    print("=" * 72)

    if args.finalize and doi:
        print("updating manuscript DOI locations...")
        cmd = [sys.executable, str(ROOT / "scripts" / "finalize_doi.py"), "--doi", doi]
        if args.manuscript_dir:
            cmd.extend(["--manuscript-dir", str(args.manuscript_dir)])
        subprocess.run(cmd, check=True, cwd=ROOT)
        print("Next: run the test suite, commit the DOI update, and tag v1.0.0.")
    else:
        print("Next: python3 scripts/finalize_doi.py --doi " + (doi or "<DOI>"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
