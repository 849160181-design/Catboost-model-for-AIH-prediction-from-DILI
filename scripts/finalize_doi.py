#!/usr/bin/env python3
"""Replace the placeholder Zenodo DOI in public and private release locations.

After ``zenodo/publish.py`` prints the DOI, run:

    python3 scripts/finalize_doi.py --doi 10.5281/zenodo.1234567

By default the script updates the four public repository locations:

  * README.md
  * CITATION.cff
  * model/model_card.md
  * zenodo/deposition_metadata.json

The three manuscript locations are deliberately **not** part of this public
repository.  If you keep them in a private folder, pass it explicitly:

    python3 scripts/finalize_doi.py \
      --doi 10.5281/zenodo.1234567 \
      --manuscript-dir /path/to/private/manuscript

The script then also updates and verifies:

  * <manuscript-dir>/data_sharing_statement.md
  * <manuscript-dir>/methods_reproducibility.md
  * <manuscript-dir>/references.md

It refuses placeholders and malformed DOIs.  Use ``--dry-run`` to preview.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "10.5281/zenodo.XXXXXXX"
PUBLIC_FILES = [
    ROOT / "README.md",
    ROOT / "CITATION.cff",
    ROOT / "model" / "model_card.md",
    ROOT / "zenodo" / "deposition_metadata.json",
]
MANUSCRIPT_NAMES = (
    "data_sharing_statement.md",
    "methods_reproducibility.md",
    "references.md",
)
DOI_RE = re.compile(r"^10\.(?:5281|5072)/zenodo\.[0-9]+$")


def validate(doi: str) -> str:
    doi = doi.strip()
    if "XXXX" in doi.upper() or doi == PLACEHOLDER:
        raise SystemExit("refusing to write a placeholder DOI; pass the real Zenodo DOI")
    if not DOI_RE.match(doi):
        raise SystemExit(
            f"invalid DOI: {doi!r}. Expected a Zenodo DOI such as "
            "10.5281/zenodo.1234567 (production) or 10.5072/zenodo.123456 (sandbox)."
        )
    return doi


def label(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def replace_in(path: Path, doi: str, dry_run: bool) -> tuple[int, str]:
    if not path.exists():
        return 0, "MISSING"
    text = path.read_text(encoding="utf-8")
    count = text.count(PLACEHOLDER)
    if count == 0:
        return 0, "OK" if doi in text else "NO_PLACEHOLDER"
    if not dry_run:
        path.write_text(text.replace(PLACEHOLDER, doi), encoding="utf-8")
    return count, "UPDATE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doi", required=True, help="final Zenodo DOI, e.g. 10.5281/zenodo.1234567")
    parser.add_argument("--manuscript-dir", type=Path, default=None,
                        help="private folder containing the three manuscript insert files")
    parser.add_argument("--dry-run", action="store_true", help="show changes without writing")
    args = parser.parse_args()
    doi = validate(args.doi)

    files = list(PUBLIC_FILES)
    manuscript_files: list[Path] = []
    if args.manuscript_dir is not None:
        manuscript_files = [args.manuscript_dir / name for name in MANUSCRIPT_NAMES]
        files.extend(manuscript_files)

    total = 0
    for path in files:
        count, status = replace_in(path, doi, args.dry_run)
        total += count
        prefix = "WOULD UPDATE" if (args.dry_run and status == "UPDATE") else status
        print(f"  {prefix:12s} {label(path)}" + (f" ({count} occurrence(s))" if count else ""))

    missing = [label(p) for p in manuscript_files if not p.exists()]
    if missing:
        print("\nERROR: missing private manuscript file(s): " + ", ".join(missing))
        return 1

    if manuscript_files:
        bad = []
        for path in manuscript_files:
            text = path.read_text(encoding="utf-8")
            if args.dry_run:
                if PLACEHOLDER not in text and doi not in text:
                    bad.append(label(path))
            elif doi not in text:
                bad.append(label(path))
        if bad:
            print("\nERROR: the DOI/placeholder is missing from: " + ", ".join(bad))
            return 1
        print("\nPrivate manuscript locations verified: Data sharing, Methods-Reproducibility, reference 41.")

    print(f"\n{total} placeholder occurrence(s) {'would be ' if args.dry_run else ''}replaced with {doi}")
    print("Public repository locations updated. The private manuscript folder is optional and was "
          + ("processed." if manuscript_files else "not provided."))
    if not args.dry_run:
        print("Next: run `python3 -m unittest discover -s tests -v`, commit, and tag the release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
