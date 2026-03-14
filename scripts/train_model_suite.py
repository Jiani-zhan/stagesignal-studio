#!/usr/bin/env python3
"""Train deterministic model suite from Broadway Revenue source labels.

This script uses only Python standard library components.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

try:
    from build_demo_data import XlsxWorkbook, excel_serial_to_date, parse_number
except ModuleNotFoundError:
    from scripts.build_demo_data import XlsxWorkbook, excel_serial_to_date, parse_number


SEED = 20260314
TRAIN_FRACTION = 0.8
R2_THRESHOLD = 0.8
ACCURACY_THRESHOLD = 0.8

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DATA = ROOT / "assets" / "data"
SOURCE_XLSX = ROOT / "Final presentation" / "Data Collection & Visualization.xlsx"
SOURCE_SHEET = "Broadway Revenue"


@dataclass
class WeeklyRecord:
    row_id: int
    week_serial: float
    week_date: str
    this_week_gross: float
    last_week_gross: float
    diff_dollars: float
    average_ticket: float
    top_ticket: float
    seats_sold: float
    total_seats: float
    this_week_pct: float
    last_week_pct: float
    diff_pct: float


def ensure_output_dir() -> None:
    ASSETS_DATA.mkdir(parents=True, exist_ok=True)


def load_weekly_records() -> List[WeeklyRecord]:
    wb = XlsxWorkbook(SOURCE_XLSX)
    try:
        rows = wb.read_rows(SOURCE_SHEET)
    finally:
        wb.close()

    records: List[WeeklyRecord] = []
    for idx, row in enumerate(rows[2:], start=2):
        if len(row) < 15:
            continue
        parsed = {
            "week_serial": parse_number(row[0]),
            "this_week_gross": parse_number(row[2]),
            "last_week_gross": parse_number(row[3]),
            "diff_dollars": parse_number(row[4]),
            "average_ticket": parse_number(row[7]),
            "top_ticket": parse_number(row[8]),
            "seats_sold": parse_number(row[9]),
            "total_seats": parse_number(row[10]),
            "this_week_pct": parse_number(row[12]),
            "last_week_pct": parse_number(row[13]),
            "diff_pct": parse_number(row[14]),
        }
        if any(value is None for value in parsed.values()):
            continue

        week_serial = float(parsed["week_serial"])
        records.append(
            WeeklyRecord(
                row_id=idx,
                week_serial=week_serial,
                week_date=excel_serial_to_date(week_serial).isoformat(),
                this_week_gross=float(parsed["this_week_gross"]),
                last_week_gross=float(parsed["last_week_gross"]),
                diff_dollars=float(parsed["diff_dollars"]),
                average_ticket=float(parsed["average_ticket"]),
                top_ticket=float(parsed["top_ticket"]),
                seats_sold=float(parsed["seats_sold"]),
                total_seats=float(parsed["total_seats"]),
                this_week_pct=float(parsed["this_week_pct"]),
                last_week_pct=float(parsed["last_week_pct"]),
                diff_pct=float(parsed["diff_pct"]),
            )
        )
    if not records:
        raise RuntimeError("No valid weekly records were parsed from source workbook.")
    return records


def deterministic_split(
    size: int, train_fraction: float, seed: int
) -> tuple[List[int], List[int]]:
    indices = list(range(size))
    rng = random.Random(seed)
    rng.shuffle(indices)
    train_size = max(1, min(size - 1, int(size * train_fraction)))
    return indices[:train_size], indices[train_size:]


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: Sequence[float]) -> float:
    if not values:
        return 1.0
    mu = mean(values)
    variance = sum((v - mu) ** 2 for v in values) / len(values)
    std = math.sqrt(variance)
    return std if std > 1e-12 else 1.0


def fit_standardizer(matrix: List[List[float]]) -> tuple[List[float], List[float]]:
    cols = len(matrix[0])
    means: List[float] = []
    stds: List[float] = []
    for c in range(cols):
        col = [row[c] for row in matrix]
        means.append(mean(col))
        stds.append(stdev(col))
    return means, stds


def standardize(
    matrix: List[List[float]], means: Sequence[float], stds: Sequence[float]
) -> List[List[float]]:
    out: List[List[float]] = []
    for row in matrix:
        out.append([(row[i] - means[i]) / stds[i] for i in range(len(row))])
    return out


def with_intercept(matrix: List[List[float]]) -> List[List[float]]:
    return [[1.0] + row for row in matrix]


def solve_linear_system(a: List[List[float]], b: List[float]) -> List[float]:
    n = len(a)
    aug = [a[i][:] + [b[i]] for i in range(n)]

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot_row][col]) < 1e-12:
            raise RuntimeError(
                "Linear system is singular; adjust features or regularization."
            )
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

        pivot = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= pivot

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]

    return [aug[i][n] for i in range(n)]


def fit_linear_regression(
    x_train: List[List[float]], y_train: List[float], ridge: float = 1.0
) -> List[float]:
    cols = len(x_train[0])
    xtx = [[0.0 for _ in range(cols)] for _ in range(cols)]
    xty = [0.0 for _ in range(cols)]

    for row, target in zip(x_train, y_train):
        for i in range(cols):
            xty[i] += row[i] * target
            for j in range(cols):
                xtx[i][j] += row[i] * row[j]

    for i in range(cols):
        xtx[i][i] += ridge

    return solve_linear_system(xtx, xty)


def predict_linear(weights: Sequence[float], x: List[List[float]]) -> List[float]:
    return [sum(w * xi for w, xi in zip(weights, row)) for row in x]


def r2_score(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    y_bar = mean(y_true)
    ss_tot = sum((y - y_bar) ** 2 for y in y_true)
    ss_res = sum((y - p) ** 2 for y, p in zip(y_true, y_pred))
    if ss_tot <= 1e-12:
        return 0.0
    return 1.0 - (ss_res / ss_tot)


def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    return mean([abs(y - p) for y, p in zip(y_true, y_pred)])


def rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    return math.sqrt(mean([(y - p) ** 2 for y, p in zip(y_true, y_pred)]))


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def fit_logistic_regression(
    x_train: List[List[float]],
    y_train: List[int],
    learning_rate: float = 0.05,
    iterations: int = 8000,
    l2: float = 1e-4,
) -> List[float]:
    cols = len(x_train[0])
    w = [0.0 for _ in range(cols)]
    n = float(len(x_train))

    for _ in range(iterations):
        grads = [0.0 for _ in range(cols)]
        for row, target in zip(x_train, y_train):
            z = sum(wj * xj for wj, xj in zip(w, row))
            p = sigmoid(z)
            err = p - float(target)
            for i in range(cols):
                grads[i] += err * row[i]

        for i in range(cols):
            reg_term = l2 * w[i] if i > 0 else 0.0
            w[i] -= learning_rate * ((grads[i] / n) + reg_term)
    return w


def predict_logistic(weights: Sequence[float], x: List[List[float]]) -> List[float]:
    probs: List[float] = []
    for row in x:
        z = sum(w * xi for w, xi in zip(weights, row))
        probs.append(sigmoid(z))
    return probs


def classification_metrics(
    y_true: Sequence[int], y_pred: Sequence[int]
) -> Dict[str, float | Dict[str, int]]:
    tp = fp = tn = fn = 0
    for yt, yp in zip(y_true, y_pred):
        if yt == 1 and yp == 1:
            tp += 1
        elif yt == 0 and yp == 1:
            fp += 1
        elif yt == 0 and yp == 0:
            tn += 1
        else:
            fn += 1

    total = max(1, len(y_true))
    accuracy = (tp + tn) / total
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
    }


def train_regression_model(
    model_id: str,
    records: List[WeeklyRecord],
    train_indices: Sequence[int],
    test_indices: Sequence[int],
    feature_names: Sequence[str],
    feature_fn,
    label_name: str,
    label_fn,
) -> tuple[dict, dict, dict]:
    x_all = [feature_fn(r) for r in records]
    y_all = [float(label_fn(r)) for r in records]

    x_train_raw = [x_all[i] for i in train_indices]
    y_train = [y_all[i] for i in train_indices]
    x_test_raw = [x_all[i] for i in test_indices]
    y_test = [y_all[i] for i in test_indices]

    means, stds = fit_standardizer(x_train_raw)
    x_train = with_intercept(standardize(x_train_raw, means, stds))
    x_test = with_intercept(standardize(x_test_raw, means, stds))

    weights = fit_linear_regression(x_train, y_train)
    y_pred = predict_linear(weights, x_test)

    model_metrics = {
        "r2": r2_score(y_test, y_pred),
        "mae": mae(y_test, y_pred),
        "rmse": rmse(y_test, y_pred),
    }
    pass_flag = model_metrics["r2"] >= R2_THRESHOLD

    performance = {
        "model_id": model_id,
        "model_type": "regression",
        "target": label_name,
        "train_rows": len(train_indices),
        "holdout_rows": len(test_indices),
        "metrics": model_metrics,
        "threshold": {"metric": "r2", "min_value": R2_THRESHOLD},
        "passed": pass_flag,
    }

    predictions = {
        "model_id": model_id,
        "target": label_name,
        "rows": [
            {
                "row_id": records[i].row_id,
                "week_serial": records[i].week_serial,
                "week_date": records[i].week_date,
                "actual": y_true,
                "predicted": y_hat,
                "error": y_hat - y_true,
            }
            for i, y_true, y_hat in zip(test_indices, y_test, y_pred)
        ],
    }

    features = {
        "model_id": model_id,
        "target": label_name,
        "feature_definitions": [
            {
                "name": name,
                "description": name.replace("_", " "),
                "standardized": True,
            }
            for name in feature_names
        ],
        "learned_parameters": {
            "intercept": weights[0],
            "coefficients": {
                feature_names[i]: weights[i + 1] for i in range(len(feature_names))
            },
        },
        "standardization": {
            "means": {feature_names[i]: means[i] for i in range(len(feature_names))},
            "stds": {feature_names[i]: stds[i] for i in range(len(feature_names))},
        },
    }

    return performance, predictions, features


def train_classifier(
    model_id: str,
    records: List[WeeklyRecord],
    train_indices: Sequence[int],
    test_indices: Sequence[int],
    feature_names: Sequence[str],
    feature_fn,
) -> tuple[dict, dict, dict]:
    x_all = [feature_fn(r) for r in records]
    y_all = [1 if r.this_week_pct >= 1.0 else 0 for r in records]

    x_train_raw = [x_all[i] for i in train_indices]
    y_train = [y_all[i] for i in train_indices]
    x_test_raw = [x_all[i] for i in test_indices]
    y_test = [y_all[i] for i in test_indices]

    means, stds = fit_standardizer(x_train_raw)
    x_train = with_intercept(standardize(x_train_raw, means, stds))
    x_test = with_intercept(standardize(x_test_raw, means, stds))

    weights = fit_logistic_regression(x_train, y_train)
    probs = predict_logistic(weights, x_test)
    y_pred = [1 if p >= 0.5 else 0 for p in probs]

    metrics = classification_metrics(y_test, y_pred)
    accuracy = float(metrics["accuracy"])
    pass_flag = accuracy >= ACCURACY_THRESHOLD

    performance = {
        "model_id": model_id,
        "model_type": "classification",
        "target": "sellout_flag (derived from this_week_pct >= 1.0)",
        "train_rows": len(train_indices),
        "holdout_rows": len(test_indices),
        "metrics": metrics,
        "threshold": {"metric": "accuracy", "min_value": ACCURACY_THRESHOLD},
        "passed": pass_flag,
    }

    predictions = {
        "model_id": model_id,
        "target": "sellout_flag",
        "rows": [
            {
                "row_id": records[i].row_id,
                "week_serial": records[i].week_serial,
                "week_date": records[i].week_date,
                "actual": int(y_true),
                "predicted": int(y_hat),
                "predicted_probability": prob,
            }
            for i, y_true, y_hat, prob in zip(test_indices, y_test, y_pred, probs)
        ],
    }

    features = {
        "model_id": model_id,
        "target": "sellout_flag",
        "feature_definitions": [
            {
                "name": name,
                "description": name.replace("_", " "),
                "standardized": True,
            }
            for name in feature_names
        ],
        "learned_parameters": {
            "intercept": weights[0],
            "coefficients": {
                feature_names[i]: weights[i + 1] for i in range(len(feature_names))
            },
        },
        "standardization": {
            "means": {feature_names[i]: means[i] for i in range(len(feature_names))},
            "stds": {feature_names[i]: stds[i] for i in range(len(feature_names))},
        },
    }

    return performance, predictions, features


def write_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def main() -> None:
    ensure_output_dir()
    records = load_weekly_records()
    train_indices, test_indices = deterministic_split(
        len(records), TRAIN_FRACTION, SEED
    )

    min_week = min(r.week_serial for r in records)

    gross_feature_names = [
        "last_week_gross",
        "top_ticket",
        "last_week_pct",
        "trend_weeks",
    ]

    def gross_features(r: WeeklyRecord) -> List[float]:
        return [
            r.last_week_gross,
            r.top_ticket,
            r.last_week_pct,
            r.week_serial - min_week,
        ]

    pricing_feature_names = [
        "top_ticket",
        "last_week_gross",
        "last_week_pct",
        "trend_weeks",
    ]

    def pricing_features(r: WeeklyRecord) -> List[float]:
        return [
            r.top_ticket,
            r.last_week_gross,
            r.last_week_pct,
            r.week_serial - min_week,
        ]

    cls_feature_names = [
        "last_week_gross",
        "average_ticket",
        "top_ticket",
        "total_seats",
        "last_week_pct",
        "trend_weeks",
    ]

    def cls_features(r: WeeklyRecord) -> List[float]:
        return [
            r.last_week_gross,
            r.average_ticket,
            r.top_ticket,
            r.total_seats,
            r.last_week_pct,
            r.week_serial - min_week,
        ]

    performance_rows: List[dict] = []
    prediction_rows: List[dict] = []
    feature_rows: List[dict] = []

    perf, preds, feats = train_regression_model(
        model_id="weekly_gross_regression",
        records=records,
        train_indices=train_indices,
        test_indices=test_indices,
        feature_names=gross_feature_names,
        feature_fn=gross_features,
        label_name="this_week_gross",
        label_fn=lambda r: r.this_week_gross,
    )
    performance_rows.append(perf)
    prediction_rows.append(preds)
    feature_rows.append(feats)

    perf, preds, feats = train_regression_model(
        model_id="average_ticket_regression",
        records=records,
        train_indices=train_indices,
        test_indices=test_indices,
        feature_names=pricing_feature_names,
        feature_fn=pricing_features,
        label_name="average_ticket",
        label_fn=lambda r: r.average_ticket,
    )
    performance_rows.append(perf)
    prediction_rows.append(preds)
    feature_rows.append(feats)

    perf, preds, feats = train_classifier(
        model_id="sellout_flag_classifier",
        records=records,
        train_indices=train_indices,
        test_indices=test_indices,
        feature_names=cls_feature_names,
        feature_fn=cls_features,
    )
    performance_rows.append(perf)
    prediction_rows.append(preds)
    feature_rows.append(feats)

    performance_payload = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "seed": SEED,
        "split": {
            "train_fraction": TRAIN_FRACTION,
            "holdout_fraction": 1.0 - TRAIN_FRACTION,
            "train_rows": len(train_indices),
            "holdout_rows": len(test_indices),
        },
        "source": {
            "source_file": "Final presentation/Data Collection & Visualization.xlsx",
            "source_sheet": "Broadway Revenue",
            "labels": {
                "weekly_gross_regression": "This Week's Gross",
                "average_ticket_regression": "Average Ticket",
                "sellout_flag_classifier": "Derived: this_week_pct >= 1.0",
            },
        },
        "thresholds": {"r2_min": R2_THRESHOLD, "accuracy_min": ACCURACY_THRESHOLD},
        "models": performance_rows,
        "all_models_passed": all(row["passed"] for row in performance_rows),
    }

    predictions_payload = {
        "generated_at_utc": performance_payload["generated_at_utc"],
        "seed": SEED,
        "source": performance_payload["source"],
        "models": prediction_rows,
    }

    features_payload = {
        "generated_at_utc": performance_payload["generated_at_utc"],
        "seed": SEED,
        "source": performance_payload["source"],
        "models": feature_rows,
    }

    write_json(ASSETS_DATA / "model_performance.json", performance_payload)
    write_json(ASSETS_DATA / "model_predictions.json", predictions_payload)
    write_json(ASSETS_DATA / "model_features.json", features_payload)

    print("Model suite training complete.")
    for row in performance_rows:
        metric_name = row["threshold"]["metric"]
        metric_value = row["metrics"][metric_name]
        print(
            f"- {row['model_id']}: {metric_name}={metric_value:.4f}, passed={row['passed']}"
        )
    print(f"All models passed: {performance_payload['all_models_passed']}")


if __name__ == "__main__":
    main()
