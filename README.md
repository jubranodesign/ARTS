# Agentic Test System

LangGraph multi-agent pipeline that ingests a target repository, scores code risk with an ML model, runs retrieval-augmented research, and generates pytest files **inside your repo** under test.

This is a **research / course-style** project, not a hosted SaaS. Expect local CLI, Rich streaming output, and Chroma + SQLite on disk.

For a one-page cheat sheet, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo-url>
cd agentic_test_system_project_v2
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e .
# or: pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

- Copy from [`.env.example`](.env.example) any keys you are missing (merge; do not wipe existing secrets).
- Set **`REPO_PATH`** to the repository you want to test (required).
- Set **`MODEL_PROVIDER`** (default `mistral`) and the matching API key (e.g. `MISTRAL_API_KEY`).

### 3. Ingest vector store (first time or after repo changes)

```bash
python ingest.py --repo-path "%REPO_PATH%" --both
```

Or use `run_local.py` with `RUN = "both"` and `INGEST_MODE = "both"`.

### 4. Run the agent

**CLI:**

```bash
python main.py --repo-path "%REPO_PATH%"
# optional: --task "Write unit tests for analysis_service/analysis.py"
```

**Local dev (edit flags in file):**

```bash
python run_local.py
```

Set `LOG_LEVEL=DEBUG` in `.env` for detailed logs from `wait_for_task`, writer, and failure analysis.

### 5. What you should see

- Rich panels per graph node (researcher, designer, writer, executor).
- If the run **stops early** with little output, see [Risk gate](#risk-gate) below.

## Configuration reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `REPO_PATH` | — | Target repo (required) |
| `MODEL_PROVIDER` | `mistral` | LLM backend for all agent nodes |
| `RISK_THRESHOLD` | `0.2` | Min ML risk score to enter researcher path |
| `MAX_TEST_ATTEMPTS` | `3` | Pytest failure → writer repair loops |
| `LOG_LEVEL` | `INFO` | Python logging (`DEBUG` for dev) |
| `USER_TASK` | built-in default | Task when CLI/`run_local` task unset |

Graph run overrides (thread id, provider per run): pass `configurable` from `run_local.py` as `GRAPH_CONFIG`, e.g. `{"model_provider": "groq", "thread_id": "dev-1"}`.

Single source for defaults: `shared/run_policy.py`.

## Risk gate

After `wait_for_task`, a random-forest risk score is computed on the target file.

- If **`risk_score >= RISK_THRESHOLD`** (default **0.2**): flow continues to **researcher** → designer → writer → executor.
- If **`risk_score < RISK_THRESHOLD`**: the graph routes to **END**. You will **not** get tests or writer output — only the early risk step runs (plus stream setup). This is intentional (high-recall gate from the ML notebook), not a crash.

To proceed on “low risk” files during experiments, temporarily lower `RISK_THRESHOLD` in `.env` (e.g. `0.0`) or point `USER_TASK` at a file the model scores higher.

## Limitations

Read these before running on an important repository.

### Graph interrupt (`wait_for_task`)

The compiled graph uses `interrupt_before=["wait_for_task"]` for LangGraph Studio / human-in-the-loop workflows. The CLI and `run_local` path **seed state** with `update_state` and then **`stream`**, which resumes past the interrupt. If you invoke the graph differently (e.g. raw LangGraph CLI without that pattern), `wait_for_task` may not run until you resume correctly.

### Ingestion required

Semantic/BM25 tools expect a populated Chroma store under `data/vector_store`. Run **`ingest.py`** (or `RUN=both` in `run_local.py`) before expecting useful researcher retrieval.

### ML model at import

`wait_for_task` imports `ml_predictor` and loads the sklearn model when that node module loads. First run can be slower; the model file must be present in the project layout expected by `ml_predictor.utils`.

### Writes and pytest under `REPO_PATH`

The writer uses tools to **read and write files under `REPO_PATH`**, typically under `tests/…`. The executor runs **`pytest`** on those paths with `cwd=REPO_PATH`. Use a disposable clone or branch — not production code without review.

### Checkpoint SQLite

Runs persist LangGraph state to `checkpoints.sqlite` (or `CHECKPOINT_DB`). Re-use the same `thread_id` to continue threads; delete the file for a clean slate.

## Project layout (short)

| Path | Role |
|------|------|
| `main.py` | CLI + streaming UX |
| `run_local.py` | Dev entry (`RUN=ingest\|agent\|both`) |
| `ingest.py` | Chroma + BM25 ingestion |
| `graph/builder.py` | LangGraph definition |
| `graph/routes.py` | Risk gate, repair loop |
| `agents/` | Researcher, designer, writer, executor nodes |
| `evaluation/` | Offline RAG/metrics (not imported by the live graph) |

## Development notes

- Entry points call `configure_logging()` after `load_dotenv()`. `build_app()` does **not** change log level, so `LOG_LEVEL=DEBUG` stays active for the whole run.
- Do not commit `.env` or `data/vector_store/` (see `.gitignore`).

For deeper evaluation workflows, see scripts under `evaluation/`. **Ground truth** for Ragas/metrics lives in evaluation datasets (e.g. `evaluation/rag/researcher_agent/datasets.py`), not in `main.py` or `GRAPH_CONFIG`.
