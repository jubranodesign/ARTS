import logging
import os

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vector_store")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info("Created missing directory: %s", DATA_DIR)

_REPO_PATH_HELP = (
    "REPO_PATH is required. Set it in your environment (e.g. .env) "
    "or pass --repo-path when running main.py, ingest.py, or feature_extractor.py."
)


def get_repo_path() -> str:
    raw = os.getenv("REPO_PATH")
    if not raw or not str(raw).strip():
        raise RuntimeError(_REPO_PATH_HELP)
    return os.path.abspath(os.path.expanduser(raw.strip()))


def get_repo_seed_path(repo_path: str | None = None) -> str:
    seed = os.getenv("REPO_SEED_PATH")
    if seed and str(seed).strip():
        return os.path.abspath(os.path.expanduser(seed.strip()))
    base = repo_path if repo_path is not None else get_repo_path()
    return os.path.join(base, "seed_data")
