"""Load env once; re-export LLM entry helpers (avoid importing services/graph here)."""

from dotenv import load_dotenv

load_dotenv()

from shared.llm_factory import get_model
from shared.node_llm import setup_node_llm

__all__ = [
    "get_model",
    "setup_node_llm",
]
