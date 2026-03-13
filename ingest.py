import os
from dotenv import load_dotenv

# ייבוא השירותים שבנינו
from services.scanner import CodeScanner
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService
from shared.config import REPO_PATH, VECTOR_STORE_PATH, get_embeddings_model

def run_ingestion():
    print("--- 🏁 The script has started! ---") # תוסיף את זה
    # 1. טעינת משתני סביבה (API Key)
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found. Check your .env file.")
        return

    
    print(f"🚀 Starting ingestion for: {REPO_PATH}")

    # 3. אתחול מודל ה-Embedding (הזרקת תלויות)
    # אנחנו משתמשים במודל 004 המעודכן של גוגל
    embeddings_model = get_embeddings_model()

    # 4. אתחול השירותים
    scanner = CodeScanner()
    processor = CodeProcessor()
    # מזריקים את ה-embeddings ל-DB Service
    db_service = VectorDBService(embeddings=embeddings_model)

    try:
        # שלב א': סריקת הקבצים (מחזיר Documents)
        raw_documents = scanner.scan(REPO_PATH)
        if not raw_documents:
            print("⚠️ No documents found to process. Exiting.")
            return

        # שלב ב': חיתוך חכם (Splitting) לפי שפת Python
        chunks = processor.process(raw_documents)

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