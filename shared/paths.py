import logging
import os
import re

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


# --- Repo-relative paths (parsing, tests layout, safe join under REPO_PATH) ---


def extract_python_path(text: str) -> str:
    """
    Extract the first Python file path in a string.
    Supports paths like: 'service/api.py', './tests/test_x.py', 'main.py'
    """
    if not text:
        return "unknown_file.py"

    pattern = r"([\w\d/_.-]+\.py)"
    match = re.search(pattern, text)

    if match:
        path = match.group(1)
        return path.strip().lstrip("./")

    return "unknown_file.py"


def normalize_relative_path(path: str, *, lowercase: bool = False) -> str:
    """Normalize repo-relative paths (forward slashes; optional lowercase for comparison)."""
    if not path:
        return ""
    normalized = path.replace("\\", "/").strip()
    return normalized.lower() if lowercase else normalized


def get_safe_full_path(base_path: str, relative_path: str) -> str:
    """Join base_path with a model-provided relative path safely."""
    if not relative_path:
        return ""

    clean_path = relative_path.strip().strip("'").strip('"')
    full_path = os.path.join(base_path, clean_path)
    return os.path.normpath(full_path)


def get_test_path(target_file: str) -> str:
    """
    Map a source file to a conventional test path.
    Example: scraper/api.py -> tests/scraper/test_api.py
    """
    clean_path = normalize_relative_path(target_file)

    parts = clean_path.split("/")
    folder = "/".join(parts[:-1])
    filename = parts[-1]

    if folder:
        return f"tests/{folder}/test_{filename}"
    return f"tests/test_{filename}"


def get_import_path(target_file: str) -> str:
    """Map file path to Python import path (e.g. pkg/module.py -> pkg.module)."""
    if not target_file:
        return ""

    path_without_ext = os.path.splitext(normalize_relative_path(target_file))[0]
    import_path = path_without_ext.replace("/", ".")
    return import_path.strip(".")

