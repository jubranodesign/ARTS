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


def extract_target_file_path(text: str) -> str:
    """
    Extract the first source file path in a string for the active REPO_LANGUAGE extensions.
    """
    from shared.repo_language import get_ingest_code_extensions, unknown_target_file_placeholder

    if not text:
        return unknown_target_file_placeholder()

    exts = get_ingest_code_extensions()
    ext_alts = "|".join(
        re.escape(e.lstrip(".")) for e in sorted(exts, key=len, reverse=True)
    )
    pattern = rf"([\w\d/_.$-]+\.(?:{ext_alts}))"
    match = re.search(pattern, text, flags=re.IGNORECASE)

    if match:
        return match.group(1).strip().lstrip("./")

    return unknown_target_file_placeholder()


def extract_python_path(text: str) -> str:
    """Backward-compatible alias for extract_target_file_path."""
    return extract_target_file_path(text)


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
    Map a source file to a conventional test path for REPO_LANGUAGE.
    Python: tests/.../test_<file>.py — others: tests/.../<stem>.test<ext> or test_<stem><ext>.
    """
    from shared.repo_language import effective_splitter_language_id

    clean_path = normalize_relative_path(target_file)
    parts = clean_path.split("/")
    folder = "/".join(parts[:-1])
    filename = parts[-1]
    lang_id = effective_splitter_language_id()

    if lang_id == "python":
        if folder:
            return f"tests/{folder}/test_{filename}"
        return f"tests/test_{filename}"

    stem, ext = os.path.splitext(filename)
    if lang_id in ("js", "ts"):
        test_filename = f"{stem}.test{ext}"
    else:
        test_filename = f"test_{stem}{ext}"

    if folder:
        return f"tests/{folder}/{test_filename}"
    return f"tests/{test_filename}"


def get_import_path(target_file: str) -> str:
    """Map file path to Python import path; empty for non-Python pipeline."""
    from shared.repo_language import is_python_pipeline

    if not target_file or not is_python_pipeline():
        return ""

    path_without_ext = os.path.splitext(normalize_relative_path(target_file))[0]
    import_path = path_without_ext.replace("/", ".")
    return import_path.strip(".")

