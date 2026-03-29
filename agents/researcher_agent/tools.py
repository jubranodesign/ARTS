from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from services.vector_db_service import VectorDBService

@tool
def search_codebase(query: str, config: RunnableConfig) -> str:
   """
    Search the project's source code for snippets and their relative paths.
    Use this tool to find logic, classes, or specific files.
    RETURNS: A list of code chunks. Each chunk starts with 'FILE: path/to/file.py'.

     Args:
      query: A search term. Best results come from using function names, 
           class names, or filenames WITHOUT the path/extension 
           (e.g., use 'scraper_api' instead of 'scraper_service/scraper_api.py').
   """
   try:
        # שליפת המופע מהקונפיג
        vdb = config.get("configurable", {}).get("vdb") or VectorDBService()
        # הקריאה פשוטה כי ה-Service כבר מחזיר מחרוזת מעובדת (Formatted String)
        return vdb.search_code(query)
        
   except Exception as e:
        return f"Error searching the codebase: {str(e)}"





RESEARCHER_TOOLS = [search_codebase]