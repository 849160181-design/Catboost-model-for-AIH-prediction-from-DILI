#!/usr/bin/env python3
"""Five-minute, dependency-free synthetic performance demo.

This is the acceptance-test entry point:

    git clone <repo>
    cd <repo>
    ./quickstart/run_demo.sh

It loads the locked model through the dependency-free scorer
(``model/catboost_model_pure.py``), scores the synthetic cohort, and writes
a performance table (AUC, 95% CI, and operating characteristics) to ``results/``.

No R, CatBoost, NumPy, pandas, or network access is required.  The synthetic
cohort is a software-verification fixture, not a validation cohort.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic_cohort.csv"
MODEL = ROOT / "model" / "catboost_model_pure.py"
RESULTS = ROOT / "results"

REQUIRED_COLUMNS = ("sample_id", "PAS_Macrophages", "MUM1", "Group", "split")
SPLITS = ("train", "internal_test", "external_test")
CI_LEVEL = 0.95
N_BOOT = 2000
BOOT_SEED = 20240501


def load_model():
    spec = importlib.util.spec_from_file_location("catboost_model_pure", MODEL)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import model scorer: {MODEL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_cohort(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"missing data file: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"{path.name}: missing columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise SystemExit(f"{path.name}: no data rows")
    return rows


def validate(rows: list[dict[str, str]]) -> None:
    seen: set[str] = set()
    for lineno, row in enumerate(rows, start=2):
        sid = (row.get("sample_id") or "").strip()
        if not sid:
            raise SystemExit(f"line {lineno}: empty sample_id")
        if sid in seen:
            raise SystemExit(f"line {lineno}: duplicate sample_id {sid!r}")
        seen.add(sid)
        if (row.get("split") or "") not in SPLITS:
            raise SystemExit(f"line {lineno}: split must be one of {SPLITS}")
        if (row.get("Group") or "") not in {"0", "1"}:
            raise SystemExit(f"line {lineno}: Group must be 0 or 1")
        if (row.get("PAS_Macrophages") or "") not in {"0", "1", "2"}:
            raise SystemExit(f"line {lineno}: PAS_Macrophages must be 0, 1, or 2")
        try:
            mum1 = float(row.get("MUM1") or "")
        except ValueError:
            raise SystemExit(f"line {lineno}: MUM1 is not numeric") from None
        if not math.isfinite(mum1) or mum1 <= 0:
            raise SystemExit(f"line {lineno}: MUM1 must be a positive finite number")
    for split in SPLITS:
        subset = [r for r in rows if r["split"] == split]
        if not subset:
            raise SystemExit(f"no rows for split {split!r}")
        labels = {int(r["Group"]) for r in subset}
        if labels != {0, 1}:
            raise SystemExit(f"split {split!r} must contain both classes")


def auc_score(y: list[int], p: list[float]) -> float:
    """Mann-Whitney AUC with mid-ranks for ties."""
    n1 = sum(y)
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        raise ValueError("AUC is undefined when only one class is present")
    pairs = sorted(zip(p, y))
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = rank
        i = j + 1
    rank_sum = sum(ranks[k] for k in range(len(pairs)) if pairs[k][1] == 1)
    return (rank_sum - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def bootstrap_ci(y: list[int], p: list[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED):
    rng = random.Random(seed)
    n = len(y)
    values: list[float] = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        yy = [y[i] for i in idx]
        if sum(yy) in (0, n):
            continue
        values.append(auc_score(yy, [p[i] for i in idx]))
    if not values:
        return float("nan"), float("nan")
    values.sort()
    alpha = 1.0 - CI_LEVEL
    lo = values[int(math.floor((alpha / 2.0) * (len(values) - 1)))]
    hi = values[int(math.ceil((1.0 - alpha / 2.0) * (len(values) - 1)))]
    return lo, hi


def operating_metrics(y: list[int], p: list[float], threshold: float) -> dict[str, float]:
    pred = [1 if value >= threshold else 0 for value in p]
    tp = sum(1 for a, b in zip(pred, y) if a == 1 and b == 1)
    tn = sum(1 for a, b in zip(pred, y) if a == 0 and b == 0)
    fp = sum(1 for a, b in zip(pred, y) if a == 1 and b == 0)
    fn = sum(1 for a, b in zip(pred, y) if a == 0 and b == 1)
    sens = tp / (tp + fn) if tp + fn else float("nan")
    spec = tn / (tn + fp) if tn + fp else float("nan")
    acc = (tp + tn) / len(y)
    ppv = tp / (tp + fp) if tp + fp else float("nan")
    npv = tn / (tn + fn) if tn + fn else float("nan")
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else float("nan")
    return {
        "sensitivity": sens,
        "specificity": spec,
        "accuracy": acc,
        "ppv": ppv,
        "npv": npv,
        "f1": f1,
        "youden": sens + spec - 1.0,
    }


def youden_threshold(y: list[int], p: list[float]) -> float:
    """Threshold that maximises sensitivity + specificity - 1.

    The optimum is a range whenever no observation falls between two scores.
    We report the midpoint of that range, which matches pROC's ``coords(...,
    "best", best.method = "youden")`` convention and keeps the R and Python
    outputs aligned.
    """
    candidates = sorted(set(p))
    best_j = -math.inf
    best_i = 0
    for i, t in enumerate(candidates):
        m = operating_metrics(y, p, t)
        if m["youden"] > best_j:
            best_j, best_i = m["youden"], i
    if best_i == 0:
        return candidates[0]
    return (candidates[best_i - 1] + candidates[best_i]) / 2.0


def roc_points(y: list[int], p: list[float]) -> list[tuple[float, float, float]]:
    """Return (threshold, fpr, tpr) by sweeping unique scores from high to low."""
    thresholds = sorted(set(p), reverse=True)
    points = [(math.inf, 0.0, 0.0)]
    for t in thresholds:
        pred = [1 if value >= t else 0 for value in p]
        tp = sum(1 for a, b in zip(pred, y) if a == 1 and b == 1)
        fp = sum(1 for a, b in zip(pred, y) if a == 1 and b == 0)
        tpr = tp / sum(y)
        fpr = fp / (len(y) - sum(y))
        points.append((t, fpr, tpr))
    return points


def fmt(value: float, digits: int = 3) -> str:
    if isinstance(value, float) and math.isnan(value):
        return "NA"
    return f"{value:.{digits}f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--outdir", type=Path, default=RESULTS)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    rows = read_cohort(args.data)
    validate(rows)
    model = load_model()

    by_split: dict[str, list[dict[str, str]]] = {s: [r for r in rows if r["split"] == s] for s in SPLITS}
    scores = {
        r["sample_id"]: model.predict_proba(r["PAS_Macrophages"], r["MUM1"]) for r in rows
    }

    train_y = [int(r["Group"]) for r in by_split["train"]]
    train_p = [scores[r["sample_id"]] for r in by_split["train"]]
    youden = youden_threshold(train_y, train_p)

    table: list[dict[str, object]] = []
    roc_rows: list[dict[str, object]] = []
    for split in SPLITS:
        y = [int(r["Group"]) for r in by_split[split]]
        p = [scores[r["sample_id"]] for r in by_split[split]]
        auc = auc_score(y, p)
        lo, hi = bootstrap_ci(y, p)
        metrics = operating_metrics(y, p, 0.5)
        table.append(
            {
                "cohort": split,
                "n": len(y),
                "events": sum(y),
                "auc": auc,
                "ci_lower": lo,
                "ci_upper": hi,
                "threshold": 0.5,
                "sensitivity": metrics["sensitivity"],
                "specificity": metrics["specificity"],
                "accuracy": metrics["accuracy"],
                "ppv": metrics["ppv"],
                "npv": metrics["npv"],
                "f1": metrics["f1"],
                "youden": metrics["youden"],
                "ci_method": f"bootstrap_percentile_{N_BOOT}",
            }
        )
        for t, fpr, tpr in roc_points(y, p):
            roc_rows.append({"cohort": split, "threshold": t, "fpr": fpr, "tpr": tpr})

    # Youden sensitivity analysis (training-derived threshold applied unchanged).
    youden_table: list[dict[str, object]] = []
    for split in SPLITS:
        y = [int(r["Group"]) for r in by_split[split]]
        p = [scores[r["sample_id"]] for r in by_split[split]]
        metrics = operating_metrics(y, p, youden)
        youden_table.append(
            {
                "cohort": split,
                "threshold": youden,
                "sensitivity": metrics["sensitivity"],
                "specificity": metrics["specificity"],
                "accuracy": metrics["accuracy"],
                "ppv": metrics["ppv"],
                "npv": metrics["npv"],
                "f1": metrics["f1"],
                "youden": metrics["youden"],
            }
        )

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "figures").mkdir(exist_ok=True)

    table_fields = list(table[0].keys())
    with (outdir / "performance_demo.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=table_fields, lineterminator="\n")
        writer.writeheader()
        for row in table:
            writer.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()})

    with (outdir / "youden_demo.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(youden_table[0].keys()), lineterminator="\n")
        writer.writeheader()
        for row in youden_table:
            writer.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()})

    with (outdir / "roc_points_demo.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["cohort", "threshold", "fpr", "tpr"], lineterminator="\n")
        writer.writeheader()
        for row in roc_rows:
            writer.writerow(
                {
                    "cohort": row["cohort"],
                    "threshold": "" if math.isinf(row["threshold"]) else f"{row['threshold']:.6f}",
                    "fpr": f"{row['fpr']:.6f}",
                    "tpr": f"{row['tpr']:.6f}",
                }
            )

    with (outdir / "predictions_demo.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sample_id", "split", "PAS_Macrophages", "MUM1", "Group", "predicted_probability"],
            lineterminator="\n",
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "sample_id": r["sample_id"],
                    "split": r["split"],
                    "PAS_Macrophages": r["PAS_Macrophages"],
                    "MUM1": r["MUM1"],
                    "Group": r["Group"],
                    "predicted_probability": f"{scores[r['sample_id']]:.6f}",
                }
            )

    lines = [
        "# Synthetic performance demo",
        "",
        "> **SYNTHETIC DEMO — NOT PATIENT DATA AND NOT FOR DIAGNOSIS.**  ",
        "> Generated by `quickstart/run_demo.py` from `data/synthetic_cohort.csv`.",
        "> The data are synthetic; the numbers below verify the software path only.",
        "> Do not cite them as validation results.",
        "",
        "| Cohort | n | Events | AUC (95% CI) | Sensitivity | Specificity | Accuracy | PPV | NPV | F1 |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {"train": "Training", "internal_test": "Internal test", "external_test": "External test"}
    for row in table:
        lines.append(
            "| {cohort} | {n} | {events} | {auc} ({lo}–{hi}) | {sens} | {spec} | {acc} | {ppv} | {npv} | {f1} |".format(
                cohort=labels[row["cohort"]],
                n=row["n"],
                events=row["events"],
                auc=fmt(row["auc"]),
                lo=fmt(row["ci_lower"]),
                hi=fmt(row["ci_upper"]),
                sens=fmt(row["sensitivity"]),
                spec=fmt(row["specificity"]),
                acc=fmt(row["accuracy"]),
                ppv=fmt(row["ppv"]),
                npv=fmt(row["npv"]),
                f1=fmt(row["f1"]),
            )
        )
    lines += [
        "",
        "Operating point: threshold = 0.50.  AUC 95% CI: percentile bootstrap "
        f"({N_BOOT} resamples, seed {BOOT_SEED}).",
        "",
        "The internal-test row uses the cohort that was CatBoost's `test_pool` during",
        "model selection; treat it as selection-optimistic.  The external-test row is",
        "the primary held-out estimate.  No performance result table is stored in",
        "this repository.",
        "",
        f"Training-derived Youden threshold: **{youden:.3f}**.  "
        "See `results/youden_demo.csv` for the sensitivity analysis.",
        "",
    ]
    (outdir / "performance_demo.md").write_text("\n".join(lines), encoding="utf-8")

    if not args.quiet:
        print("=" * 72)
        print("SYNTHETIC DEMO (not patient data; not for diagnosis)")
        print("=" * 72)
        print(f"{'Cohort':15s} {'n':>4s} {'Events':>7s} {'AUC (95% CI)':>20s} {'Sens':>6s} {'Spec':>6s}")
        for row in table:
            print(
                f"{labels[row['cohort']]:15s} {row['n']:4d} {row['events']:7d} "
                f"{fmt(row['auc'])} ({fmt(row['ci_lower'])}–{fmt(row['ci_upper'])}) "
                f"{fmt(row['sensitivity']):>6s} {fmt(row['specificity']):>6s}"
            )
        print("-" * 72)
        print("Synthetic demo only: these are not patient data and not for diagnosis.")
        print(f"Youden threshold (training): {youden:.3f}")
        print(f"Wrote: {outdir/'performance_demo.csv'}")
        print(f"Wrote: {outdir/'performance_demo.md'}")
        print("=" * 72)
        print("If you see an AUC above, the 5-minute acceptance test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
