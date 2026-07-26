import logging

import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.patch import apply_search_replace_patch
from utils.repo_files import (
    read_repo_text,
    repo_path_from_config,
    resolve_repo_file,
    write_repo_text,
)

logger = logging.getLogger(__name__)


@tool
def write_local_file(file_path: str, content: str, config: RunnableConfig) -> str:
    """
    Writes content to a local file.
    Path must be relative to project root.
    """
    try:
        repo_path = repo_path_from_config(config)
        full_path = write_repo_text(repo_path, file_path, content)
        logger.info("Writing file: %s", full_path)
        return f"SUCCESS: File written to absolute path: {full_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def patch_test_code(file_path: str, patch_content: str, config: RunnableConfig) -> str:
    """
    Applies a Search/Replace patch to a file using a safe path.
    Format of patch_content:
    <<<<<<< SEARCH
    old code
    =======
    new code
    >>>>>>> REPLACE
    """
    logger.debug("patch_test_code patch_content: %s", patch_content)
    try:
        repo_path = repo_path_from_config(config)
        full_path = resolve_repo_file(repo_path, file_path)

        if not os.path.exists(full_path):
            return f"Error: File {file_path} (Full path: {full_path}) not found."

        content = read_repo_text(repo_path, file_path)
        new_content, error = apply_search_replace_patch(content, patch_content)
        if error is not None:
            return error

        write_repo_text(repo_path, file_path, new_content)

        logger.info("patch_test_code successfully patched %s", file_path)
        return f"Successfully patched {file_path}."

    except Exception as e:
        return f"An error occurred during patching: {str(e)}"


WRITER_TOOLS = [write_local_file, patch_test_code]
