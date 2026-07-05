
# ייבוא השירותים שבנינו
import os
from langchain_core.documents import Document
from services.document_factory import DocumentFactory
from services.scanner import CodeScanner
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService
from shared.config import DATA_DIR, REPO_PATH, VECTOR_STORE_PATH, REPO_SEED_PATH
from langchain_community.retrievers import BM25Retriever
import pickle
from utils.retrieval import prepare_bm25_documents, print_chunks_summary, python_code_tokenizer
from shared.ingestion_prompts import SEED_SUMMARY_PROMPT, CHUNK_SUMMARY_PROMPT

# def run_ingestion():
#     print("--- 🏁 The script has started! ---")
#     print(f"🚀 Starting ingestion for: {REPO_PATH}")

#     scanner = CodeScanner()
#     factory = DocumentFactory()
    
#     # משדרגים את האתחול: מעבירים את ה-provider שבחרנו (למשל gemini)
#     processor = CodeProcessor(provider="mistral")
#     db_service = VectorDBService()

#     try:
#         file_paths, root_path = scanner.scan(REPO_PATH)
#         documents = []
#         for path in file_paths:
#             doc = factory.create_document(path, root_path)
#             if doc:
#                 documents.append(doc)

#         # שלב ב': חיתוך חכם והעשרה סמנטית (Multi-Vector)
#         chunks = processor.process(documents)
        
#         # --- תוספת בדיקה והדפסה של המבנה החדש ---
#         if chunks:
#             print("\n🔍 --- Multi-Vector Structure Verification ---")
#             sample_chunk = chunks[0] # לוקחים את הצ'אנק הראשון לדוגמה
#             print(f"📄 File Name: {sample_chunk.metadata.get('file_name')}")
#             print(f"📌 Page Content (What is vectorized - Child):")
#             print(f"   ↳ \"{sample_chunk.page_content}\"")
#             print(f"💻 Metadata Source Code (What the LLM gets - Parent):")
#             # מדפיסים רק את 5 השורות הראשונות של הקוד כדי לא להציף את הטרמינל
#             code_lines = sample_chunk.metadata.get('source_code', '').split('\n')
#             preview_code = '\n   '.join(code_lines[:5])
#             print(f"   ↳ {preview_code}\n   ... (truncated)")
#             print("-------------------------------------------\n")
#         # ----------------------------------------

#         # שלב ג': שמירה ל-ChromaDB
#         success = db_service.save_documents(chunks)

#         if success:
#             print("\n" + "="*30)
#             print("✅ INGESTION COMPLETED SUCCESSFULLY!")
#             print(f"📂 Data is now persisted in: {VECTOR_STORE_PATH}")
#             print("="*30)
#         else:
#             print("❌ Ingestion failed during database saving.")

#     except Exception as e:
#         print(f"❌ An unexpected error occurred: {e}")

def run_ingestion(provider="mistral", prompt=CHUNK_SUMMARY_PROMPT, is_test=False, repo_path=REPO_PATH):
    print("--- 🏁 The script has started! ---")
    print(f"🚀 Starting ingestion for: {repo_path} (Mode: {'Test/Seed' if is_test else 'Source Code'})")

    scanner = CodeScanner()
    factory = DocumentFactory()
    processor = CodeProcessor(provider=provider, summary_prompt=prompt)
    db_service = VectorDBService()

    try:
        # שלב א': סריקה ויצירת מסמכי בסיס
        file_paths, root_path = scanner.scan(repo_path)
        documents = [factory.create_document(p, root_path, is_test=is_test) for p in file_paths if factory.create_document(p, root_path)]

        # שלב ב': חיתוך חכם והעשרה סמנטית (Multi-Vector)
        chunks = processor.process(documents)
        
        # הדפסת דוח Chunks (הוצא לקובץ חיצוני)
        print_chunks_summary(chunks)

        # שלב ג': שמירה ל-ChromaDB (החיפוש הסמנטי - רץ תמיד עבור שניהם)
        success = db_service.save_documents(chunks)

        # 🎯 שלב ד' + ה': בניית אינדקס מילות מפתח ושמירה לדיסק - רק עבור קוד מקור!
        dependency_retriever = None
        if not is_test:
            print("🔍 Building BM25 keyword index for source code...")
            bm25_documents = prepare_bm25_documents(chunks)
            
            dependency_retriever = BM25Retriever.from_documents(
                bm25_documents,
                preprocess_func=python_code_tokenizer
            )

            # שמירה לדיסק
            bm25_index_path = os.path.join(DATA_DIR, "bm25_index.pkl")
            with open(bm25_index_path, "wb") as f:
                pickle.dump(dependency_retriever, f)
            print(f"✅ BM25 index saved to: {bm25_index_path}")
        else:
            print("ℹ️ Skipping BM25 indexing (Not required for Seed/Test data).")

        # בדיקת הצלחה מותאמת למצב הריצה
        is_successful = success and (is_test or dependency_retriever is not None)

        if is_successful:
            print("\n" + "="*30)
            print("✅ INGESTION COMPLETED SUCCESSFULLY!")
            print(f"📂 Data is now persisted in: {VECTOR_STORE_PATH}")
            print("="*30)
        else:
            print("❌ Ingestion failed during database saving.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")


if __name__ == "__main__":
    # run_ingestion(provider="mistral", prompt=CHUNK_SUMMARY_PROMPT, is_test=False, repo_path=REPO_PATH)
    run_ingestion(provider="mistral", prompt=SEED_SUMMARY_PROMPT, is_test=True, repo_path=REPO_SEED_PATH)
#     import pickle

# # 1. טען את קובץ ה-pkl הנוכחי שלך מהדיסק
# bm25_index_path = os.path.join(DATA_DIR, "bm25_index.pkl")
# with open(bm25_index_path, "rb") as f:
#     retriever = pickle.load(f)

# # 2. קח מחרוזת קוד פשוטה ובדוק איך ה-Retriever הנוכחי מפרק אותה
# test_code = "def save_study(session, study_data):"

# # הפעלת הטוקנייזר הפנימי של לנגצ'יין
# tokens = retriever.preprocess_func(test_code)

# print("--- 🔍 CURRENT TOKENS RESULT ---")
# print(tokens)
