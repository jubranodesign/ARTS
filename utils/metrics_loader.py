"""Load user-provided JM1/Radon-style metrics extractors (BYOR risk gate hook)."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from collections.abc import Callable

logger = logging.getLogger(__name__)

MetricsFn = Callable[[str], object]

_REPO_METRICS_REL = os.path.join(".arts", "metrics.py")
_METRICS_FUNC_NAMES = ("extract_metrics", "extract_code_metrics")


def _parse_entrypoint(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise ValueError(
            f"ARTS_METRICS_EXTRACTOR must be 'module:callable', got {spec!r}"
        )
    module_name, attr = spec.rsplit(":", 1)
    return module_name.strip(), attr.strip()


def _load_from_entrypoint(spec: str, repo_path: str | None) -> MetricsFn:
    module_name, attr = _parse_entrypoint(spec)
    if repo_path and os.path.isdir(repo_path):
        repo_abs = os.path.abspath(repo_path)
        if repo_abs not in sys.path:
            sys.path.insert(0, repo_abs)
    module = importlib.import_module(module_name)
    fn = getattr(module, attr, None)
    if not callable(fn):
        raise TypeError(f"{spec!r}: attribute is not callable")
    return fn  # type: ignore[return-value]


def _load_from_repo_file(repo_path: str) -> MetricsFn | None:
    path = os.path.join(os.path.abspath(repo_path), _REPO_METRICS_REL)
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("arts_repo_metrics", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in _METRICS_FUNC_NAMES:
        fn = getattr(module, name, None)
        if callable(fn):
            logger.info("Using metrics extractor from %s (%s)", path, name)
            return fn  # type: ignore[return-value]
    raise TypeError(f"{path} must define extract_metrics or extract_code_metrics")


def resolve_metrics_extractor(repo_path: str | None) -> MetricsFn | None:
    """
    ARTS_METRICS_EXTRACTOR env, then REPO_PATH/.arts/metrics.py when repo_path is set.
    Returns None to use built-in Radon for Python only.
    """
    from shared.run_policy import get_metrics_extractor_entrypoint

    entry = get_metrics_extractor_entrypoint()
    if entry:
        logger.info("Using ARTS_METRICS_EXTRACTOR=%s", entry)
        return _load_from_entrypoint(entry, repo_path)
    if repo_path:
        return _load_from_repo_file(repo_path)
    return None
