import os
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.repo_files import read_repo_text_tool_response, repo_path_from_config

@tool
def read_local_file(file_path: str, config: RunnableConfig) -> str:
    """Reads a file from the project. Path must be relative to project root."""
    try:
        repo_path = repo_path_from_config(config)
        print(f"\n📖 [TOOL CALL] Reading file: {file_path}")
        response = read_repo_text_tool_response(repo_path, file_path)
        print(f"\n📖 [TOOL CALL] Reading file response: {response}")
        return response
    except Exception as e:
        return f"Error: {str(e)}"


AGENT_TOOLS = [read_local_file]


