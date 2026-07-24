import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from utils.repo_files import (
    read_repo_text,
    repo_path_from_config,
    resolve_repo_file,
    write_repo_text,
)

@tool
def write_local_file(file_path: str, content: str, config: RunnableConfig) -> str:
    """
    Writes content to a local file. 
    Path must be relative to project root.
    """
    try:
        repo_path = repo_path_from_config(config)
        full_path = write_repo_text(repo_path, file_path, content)
        print(f"\n💾 [TOOL CALL] Writing file: {full_path}")
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
    print(f"patch_test_code patch_content: {patch_content}")
    try:
        repo_path = repo_path_from_config(config)
        full_path = resolve_repo_file(repo_path, file_path)

        if not os.path.exists(full_path):
            return f"Error: File {file_path} (Full path: {full_path}) not found."

        content = read_repo_text(repo_path, file_path)

        if "<<<<<<< SEARCH" not in patch_content or "=======" not in patch_content or ">>>>>>> REPLACE" not in patch_content:
            return "Error: Invalid patch format. Missing <<<<<<< SEARCH, =======, or >>>>>>> REPLACE."

        try:
            search_part = patch_content.split("<<<<<<< SEARCH")[1].split("=======")[0].strip('\r\n')
            replace_part = patch_content.split("=======")[1].split(">>>>>>> REPLACE")[0].strip('\r\n')

            content = content.replace("\r\n", "\n")
            search_part = search_part.replace("\r\n", "\n")
            replace_part = replace_part.replace("\r\n", "\n")

            search_part = "\n".join([line.rstrip() for line in search_part.split("\n")])

        except IndexError:
            return "Error: Could not parse SEARCH/REPLACE blocks. Check the format."

        if search_part in content and search_part != "":
            new_content = content.replace(search_part, replace_part, 1)
        else:
            print("⚠️ Full block not found. Falling back to line-by-line matching...")

            search_lines = [line.strip() for line in search_part.split('\n') if line.strip()]
            replace_lines = [line.strip() for line in replace_part.split('\n') if line.strip()]

            new_content = content
            changes_made = False

            for line in search_lines:
                found_line = None
                if line in new_content:
                    found_line = line
                elif line.replace("'", '"') in new_content:
                    found_line = line.replace("'", '"')
                elif line.replace('"', "'") in new_content:
                    found_line = line.replace('"', "'")

                if found_line:
                    line_index = search_lines.index(line)
                    current_replace = replace_lines[line_index] if line_index < len(replace_lines) else ""
                    new_content = new_content.replace(found_line, current_replace, 1)
                    changes_made = True
                else:
                    print(f"🔍 Line ignored (not found in file): {line}")

            if not changes_made and replace_part != "":
                return (
                    f"Error: None of the lines in the SEARCH block were found in the file.\n"
                    f"AI tried to find lines from:\n{search_part}"
                )

        write_repo_text(repo_path, file_path, new_content)

        print("patch_test_code Successfully patched")
        return f"Successfully patched {file_path}."

    except Exception as e:
        return f"An error occurred during patching: {str(e)}"


WRITER_TOOLS = [write_local_file, patch_test_code]
