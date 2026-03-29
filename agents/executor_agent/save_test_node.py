from pathlib import Path
from langgraph.graph.state import RunnableConfig
from graph.state import AgentState
from services.code_processor import CodeProcessor
from services.document_factory import DocumentFactory
from services.vector_db_service import VectorDBService
from shared.config import REPO_PATH


def save_test_node(state: AgentState, config: RunnableConfig):

    db_service =config.get("configurable", {}).get("vdb") or VectorDBService()
    processor = config.get("configurable", {}).get("processor") or CodeProcessor()

    # 1. בדיקה שהטסט באמת עבר ב-State
    if state.get("test_run_status") != "passed":
        return state

    # 2. הכנת הנתיבים (שימוש בנתיב המלא לקריאה מהדיסק)
    rel_path = state.get("test_file_path")
    if not rel_path:
        return state
        
    full_path = Path(REPO_PATH) / rel_path
    root_path = Path(REPO_PATH)

    # 3. הקריאה המדויקת ל-Factory
    # שים לב: אנחנו מעבירים את הנתיבים ואת ה-Flag של ה-is_test
    doc = DocumentFactory.create_document(
        full_path=full_path,
        root_path=root_path,
        is_test=True,
        extra_metadata={"test_status": "passed"}
    )

    # 4. עיבוד ושמירה ב-Vector DB
    if doc:
        # כאן ה-Processor חותך את ה-Document ל-Chunks
        chunks = processor.process([doc])
        print("save_test_node chunks: ", chunks)

        # וה-DB Service שומר אותם ב-ChromaDB
        db_service.save_documents(chunks)
        print(f"✨ Self-Feeding: Successfully indexed new test: {rel_path}")

    return state