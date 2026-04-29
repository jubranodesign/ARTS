from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from services.vector_db_service import VectorDBService

# @tool
# def search_codebase(query: str, config: RunnableConfig) -> str:
#    """
#     Search the project's source code for snippets and their relative paths.
#     Use this tool to find logic, classes, or specific files.
#     RETURNS: A list of code chunks. Each chunk starts with 'FILE: path/to/file.py'.

#      Args:
#       query: A search term. Best results come from using function names, 
#            class names, or filenames WITHOUT the path/extension 
#            (e.g., use 'scraper_api' instead of 'scraper_service/scraper_api.py').
#    """
#    try:
#         # שליפת המופע מהקונפיג
#         vdb = config.get("configurable", {}).get("vdb") or VectorDBService()
#         # הקריאה פשוטה כי ה-Service כבר מחזיר מחרוזת מעובדת (Formatted String)
#         return vdb.search_code(query)
        
#    except Exception as e:
#         return f"Error searching the codebase: {str(e)}"

@tool
def search_codebase(query: str, search_type: str = "code_only", config: RunnableConfig = None) -> str:
    """
    Search the project's codebase. Use this tool TWICE per task: 
    First for code logic, then for test examples.
    
    Args:
        query: Search term (function/class name).
        search_type: 
            - 'code_only' (DEFAULT): MUST be used first to find the implementation logic.
            - 'tests_only': MUST be used second to find "Golden Examples" (existing tests). 
                            Do not skip this, as it is required for the briefing.
    
    RETURNS: A formatted string of code chunks.
    """
    try:
        vdb = config.get("configurable", {}).get("vdb") or VectorDBService()
        
        # בניית ה-filter עבור ה-Service
        filter_dict = None
        if search_type == "tests_only":
            filter_dict = {"is_test": True}
        elif search_type == "code_only":
            filter_dict = {"is_test": False}

        print("filter_dict ", filter_dict)   
        # קריאה ל-Service עם ה-filter החדש
        return vdb.search_code(query, filter_dict=filter_dict)
        
    except Exception as e:
        return f"Error searching the codebase: {str(e)}"



RESEARCHER_TOOLS = [search_codebase]