
# ייבוא השירותים שבנינו
import os
from services.document_factory import DocumentFactory
from services.scanner import CodeScanner
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService
from shared.config import DATA_DIR, REPO_PATH, VECTOR_STORE_PATH
from langchain_community.retrievers import BM25Retriever
import pickle

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

def run_ingestion():
    print("--- 🏁 The script has started! ---")
    print(f"🚀 Starting ingestion for: {REPO_PATH}")

    scanner = CodeScanner()
    factory = DocumentFactory()
    
    # משדרגים את האתחול: מעבירים את ה-provider שבחרנו (למשל mistral)
    processor = CodeProcessor(provider="mistral")
    db_service = VectorDBService()

    try:
        file_paths, root_path = scanner.scan(REPO_PATH)
        documents = []
        for path in file_paths:
            doc = factory.create_document(path, root_path)
            if doc:
                documents.append(doc)

        # שלב ב': חיתוך חכם והעשרה סמנטית (Multi-Vector)
        chunks = processor.process(documents)
        
        # --- תוספת בדיקה: הדפסת התיאורים של כל ה-Chunks שנוצרו ---
        if chunks:
            print("\n🔍 " + "="*20 + " MULTI-VECTOR CHUNKS SUMMARY REPORT " + "="*20)
            print(f"Total Chunks Generated: {len(chunks)}")
            print("-" * 76)
            
            for index, chunk in enumerate(chunks, start=1):
                file_name = chunk.metadata.get('file_name', 'unknown')
                description = chunk.page_content.replace('\n', ' ')
                original_code = chunk.metadata.get('source_code', '')
                
                # חילוץ 3 שורות ראשונות מהקוד המקורי לצורך תצוגה קצרה
                code_lines = original_code.split('\n')
                code_preview = '\n       '.join(code_lines[:3])
                
                print(f"🧩 Chunk #{index} | 📄 File: {file_name}")
                print(f"   ↳ 📌 Description: {description}")
                print(f"   ↳ 💻 Code Preview:\n       {code_preview}\n       ...")
                print("-" * 76)
                
            print("=" * 76 + "\n")
        # -----------------------------------------------------------

        # שלב ג': שמירה ל-ChromaDB
        success = db_service.save_documents(chunks)

        #  סינון טסטים לטובת ה-BM25 (כדי לחפש רק תלויות קוד נקיות)
        code_only_chunks = [c for c in chunks if not c.metadata.get("is_test", False)]
        dependency_retriever = BM25Retriever.from_documents(code_only_chunks)

        bm25_index_path = os.path.join(DATA_DIR, "bm25_index.pkl")
        with open(bm25_index_path, "wb") as f:
            pickle.dump(dependency_retriever, f)
        print(f"✅ BM25 index saved to: {bm25_index_path}")
        
        if success and dependency_retriever:
            print("\n" + "="*30)
            print("✅ INGESTION COMPLETED SUCCESSFULLY!")
            print(f"📂 Data is now persisted in: {VECTOR_STORE_PATH}")
            print("="*30)
        else:
            print("❌ Ingestion failed during database saving.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_ingestion()