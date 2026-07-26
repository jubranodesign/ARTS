"""Backward-compatible barrel: load env once, re-export shared settings."""

from dotenv import load_dotenv

load_dotenv()

from shared.constants import LLM_MODEL_NAME, MOCK_TOOL, TEST_FRAMEWORK
from shared.embeddings import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_VERSION,
    get_embeddings_model,
)
from shared.llm_factory import get_model
from shared.node_llm import setup_node_llm
from shared.run_policy import (
    get_default_model_provider,
    get_max_test_attempts,
    get_risk_threshold,
)
from shared.graph_config import (
    GRAPH_CONFIG_OVERRIDE_KEYS,
    build_langgraph_run_config,
    merge_graph_configurable,
)
from shared.paths import (
    BASE_DIR,
    DATA_DIR,
    VECTOR_STORE_PATH,
    get_repo_path,
    get_repo_seed_path,
)

__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "EMBEDDING_MODEL_NAME",
    "EMBEDDING_MODEL_VERSION",
    "LLM_MODEL_NAME",
    "MOCK_TOOL",
    "TEST_FRAMEWORK",
    "VECTOR_STORE_PATH",
    "get_embeddings_model",
    "get_model",
    "get_repo_path",
    "get_repo_seed_path",
    "setup_node_llm",
    "get_default_model_provider",
    "get_risk_threshold",
    "get_max_test_attempts",
    "GRAPH_CONFIG_OVERRIDE_KEYS",
    "build_langgraph_run_config",
    "merge_graph_configurable",
]
