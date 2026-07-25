
# ייבוא השירותים שבנינו
import os
from langchain_core.documents import Document
from services.document_factory import DocumentFactory
from services.scanner import CodeScanner
from services.code_processor import CodeProcessor
from services.vector_db_service import VectorDBService
from shared.config import DATA_DIR, VECTOR_STORE_PATH
from shared.paths import get_repo_path, get_repo_seed_path
from langchain_community.retrievers import BM25Retriever
import pickle
from utils.retrieval import prepare_bm25_documents, print_chunks_summary, python_code_tokenizer
from shared.ingestion_prompts import SEED_SUMMARY_PROMPT, CHUNK_SUMMARY_PROMPT

def run_ingestion(
    vdb: VectorDBService,
    provider="mistral",
    prompt=CHUNK_SUMMARY_PROMPT,
    is_test=False,
    repo_path: str | None = None,
    processor=None,
):
    print("--- 🏁 The script has started! ---")
    resolved_repo = repo_path or get_repo_path()
    print(f"🚀 Starting ingestion for: {resolved_repo} (Mode: {'Test/Seed' if is_test else 'Source Code'})")

    scanner = CodeScanner()
    factory = DocumentFactory()
    proc = processor or CodeProcessor(provider=provider, summary_prompt=prompt)

    try:
        # שלב א': סריקה ויצירת מסמכי בסיס
        file_paths, root_path = scanner.scan(resolved_repo)
        documents = [factory.create_document(p, root_path, is_test=is_test) for p in file_paths if factory.create_document(p, root_path)]

        # שלב ב': חיתוך חכם והעשרה סמנטית (Multi-Vector)
        chunks = proc.process(documents)
        
        # הדפסת דוח Chunks (הוצא לקובץ חיצוני)
        print_chunks_summary(chunks)

        # שלב ג': שמירה ל-ChromaDB (החיפוש הסמנטי - רץ תמיד עבור שניהם)
        success = vdb.save_documents(chunks)

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
    import argparse

    from dotenv import load_dotenv

    from shared.repo_cli import add_repo_path_argument, resolve_repo_path

    load_dotenv()
    parser = argparse.ArgumentParser(description="Ingest repository code into the vector store.")
    add_repo_path_argument(parser)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Ingest the full source repository (default: seed/test data under seed_data).",
    )
    args = parser.parse_args()
    repo_root = resolve_repo_path(args.repo_path)
    if args.full:
        ingest_path = repo_root
        is_test = False
    else:
        ingest_path = get_repo_seed_path(repo_root)
        is_test = True

    vdb = VectorDBService()
    processor = CodeProcessor(provider="mistral", summary_prompt=SEED_SUMMARY_PROMPT)
    run_ingestion(
        vdb=vdb,
        provider="mistral",
        prompt=SEED_SUMMARY_PROMPT,
        is_test=is_test,
        repo_path=ingest_path,
        processor=processor,
    )
