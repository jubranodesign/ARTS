import os
import pickle
import re
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from rich.table import Table as RichTable
from graph.state import AgentState
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
def search_dependencies_bm25(query: str, state: AgentState) -> str:
    """
    Strict keyword-based search (BM25) to find the exact implementation and 
    source code of a specific class, method, or dependency (e.g., 'UserRepository', 'EmailService').
    Use this ONLY when you discover a dependency/import in the target file and need its source code.
    Do NOT use this for semantic searching or test pattern discovery.
    """
    print(f"🔍 Executing search_dependencies_bm25 for query: '{query}'")
    try:
        # 1. בניית הנתיב וטעינת אינדקס ה-BM25 מהדיסק
        bm25_index_path = os.path.join(DATA_DIR, "bm25_index.pkl")
        if not os.path.exists(bm25_index_path):
            return f"Error: BM25 index file not found at {bm25_index_path}. Please run ingestion first."

        with open(bm25_index_path, "rb") as f:
            dependency_retriever = pickle.load(f)
        
        # 2. הגדרת k=3 כדי לקבל מספיק תוצאות למקרה שנצטרך לסנן את קובץ המקור
        dependency_retriever.k = 3 
        
        processed_query = query.lower().strip()
        processed_query = re.sub(r'^(def|class)\s+(\w+)', r'\1_\2', processed_query)
        # 3. הרצת החיפוש מבוסס המילים (TF-IDF מתקדם)
        results = dependency_retriever.invoke(processed_query)

        if not results:
            return f"No exact dependency found for query: '{processed_query}'"
        
        # 4. שליפת נתיב קובץ המטרה מתוך ה-config.configurable שהזרקנו ב-Node
        target_file = state.get("target_file") 
        print("target_file: ", target_file)
        # 5. לוגיקת פילטור כירורגית ונרמול סלאשים (Windows vs Linux)
        best_match = None
        # הופכים את scraper_service/scraper_api.py לקו אחיד ב-lower case
        normalized_target = target_file.replace("\\", "/").lower() if target_file else ""
        print("normalized_target: ", normalized_target)
        
        for doc in results:
            # הופכים את scraper_service\\scraper_api.py לקו אחיד ב-lower case
            doc_path = doc.metadata.get("relative_path", "").replace("\\", "/").lower()
            
            # בדיקת התאמה: אם מדובר באותו הקובץ הנוכחי שהחוקר מנתח - מדלגים עליו!
            if normalized_target and (normalized_target in doc_path or doc_path in normalized_target):
                print(f"✂️ Skipping target file chunk to avoid self-duplication: {doc_path}")
                continue
                
            # אם הגענו לכאן, מצאנו את התלות החיצונית הראשונה שהיא לא קובץ המקור
            best_match = doc
            break
            
        # פולבק: אם הכל סונן, ניקח את התוצאה הראשונה
        if not best_match:
            # best_match = results[0]
            print(f"⚠️ Search concluded: No external dependencies found for query '{processed_query}' outside of the target file.")
            return f"INFO: No external dependencies discovered in the codebase for symbol: '{processed_query}'."
            
        # 6. חילוץ הנתונים מהצ'אנק הנבחר
        relative_path = best_match.metadata.get("relative_path", "Unknown path")
        source_code = best_match.page_content
    
        # print(f" source_code: {source_code}")
        # print(f"✅ Successfully selected dependency from: {relative_path}")
      
        console = Console()
        
        result_table = RichTable(show_lines=True, style="green")
        result_table.add_column("Property", style="bold magenta", width=15)
        result_table.add_column("Value", style="white")

        result_table.add_row("Query Term", processed_query)
        result_table.add_row("Relative Path", relative_path)

        # חותכים תצוגה מקדימה של הקוד כדי שלא יציף את הטרמינל
        code_preview = "\n".join(source_code.split("\n")[:10]) + "\n..." if len(source_code.split("\n")) > 10 else source_code
        result_table.add_row("Code Preview", f"[dim]{code_preview}[/dim]")

        console.print(result_table)
        # 7. החזרת פורמט נקי ומובנה שהסוכן החוקר יכול לקרוא בקלות
        return f"--- FOUND DEPENDENCY IN {relative_path} ---\n\n{source_code}\n"
        
    except Exception as e:
        print(f"❌ Error in search_dependencies_bm25: {str(e)}")
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