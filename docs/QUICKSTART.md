# Quickstart (condensed)

Full details: [README.md](../README.md).

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
