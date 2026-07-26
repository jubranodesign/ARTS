import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.repo_files import read_repo_text_tool_response, repo_path_from_config

logger = logging.getLogger(__name__)


@tool
def read_local_file(file_path: str, config: RunnableConfig) -> str:
    """Reads a file from the project. Path must be relative to project root."""
    try:
        repo_path = repo_path_from_config(config)
        logger.info("Reading file: %s", file_path)
        response = read_repo_text_tool_response(repo_path, file_path)
        logger.debug("Reading file response length=%s", len(response) if response else 0)
        return response
    except Exception as e:
        return f"Error: {str(e)}"


AGENT_TOOLS = [read_local_file]

