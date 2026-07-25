def apply_search_replace_patch(content: str, patch_content: str) -> tuple[str | None, str | None]:
    """
    Apply SEARCH/REPLACE patch_content to file content.

    Returns (new_content, None) on success, (None, error_message) on failure.
    """
    if (
        "<<<<<<< SEARCH" not in patch_content
        or "=======" not in patch_content
        or ">>>>>>> REPLACE" not in patch_content
    ):
        return None, (
            "Error: Invalid patch format. Missing <<<<<<< SEARCH, =======, or >>>>>>> REPLACE."
        )

    try:
        search_part = (
            patch_content.split("<<<<<<< SEARCH")[1].split("=======")[0].strip("\r\n")
        )
        replace_part = (
            patch_content.split("=======")[1].split(">>>>>>> REPLACE")[0].strip("\r\n")
        )

        content = content.replace("\r\n", "\n")
        search_part = search_part.replace("\r\n", "\n")
        replace_part = replace_part.replace("\r\n", "\n")

        search_part = "\n".join([line.rstrip() for line in search_part.split("\n")])

    except IndexError:
        return None, "Error: Could not parse SEARCH/REPLACE blocks. Check the format."

    if search_part in content and search_part != "":
        new_content = content.replace(search_part, replace_part, 1)
    else:
        print("⚠️ Full block not found. Falling back to line-by-line matching...")

        search_lines = [line.strip() for line in search_part.split("\n") if line.strip()]
        replace_lines = [line.strip() for line in replace_part.split("\n") if line.strip()]

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
                current_replace = (
                    replace_lines[line_index] if line_index < len(replace_lines) else ""
                )
                new_content = new_content.replace(found_line, current_replace, 1)
                changes_made = True
            else:
                print(f"🔍 Line ignored (not found in file): {line}")

        if not changes_made and replace_part != "":
            return None, (
                f"Error: None of the lines in the SEARCH block were found in the file.\n"
                f"AI tried to find lines from:\n{search_part}"
            )

    return new_content, None
