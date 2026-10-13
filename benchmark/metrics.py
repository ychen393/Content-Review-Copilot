from __future__ import annotations

from typing import Iterable


def issue_metrics(expected: Iterable[str], actual: Iterable[str]) -> dict[str, float]:
    expected_set, actual_set = set(expected), set(actual)
    true_positive = len(expected_set & actual_set)
    precision = true_positive / len(actual_set) if actual_set else (1.0 if not expected_set else 0.0)
    recall = true_positive / len(expected_set) if expected_set else (1.0 if not actual_set else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def summarize(rows: list[dict]) -> dict[str, float]:
    if not rows:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "pass_rate": 0.0, "average_latency": 0.0, "estimated_cost": 0.0}
    return {key: sum(row[key] for row in rows) / len(rows) for key in ("precision", "recall", "f1", "pass_rate", "average_latency", "estimated_cost")}
