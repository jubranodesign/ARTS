import os

_DEFAULT_REPO_PATH = r"C:\Users\Remah\OneDrive\Documents\interview\coveredhealth"
REPO_PATH = os.getenv("REPO_PATH", _DEFAULT_REPO_PATH)
REPO_SEED_PATH = os.getenv("REPO_SEED_PATH", os.path.join(REPO_PATH, "seed_data"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_STORE_PATH = os.path.join(DATA_DIR, "vector_store")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"📁 Created missing directory: {DATA_DIR}")
