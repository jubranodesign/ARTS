import os

from langchain_core.runnables import RunnableConfig

from shared.paths import get_safe_full_path


def repo_path_from_config(config: RunnableConfig) -> str:
    return config["configurable"]["repo_path"]


def resolve_repo_file(repo_path: str, relative_path: str) -> str:
    return get_safe_full_path(repo_path, relative_path)


def read_repo_text(repo_path: str, relative_path: str) -> str:
    full_path = resolve_repo_file(repo_path, relative_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def write_repo_text(repo_path: str, relative_path: str, content: str) -> str:
    full_path = resolve_repo_file(repo_path, relative_path)
    directory = os.path.dirname(full_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return full_path


def read_repo_text_tool_response(repo_path: str, relative_path: str) -> str:
    full_path = resolve_repo_file(repo_path, relative_path)
    if not os.path.exists(full_path):
        return (
            f"Error: File not found. Tried to access: {full_path}. "
            "Ensure your path is relative to the project root."
        )
    content = read_repo_text(repo_path, relative_path)
    return f"SUCCESS: File read from absolute path: {full_path}\n{content}"
