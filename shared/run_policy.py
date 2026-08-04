"""Runtime policy from env (single source for defaults used by graph + LLM)."""

import os

_DEFAULT_MODEL_PROVIDER = "mistral"
_DEFAULT_RISK_THRESHOLD = 0.2
_DEFAULT_MAX_TEST_ATTEMPTS = 3


def get_default_model_provider() -> str:
    raw = os.getenv("MODEL_PROVIDER")
    if raw and str(raw).strip():
        return str(raw).strip().lower()
    return _DEFAULT_MODEL_PROVIDER


def get_ingest_model_provider() -> str:
    """LLM provider for ingest chunk summaries (CodeProcessor). Falls back to MODEL_PROVIDER."""
    raw = os.getenv("INGEST_MODEL_PROVIDER")
    if raw and str(raw).strip():
        return str(raw).strip().lower()
    return get_default_model_provider()


def get_risk_threshold() -> float:
    raw = os.getenv("RISK_THRESHOLD")
    if raw is None or not str(raw).strip():
        return _DEFAULT_RISK_THRESHOLD
    try:
        return float(str(raw).strip())
    except ValueError:
        return _DEFAULT_RISK_THRESHOLD


def get_max_test_attempts() -> int:
    raw = os.getenv("MAX_TEST_ATTEMPTS")
    if raw is None or not str(raw).strip():
        return _DEFAULT_MAX_TEST_ATTEMPTS
    try:
        value = int(str(raw).strip())
        return max(1, value)
    except ValueError:
        return _DEFAULT_MAX_TEST_ATTEMPTS


def get_test_runner_entrypoint() -> str | None:
    """ARTS_TEST_RUNNER=package.module:run_tests — optional BYOR test execution."""
    raw = os.getenv("ARTS_TEST_RUNNER")
    if raw and str(raw).strip():
        return str(raw).strip()
    return None


def get_metrics_extractor_entrypoint() -> str | None:
    """ARTS_METRICS_EXTRACTOR=package.module:extract_metrics — optional BYOR risk metrics."""
    raw = os.getenv("ARTS_METRICS_EXTRACTOR")
    if raw and str(raw).strip():
        return str(raw).strip()
    return None
