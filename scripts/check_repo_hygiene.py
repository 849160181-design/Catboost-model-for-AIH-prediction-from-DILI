#!/usr/bin/env python3
"""Repository hygiene and release-readiness checks.

Run locally or in CI:

    python3 scripts/check_repo_hygiene.py
    python3 scripts/check_repo_hygiene.py --strict-doi

Checks:
  * forbidden study-data filenames are absent;
  * no pathology-image or document attachments are committed;
  * no GSE/GSM accession strings;
  * no file larger than 5 MB;
  * the locked model's SHA-256 matches the manifest;
  * the synthetic data schema matches data_dictionary.csv;
  * no private manuscript/ or results/ files are tracked;
  * the same DOI appears in the four public repository locations;
  * --strict-doi additionally rejects the placeholder DOI.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {
    "train_data.csv",
    "test_data.csv",
    "external_test_data.csv",
    "code.R",
}
FORBIDDEN_SUFFIXES = {
    ".svs", ".ndpi", ".scn", ".czi", ".nd2", ".lif", ".mrxs",
    ".tif", ".tiff", ".dcm", ".docx", ".pdf",
}
ALLOWED_BINARY_DIR = ROOT / "results" / "figures"
TEXT_SUFFIXES = {
    ".md", ".csv", ".py", ".R", ".r", ".ijm", ".yml", ".yaml",
    ".json", ".cff", ".txt",
}
DOI_FILES = [
    ROOT / "README.md",
    ROOT / "CITATION.cff",
    ROOT / "model" / "model_card.md",
    ROOT / "zenodo" / "deposition_metadata.json",
]
DOI_RE = re.compile(r"10\.5281/zenodo\.[0-9A-Za-z]+")
PLACEHOLDER = "10.5281/zenodo.XXXXXXX"
MAX_BYTES = 5_000_000


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.checks = 0

    def ok(self, message: str) -> None:
        self.checks += 1
        print(f"  PASS  {message}")

    def fail(self, message: str) -> None:
        self.checks += 1
        self.failures.append(message)
        print(f"  FAIL  {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"  WARN  {message}")


def make_report(strict_doi: bool = False) -> tuple[Report, dict]:
    report = Report()
    files = [
        p for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts
    ]

    print("\n[1] Forbidden study-data filenames")
    bad = [p for p in files if p.name in FORBIDDEN_NAMES]
    report.fail(f"forbidden study files: {bad}") if bad else report.ok("no train/test/external study CSVs or legacy code.R")

    print("\n[2] Pathology images and document attachments")
    bad = []
    for p in files:
        if p.suffix.lower() not in FORBIDDEN_SUFFIXES:
            continue
        if ALLOWED_BINARY_DIR in p.parents:
            continue
        bad.append(p.relative_to(ROOT))
    report.fail(f"forbidden attachments: {bad}") if bad else report.ok("no pathology images, PDFs, or Office documents outside generated figures")

    print("\n[3] Study accession strings")
    pattern = re.compile(r"GSE\d{4,}|GSM\d{4,}")
    hits = []
    for p in files:
        if p.suffix.lower() in TEXT_SUFFIXES:
            if pattern.search(p.read_text(encoding="utf-8", errors="ignore")):
                hits.append(p.relative_to(ROOT))
    report.fail(f"accession strings found: {hits}") if hits else report.ok("no GSE/GSM identifiers")

    print("\n[4] File sizes")
    large = [p.relative_to(ROOT) for p in files if p.stat().st_size > MAX_BYTES]
    report.fail(f"files over 5 MB: {large}") if large else report.ok("all files under 5 MB")

    print("\n[5] Locked-model checksum")
    manifest_path = ROOT / "model" / "model_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest["artifact_sha256"]
        actual = hashlib.sha256((ROOT / "model" / "catboost_model.cbm").read_bytes()).hexdigest()
        if expected == actual:
            report.ok(f"catboost_model.cbm SHA-256 matches ({actual[:12]}…)")
        else:
            report.fail(f"checksum mismatch: manifest={expected}, actual={actual}")
    except Exception as exc:  # noqa: BLE001 - report, do not crash the release check
        report.fail(f"could not verify model manifest: {exc}")

    print("\n[6] Synthetic-data schema")
    try:
        with (ROOT / "data_dictionary.csv").open(newline="", encoding="utf-8") as handle:
            dictionary_fields = {row["field"] for row in csv.DictReader(handle)}
        with (ROOT / "data" / "synthetic_cohort.csv").open(newline="", encoding="utf-8") as handle:
            data_fields = set(csv.DictReader(handle).fieldnames or [])
        if dictionary_fields == data_fields and len(dictionary_fields) > 0:
            report.ok(f"data columns match the dictionary ({sorted(dictionary_fields)})")
        else:
            report.fail(f"schema mismatch: dictionary={sorted(dictionary_fields)}, data={sorted(data_fields)}")
    except Exception as exc:  # noqa: BLE001
        report.fail(f"could not check schema: {exc}")

    print("\n[7] Private manuscript/results are not tracked")
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        bad = [f for f in tracked if f.startswith(("manuscript/", "results/"))]
        if bad:
            report.fail(f"private manuscript/results are tracked: {bad}")
        else:
            report.ok("no manuscript/ or results/ files are tracked")
    except Exception as exc:  # noqa: BLE001
        report.warn(f"could not inspect git index (not a Git checkout?): {exc}")

    print("\n[8] DOI consistency")
    dois: dict[str, str] = {}
    for path in DOI_FILES:
        if not path.exists():
            report.fail(f"missing DOI file: {path.relative_to(ROOT)}")
            continue
        found = DOI_RE.findall(path.read_text(encoding="utf-8"))
        if not found:
            report.fail(f"no Zenodo DOI in {path.relative_to(ROOT)}")
        else:
            dois[path.relative_to(ROOT).as_posix()] = found[0]
    unique = set(dois.values())
    if len(unique) == 1:
        doi = next(iter(unique))
        if doi == PLACEHOLDER:
            report.warn("DOI is still the placeholder 10.5281/zenodo.XXXXXXX; run zenodo/publish.py then scripts/finalize_doi.py")
        else:
            report.ok(f"all four public locations carry the same DOI ({doi})")
    elif len(unique) > 1:
        report.fail(f"DOI mismatch across files: {dois}")
    else:
        report.fail("no DOI found in any location")

    if strict_doi:
        print("\n[9] Strict DOI (no placeholder)")
        if any(v == PLACEHOLDER for v in unique):
            report.fail("strict DOI requested but the placeholder is still present")
        else:
            report.ok("no placeholder DOI")

    print("\n" + "=" * 72)
    print(f"checks: {report.checks}  failures: {len(report.failures)}  warnings: {len(report.warnings)}")
    for failure in report.failures:
        print(f"  FAIL: {failure}")
    for warning in report.warnings:
        print(f"  WARN: {warning}")
    print("=" * 72)
    return report, dois


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-doi", action="store_true", help="fail if the placeholder DOI is present")
    args = parser.parse_args()
    report, _ = make_report(strict_doi=args.strict_doi)
    sys.exit(1 if report.failures else 0)
