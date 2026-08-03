"""
Example BYOR metrics extractor for REPO_PATH/.arts/metrics.py

Must return a pandas DataFrame with columns (JM1 / Radon aligned):
  loc, v(g), v, d, e, complexity_density, volume_per_line

For Python repos you can delegate to ml_predictor.utils.extract_code_metrics_radon.
For other languages, map your analyzer (lizard, Sonar, etc.) to the same columns.
"""

from __future__ import annotations

from ml_predictor.utils import extract_code_metrics_radon


def extract_metrics(code_string: str):
    return extract_code_metrics_radon(code_string)
