import logging
import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.repo_files import read_repo_text, repo_path_from_config, resolve_repo_file

logger = logging.getLogger(__name__)


@tool
def read_local_file(file_path: str, config: RunnableConfig) -> str:
    """Reads a file from the project. Path must be relative to project root."""
    try:
        repo_path = repo_path_from_config(config)
        logger.info("Reading file: %s", file_path)
        full_path = resolve_repo_file(repo_path, file_path)
        if not os.path.exists(full_path):
            return (
                f"Error: File not found. Tried to access: {full_path}. "
                "Ensure your path is relative to the project root."
            )
        content = read_repo_text(repo_path, file_path)
        response = f"SUCCESS: File read from absolute path: {full_path}\n{content}"
        logger.debug("Reading file response length=%s", len(response) if response else 0)
        return response
    except Exception as e:
        return f"Error: {str(e)}"


AGENT_TOOLS = [read_local_file]

