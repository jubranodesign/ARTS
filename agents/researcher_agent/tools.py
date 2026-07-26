import logging
import os
import pickle
import re

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from graph.state import AgentState
from shared.paths import DATA_DIR
from shared.paths import normalize_relative_path

logger = logging.getLogger(__name__)


@tool
def search_dependencies_bm25(query: str, state: AgentState) -> str:
    """
    Strict keyword-based search (BM25) to find the exact implementation and 
    source code of a specific class, method, or dependency (e.g., 'UserRepository', 'EmailService').
    Use this ONLY when you discover a dependency/import in the target file and need its source code.
    Do NOT use this for semantic searching or test pattern discovery.
    """
    logger.info("Executing search_dependencies_bm25 for query: %r", query)
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
        logger.debug("target_file: %s", target_file)
        # 5. לוגיקת פילטור כירורגית ונרמול סלאשים (Windows vs Linux)
        best_match = None
        # הופכים את scraper_service/scraper_api.py לקו אחיד ב-lower case
        normalized_target = normalize_relative_path(target_file, lowercase=True)
        logger.debug("normalized_target: %s", normalized_target)
        
        for doc in results:
            doc_path = normalize_relative_path(
                doc.metadata.get("relative_path", ""), lowercase=True
            )
            
            # בדיקת התאמה: אם מדובר באותו הקובץ הנוכחי שהחוקר מנתח - מדלגים עליו!
            if normalized_target and (normalized_target in doc_path or doc_path in normalized_target):
                logger.debug("Skipping target file chunk to avoid self-duplication: %s", doc_path)
                continue
                
            # אם הגענו לכאן, מצאנו את התלות החיצונית הראשונה שהיא לא קובץ המקור
            best_match = doc
            break
            
        # פולבק: אם הכל סונן, ניקח את התוצאה הראשונה
        if not best_match:
            logger.warning(
                "Search concluded: no external dependencies for query %r outside target file",
                processed_query,
            )
            return f"INFO: No external dependencies discovered in the codebase for symbol: '{processed_query}'."
            
        # 6. חילוץ הנתונים מהצ'אנק הנבחר
        relative_path = best_match.metadata.get("relative_path", "Unknown path")
        source_code = best_match.page_content
      
        code_preview = (
            "\n".join(source_code.split("\n")[:10]) + "\n..."
            if len(source_code.split("\n")) > 10
            else source_code
        )
        logger.debug(
            "BM25 dependency match: query=%s relative_path=%s code_preview=%s",
            processed_query,
            relative_path,
            code_preview,
        )
        # 7. החזרת פורמט נקי ומובנה שהסוכן החוקר יכול לקרוא בקלות
        return f"--- FOUND DEPENDENCY IN {relative_path} ---\n\n{source_code}\n"
        
    except Exception as e:
        logger.error("Error in search_dependencies_bm25: %s", e)
        return f"Error during dependency search: {str(e)}"

@tool
def search_golden_tests_semantic(query: str, config: RunnableConfig = None) -> str:
    """
    Semantic search over the test suite to discover existing test patterns and "Golden Examples" (Seed Data).
    Use this tool ONLY to find how similar features, infrastructure workflows, or code logic are tested 
    elsewhere in the project (e.g., how to mock context managers, database sessions, or third-party APIs).
    
    Do NOT use this tool to discover production/source code implementations.
    
    Args:
        query: Semantic description of the testing pattern or mock architecture you need (e.g., 'mocking database context manager with block').
    
    RETURNS: A formatted string of reference test code chunks (Golden Seeds).
    """
    logger.debug("search_golden_tests_semantic query: %s", query)
    try:
        vdb = config["configurable"]["vdb"]
        
        # 🎯 נעול קשיח במטא-דטה: מחפש אך ורק דוגמאות בדיקה ו-Seeds
        filter_dict = {"is_test": True}
        
        return vdb.search_code(query, filter_dict=filter_dict)
        
    except Exception as e:
        return f"Error searching the golden tests: {str(e)}"

@tool
def search_source_code_semantic(query: str, config: RunnableConfig = None) -> str:
    """
    Semantic search over the production/source code repository to discover logical features and business logic.
    Use this tool ONLY when you need to understand *what* the application logic achieves from a conceptual perspective
    and a simple keyword search (BM25) is insufficient.
    
    Do NOT use this tool to find test examples or mock structures (use search_golden_tests_semantic instead).
    
    Args:
        query: Semantic description of the functional business logic you are searching for (e.g., 'user authentication token generation').
    
    RETURNS: A formatted string of production code chunks.
    """
    logger.debug("search_source_code_semantic query: %s", query)
    try:
        vdb = config["configurable"]["vdb"]
        
        # 🎯 נעול קשיח במטא-דטה: מחפש אך ורק קוד מקור של האפליקציה
        filter_dict = {"is_test": False}
        
        return vdb.search_code(query, filter_dict=filter_dict)
        
    except Exception as e:
        return f"Error searching the source code: {str(e)}"

RESEARCHER_TOOLS = [search_dependencies_bm25, search_golden_tests_semantic, search_source_code_semantic]
