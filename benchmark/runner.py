from __future__ import annotations

import json
import time
from pathlib import Path
from backend.pipeline import ContentQAPipeline
from .metrics import issue_metrics, summarize


def run(dataset: str | Path = "benchmark/dataset.jsonl", data_dir: str | Path = "data") -> dict[str, float]:
    pipeline = ContentQAPipeline(data_dir)
    rows = []
    for line in Path(dataset).read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        started = time.perf_counter()
        result = pipeline.run(case["input"])
        actual = [issue["issue_id"] for issue in result.report["issues_found"]]
        metrics = issue_metrics(case["expected_issues"], actual)
        metrics.update(pass_rate=float(result.evaluation.compliance_pass == case["expected_pass"]), average_latency=(time.perf_counter() - started) * 1000, estimated_cost=result.evaluation.estimated_cost)
        rows.append(metrics)
    return summarize(rows)


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
