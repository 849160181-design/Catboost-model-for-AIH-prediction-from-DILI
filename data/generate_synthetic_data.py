#!/usr/bin/env python3
"""Generate the synthetic demonstrator cohort used by this repository.

Why this file exists
--------------------
Patient-level data are not redistributed.  Users still need a dataset that
exercises the *entire* scoring and evaluation pipeline.  This script therefore
generates a small, fully synthetic cohort whose columns match
``data_dictionary.csv`` exactly.

Generative model (transparent by design)
----------------------------------------
For every synthetic participant:

1. Disease status is drawn with probability 0.5:
       Group ~ Bernoulli(0.5)
2. MUM1-positive cells per portal tract are drawn from a group-specific
   log-normal distribution and clipped to [1, 700]:
       control : MUM1 ~ LogNormal(mu0, sd0)
       case    : MUM1 ~ LogNormal(mu1, sd1)
3. PAS-positive macrophages are drawn from a group-specific three-level
   categorical distribution:
       control : P(0, 1, 2) = (0.55, 0.35, 0.10)
       case    : P(0, 1, 2) = (0.35, 0.40, 0.25)

The parameters and random seeds below were chosen **once** so that the locked
model (``model/catboost_model.cbm``) returns a realistic AUC range.  This makes
the fixture useful as a software regression test.  It is *not* a validation
cohort, it contains no patient data, and it must never be used to estimate
performance, prevalence, or subgroup effects.

No patient-level data, pathology image, or medical record is used here.
All identifiers are synthetic (``SYN-T-001``, ``SYN-V-001``, ``SYN-E-001``).

Usage
-----
    python3 data/generate_synthetic_data.py
    python3 data/generate_synthetic_data.py --out data/synthetic_cohort.csv

The output is deterministic for a given Python version and the fixed seeds.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

# Fixed design.  Changing these values changes the synthetic demo AUCs.
DESIGN = (
    # split,           n,  seed, mu0,  mu1,  sd0, sd1, id prefix
    ("train",         80, 384, 2.00, 4.20, 0.90, 1.10, "SYN-T"),
    ("internal_test", 50, 326, 2.00, 4.20, 0.90, 1.10, "SYN-V"),
    ("external_test", 50, 282, 2.00, 4.25, 0.90, 1.05, "SYN-E"),
)

PAS_CONTROL = (0.55, 0.35, 0.10)
PAS_CASE = (0.35, 0.40, 0.25)
LEVELS = (0, 1, 2)


def draw_mum1(rng: random.Random, mu: float, sd: float) -> float:
    """Draw one clipped, log-normal MUM1 value."""
    value = math.exp(rng.gauss(mu, sd))
    return round(max(1.0, min(700.0, value)), 2)


def draw_pas(rng: random.Random, group: int) -> int:
    """Draw one PAS category (0/1/2) conditional on group."""
    weights = PAS_CASE if group == 1 else PAS_CONTROL
    return rng.choices(LEVELS, weights=weights, k=1)[0]


def generate() -> list[dict[str, object]]:
    """Return all synthetic rows in a stable order."""
    rows: list[dict[str, object]] = []
    for split, n, seed, mu0, mu1, sd0, sd1, prefix in DESIGN:
        rng = random.Random(seed)
        for i in range(1, n + 1):
            group = 1 if rng.random() < 0.5 else 0
            mum1 = draw_mum1(rng, mu1 if group else mu0, sd1 if group else sd0)
            pas = draw_pas(rng, group)
            rows.append(
                {
                    "sample_id": f"{prefix}-{i:03d}",
                    "PAS_Macrophages": pas,
                    "MUM1": f"{mum1:.2f}",
                    "Group": group,
                    "split": split,
                }
            )
    return rows


FIELDS = ("sample_id", "PAS_Macrophages", "MUM1", "Group", "split")


def write_csv(rows: list[dict[str, object]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: list[dict[str, object]]) -> None:
    print(f"rows: {len(rows)}")
    for split, *_ in DESIGN:
        subset = [r for r in rows if r["split"] == split]
        events = sum(int(r["Group"]) for r in subset)
        print(
            f"  {split:13s} n={len(subset):3d} events={events:3d} "
            f"controls={len(subset) - events:3d}"
        )
    pas_counts = {level: sum(1 for r in rows if r["PAS_Macrophages"] == level) for level in LEVELS}
    print(f"  PAS counts: {pas_counts}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "synthetic_cohort.csv",
        help="output CSV (default: data/synthetic_cohort.csv)",
    )
    args = parser.parse_args()

    rows = generate()
    write_csv(rows, args.out)
    summarise(rows)
    print(f"written: {args.out}")


if __name__ == "__main__":
    main()
