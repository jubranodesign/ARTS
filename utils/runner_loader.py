"""Load user-provided test runner callables (BYOR execution hook)."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

RunnerFn = Callable[..., tuple[str, str]]

_REPO_RUNNER_REL = os.path.join(".arts", "runner.py")
_RUNNER_FUNC_NAMES = ("run_tests", "run")


def _parse_entrypoint(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise ValueError(
            f"ARTS_TEST_RUNNER must be 'module:callable', got {spec!r}"
        )
    module_name, attr = spec.rsplit(":", 1)
    return module_name.strip(), attr.strip()


def _load_from_entrypoint(spec: str, repo_path: str | None) -> RunnerFn:
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


def _load_from_repo_file(repo_path: str) -> RunnerFn | None:
    path = os.path.join(os.path.abspath(repo_path), _REPO_RUNNER_REL)
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("arts_repo_runner", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in _RUNNER_FUNC_NAMES:
        fn = getattr(module, name, None)
        if callable(fn):
            logger.info("Using test runner from %s (%s)", path, name)
            return fn  # type: ignore[return-value]
    raise TypeError(f"{path} must define run_tests or run callable")


def resolve_test_runner(repo_path: str) -> RunnerFn | None:
    """
    Resolve BYOR runner: ARTS_TEST_RUNNER env, then REPO_PATH/.arts/runner.py.
    Returns None to use built-in pytest (Python default).
    """
    from shared.run_policy import get_test_runner_entrypoint

    entry = get_test_runner_entrypoint()
    if entry:
        logger.info("Using ARTS_TEST_RUNNER=%s", entry)
        return _load_from_entrypoint(entry, repo_path)
    return _load_from_repo_file(repo_path)
