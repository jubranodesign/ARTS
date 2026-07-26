# Contributing

Thank you for considering a contribution. This project is **early open source** ([MIT](LICENSE)) — active development; APIs and graph behavior may change. Issues, docs, and focused PRs are welcome.

## Before you start

- Read the [README](README.md) (bring-your-own-repo, ingest, risk gate, limitations).
- Quick path: [docs/QUICKSTART.md](docs/QUICKSTART.md).
- Demos: [LinkedIn (~5 min)](https://www.linkedin.com/feed/update/urn:li:activity:7470499709799821313/) · [YouTube (~30 min)](https://www.youtube.com/watch?v=hKFgm7mVf7I).

## Local setup

1. Clone the repo, create a venv, `pip install -e .`
2. Copy [`.env.example`](.env.example) to `.env` — set `REPO_PATH` (your target repo) and API keys for `MODEL_PROVIDER`
3. Ingest your repo: `python ingest.py --repo-path "%REPO_PATH%" --both`
4. Run the agent: `python main.py --repo-path "%REPO_PATH%"` or edit and run `run_local.py`

Optional:

- RAG eval: `pip install -e ".[eval]"` then `python evaluation.py rag` or `run_eval_local.py`
- Retrieval eval: `python evaluation.py retrieval` (needs ingest first; **Chroma summaries only** — not BM25. Low scores with code-literal keywords are often expected until you tune `evaluation/retrieval/datasets.py` or metrics — see README § Offline evaluation)

Do **not** commit `.env`, `data/vector_store/`, or checkpoint SQLite files.

## Pull request workflow

1. Fork the repository and create a branch from `main`
2. Keep PRs **focused** (one topic: bugfix, docs, eval datasets, small feature)
3. Update README / QUICKSTART if you change behavior, env vars, or entry points
4. Write clear commit messages (English is fine)

Before opening a PR, if your change touches retrieval, ingest, or the graph, run what applies:

- `python evaluation.py retrieval` (after ingest on a test repo), and/or
- A short agent smoke run via `run_local.py`

CI may be added later; local smoke is appreciated for now.

## Good first contributions

- Improve docs or translate clarifications
- Adapt [`evaluation/retrieval/datasets.py`](evaluation/retrieval/datasets.py) for another codebase (with a short README note)
- Fix typos, logging, or startup-check messages
- Optional: smoke tests or GitHub Actions (discuss in an issue first)

## Larger changes

Please **open an issue first** for:

- Graph topology, risk-gate policy defaults, or removing `interrupt_before`
- New agents or breaking changes to `configurable` / `shared/graph_config.py`
- Large refactors of `main.py` streaming UI

## Reporting bugs

Open an issue with:

- What you ran (`main`, `run_local`, `evaluation.py`, …)
- OS and Python version
- Relevant `.env` keys **names only** (never paste secrets)
- Whether ingest completed and if the vector store was empty
- Log excerpt with `LOG_LEVEL=DEBUG` if possible

## Code of conduct

Be respectful and constructive. We are all learning and building in public.

Questions? Open a GitHub issue on this repository after you publish the remote URL.
