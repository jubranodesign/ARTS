import os
from dotenv import load_dotenv

# ייבוא השירותים שבנינו
from services.document_factory import DocumentFactory
from services.scanner import CodeScanner
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService
from shared.config import REPO_PATH, VECTOR_STORE_PATH


def run_ingestion():
    print("--- 🏁 The script has started! ---")
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found. Check your .env file.")
        return

    print(f"🚀 Starting ingestion for: {REPO_PATH}")

    scanner = CodeScanner()
    factory = DocumentFactory()
    processor = CodeProcessor()
    db_service = VectorDBService()

    try:
        file_paths, root_path = scanner.scan(REPO_PATH)
        documents = []
        for path in file_paths:
            doc = factory.create_document(path, root_path)
            if doc:
                documents.append(doc)

        # שלב ב': חיתוך חכם (Splitting) לפי שפת Python
        chunks = processor.process(documents)
        print("chunks: ", chunks)
        # שלב ג': שמירה ל-ChromaDB (כאן נוצרת תיקיית data/vector_store)
        success = db_service.save_documents(chunks)

        if success:
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