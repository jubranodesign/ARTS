# Target repository (BYOR)

ARTS **does not ship** your application code, golden tests, or third-party libraries. Everything under **`REPO_PATH`** is your responsibility.

## What you must provide

| Item | Location | Purpose |
|------|----------|---------|
| Application source | Your repo tree | Ingest + research |
| Golden pytest examples | `<REPO_PATH>/seed_data/` (or `REPO_SEED_PATH`) | `search_golden_tests_semantic` patterns |
| **Runtime dependencies** | `requirements.txt`, `pyproject.toml`, etc. | Imports must resolve when pytest runs |

ARTS installs **only its own** dependencies (`pip install -e .` in the ARTS clone). It does **not** run `pip install` on `REPO_PATH` for you.

## Python packages for pytest

The executor runs:

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

- Add pytest files under **`seed_data/`** that reflect **how you want tests written** (mocks, fixtures, style).
- Seeds are indexed separately from production source; the researcher retrieves them semantically.

See README § Golden seed data.

## Isolation and safety

- **Today:** No container sandbox — pytest runs on your machine with your user permissions.
- **Writes:** The writer can create or modify files under `REPO_PATH` (usually `tests/`). Use a **clone or branch**, not production.
- **Future / production:** A isolated job would clone the repo, install deps in a **dedicated venv or container**, run pytest there, then tear down. ARTS does not implement that yet; see [ARCHITECTURE.md](ARCHITECTURE.md).

## Checklist before first agent run

- [ ] `REPO_PATH` points at the repo you want to test
- [ ] `seed_data/` populated and **`ingest --both`** completed
- [ ] Target repo **dependencies installed** in the ARTS Python environment
- [ ] Read README **[Limitations](../README.md#limitations)** (risk gate, Python-only, demo scope)
