import os
import pickle
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from services.vector_db_service import VectorDBService
from shared.config import DATA_DIR

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
def search_dependencies_bm25(query: str) -> str:
    """
    Strict keyword-based search (BM25) to find the exact implementation and 
    source code of a specific class, method, or dependency (e.g., 'UserRepository', 'EmailService').
    Use this ONLY when you discover a dependency/import in the target file and need its source code.
    Do NOT use this for semantic searching or test pattern discovery.
    """
    print("search_dependencies_bm25 query ", query)
    try:
        bm25_index_path = os.path.join(DATA_DIR, "bm25_index.pkl")
        # 1. טעינת אינדקס ה-BM25 מהדיסק
        with open(bm25_index_path, "rb") as f:
            dependency_retriever = pickle.load(f)
        print(f"✅ BM25 index loaded from: {bm25_index_path}")
        # 2. הגדרת כמות התוצאות הרצויה (לרוב 1-2 תוצאות מדויקות זה מעל ומעבר לתלות ספציפית)
        dependency_retriever.k = 1 
        
        # 3. הרצת החיפוש המבוסס מילים
        results = dependency_retriever.invoke(query)
        print("search_dependencies_bm25 results ", results)
        if not results:
            return f"No exact dependency found for query: '{query}'"
        
        # 4. חילוץ הנתונים מהצ'אנק המוביל
        best_match = results[0]
        file_path = best_match.metadata.get("file_path", "Unknown path")
        source_code = best_match.metadata.get("source_code", "No source code available")
        print("search_dependencies_bm25 file_path ", file_path)
        print("search_dependencies_bm25 source_code ", source_code)
        # 5. החזרת פורמט נקי ומובנה שהסוכן החוקר יכול לקרוא בקלות
        return f"--- FOUND DEPENDENCY IN {file_path} ---\n\n{source_code}\n"
        
    except FileNotFoundError:
        return "Error: BM25 index file ('bm25_index.pkl') not found. Please run the ingestion process first."
    except Exception as e:
        return f"Error during dependency search: {str(e)}"

@tool
def search_golden_tests_semantic(query: str, search_type: str = "code_only", config: RunnableConfig = None) -> str:
    """
    Semantic search over the codebase to discover existing test patterns and "Golden Examples".
    Use this tool ONLY to find how similar features, workflows, or code logic are tested elsewhere 
    in the project.
    
    Do NOT use this tool to find core file implementations or source code dependencies (use search_dependencies_bm25 instead).
    
    Args:
        query: Semantic description of the logic or test pattern you are looking for (e.g., 'how to test async web scrapers').
        search_type: Hardcoded to 'tests_only' to filter out production code and focus strictly on test files.
    
    RETURNS: A formatted string of reference test code chunks.
    """
    print("search_golden_tests_semantic query ", query)
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



RESEARCHER_TOOLS = [search_dependencies_bm25, search_golden_tests_semantic]