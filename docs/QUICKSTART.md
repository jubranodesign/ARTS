# Quickstart (condensed)

Full details: [README.md](../README.md).

**Demos:** [LinkedIn (~5 min)](https://www.linkedin.com/feed/update/urn:li:activity:7470499709799821313/) · [YouTube (~30 min)](https://www.youtube.com/watch?v=hKFgm7mVf7I)

**Bring your own repo:** set `REPO_PATH` to your project; **ingest is required** (step below). No dataset ships with this repo.

```bash
cp .env.example .env
# Set REPO_PATH and MISTRAL_API_KEY (or other provider key)
pip install -e .
python ingest.py --repo-path "%REPO_PATH%" --both
python main.py --repo-path "%REPO_PATH%"
```

Or edit `run_local.py` (`RUN = "both"`) and run `python run_local.py`.

**Risk gate:** if the run ends after one node, check logs for `Risk low` — set `RISK_THRESHOLD=0.0` in `.env` to experiment.

**Debug:** `LOG_LEVEL=DEBUG` in `.env`.

**Eval (after ingest):** `python evaluation.py retrieval` or `python run_eval_local.py` — retrieval eval is **Chroma-only** (keywords matched on LLM summaries, not BM25/raw code). RAG: `pip install -e ".[eval]"` then `RUN=rag`. See README § [Offline evaluation](../README.md#offline-evaluation) and [Ingestion & retrieval storage](../README.md#ingestion--retrieval-storage).
