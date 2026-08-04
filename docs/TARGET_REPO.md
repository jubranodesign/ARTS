# Target repository (BYOR)

ARTS **does not ship** your application code, golden tests, or third-party libraries. Everything under **`REPO_PATH`** is your responsibility.

## What you must provide

| Item | Location | Purpose |
|------|----------|---------|
| Application source | Your repo tree | Ingest + research |
| Golden test examples | `<REPO_PATH>/seed_data/` (or `REPO_SEED_PATH`) | `search_golden_tests_semantic` patterns |
| **Runtime dependencies** | `requirements.txt`, `package.json`, etc. | Must resolve when **your test runner** executes |
| **Test runner** (non-Python or custom) | `ARTS_TEST_RUNNER` or `<REPO_PATH>/.arts/runner.py` | See README § BYOR test runner |
| **Risk metrics** (non-Python or custom) | `ARTS_METRICS_EXTRACTOR` or `<REPO_PATH>/.arts/metrics.py` | JM1 columns for ML gate — see README § Risk gate |

ARTS installs **only its own** dependencies (`pip install -e .` in the ARTS clone). It does **not** run `pip install` on `REPO_PATH` for you.

## Python packages for pytest (default)

When `REPO_LANGUAGE=python` and no custom runner is set, the executor runs:

```text
sys.executable -m pytest <test_file>
```

with `cwd=REPO_PATH` and `PYTHONPATH` extended to include the repo root and the target module’s directory (`agents/executor_agent/call_executor.py`).

So **`sys.executable` is the same interpreter you use to run ARTS** (typically your activated venv). Any package your **source code and generated tests import** must be installed **in that environment**.

### Recommended local setup

```bash
# 1. ARTS venv
python -m venv .venv
# activate .venv
pip install -e .

# 2. Target repo dependencies (adjust path/command to your project)
pip install -r "%REPO_PATH%/requirements.txt"
# and/or:
pip install -e "%REPO_PATH%"
```

If pytest fails with **`ModuleNotFoundError`**, install the missing package from **the target repo’s** dependency files — not ARTS’s `pyproject.toml`.

## Golden seed data

Before `python ingest.py --repo-path "%REPO_PATH%" --both`:

- Add test files under **`seed_data/`** with extensions matching **`REPO_LANGUAGE`** (e.g. `.py`, `.ts`).
- Seeds are indexed separately from production source; the researcher retrieves them semantically.

See README § Golden seed data.

## Isolation and safety

- **Today:** No container sandbox — pytest runs on your machine with your user permissions.
- **Writes:** The writer can create or modify files under `REPO_PATH` (usually `tests/`). Use a **clone or branch**, not production.
- **Future / production:** A isolated job would clone the repo, install deps in a **dedicated venv or container**, run pytest there, then tear down. ARTS does not implement that yet; see [ARCHITECTURE.md](ARCHITECTURE.md).

## Checklist before first agent run

- [ ] `REPO_PATH` points at the repo you want to test
- [ ] `seed_data/` populated and **`ingest --both`** completed
- [ ] Target repo **dependencies installed** (and runner configured if not Python/pytest)
- [ ] Read README **[Limitations](../README.md#limitations)** (risk gate, BYOR scope, demo)
