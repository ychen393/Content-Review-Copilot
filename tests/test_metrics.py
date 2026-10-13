from benchmark.metrics import issue_metrics, summarize


def test_metrics():
    metrics = issue_metrics(["a", "b"], ["a", "c"])
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert summarize([{**metrics, "pass_rate": 1.0, "average_latency": 4.0, "estimated_cost": 0.1}])["f1"] == metrics["f1"]
