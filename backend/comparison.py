from __future__ import annotations

import difflib
from .models import AnalysisVersion


def compare_versions(first: AnalysisVersion, second: AnalysisVersion) -> dict:
    diff = difflib.unified_diff(first.content.splitlines(), second.content.splitlines(), fromfile=f"Version {first.version_number}", tofile=f"Version {second.version_number}", lineterm="")
    return {
        "diff": "\n".join(diff),
        "evaluation_difference": second.evaluation.score - first.evaluation.score,
        "issues_fixed": sorted(set(first.applied_suggestions) - set(second.applied_suggestions)),
        "issues_introduced": sorted(set(second.applied_suggestions) - set(first.applied_suggestions)),
    }
