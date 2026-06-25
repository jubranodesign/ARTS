import os
from langchain_chroma import Chroma
from shared.config import VECTOR_STORE_PATH, get_embeddings_model

class VectorDBService:
    _instance = None
    _db = None

    def __new__(cls, *args, **kwargs):
        print("Init VectorDBService Instance")
        if cls._instance is None:
            print("Set VectorDBService Instance")
            cls._instance = super(VectorDBService, cls).__new__(cls)
            cls._initialize_db()
        return cls._instance

    @classmethod
    def _initialize_db(cls):
        """
        אתחול המופע של Chroma. 
        גם אם התיקייה לא קיימת, Chroma ייצור אותה ברגע שנחבר אותו לנתיב.
        """
        print(f"📡 Initializing Chroma connection at: {VECTOR_STORE_PATH}")
        cls._db = Chroma(
            collection_name="codebase_index",
            persist_directory=VECTOR_STORE_PATH,
            embedding_function=get_embeddings_model()
        )

    @property
    def db(self):
        return self._db

    def save_documents(self, chunks: list):
        """
        שימוש ב-add_documents בלבד. 
        אין יצירה מחדש של אובייקט ה-Chroma.
        """
        if not chunks:
            print("⚠️ No chunks provided to save.")
            return False
            
        try:
            print(f"➕ Adding {len(chunks)} chunks to the vector store...")
            self.db.add_documents(chunks)
            print("✅ Data persisted successfully.")
            return True
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False

    def search_code(self, query: str, k: int = 5, filter_dict: dict = None) -> str:
        """חיפוש סמנטי דרך המופע הקיים"""
        # בדיקה אם ה-DB מכיל נתונים (אופציונלי)
        if self.db._collection.count() == 0:
            return "🔍 Database is currently empty."

        docs = self.db.similarity_search(query, k=k, filter=filter_dict)
        
        formatted_results = []
        # for i, doc in enumerate(docs):
        #     source = doc.metadata.get("relative_path", "Unknown")
        #     formatted_results.append(f"--- RESULT {i+1} | FILE: {source} ---\n{doc.page_content}")
        for i, doc in enumerate(docs):
          metadata = doc.metadata
          source = metadata.get("relative_path", "Unknown")
          source_code = doc.metadata.get("source_code", "")
          
           # חילוץ המטא-דאטה החדש
          is_test = metadata.get("is_test", False)
          test_status = metadata.get("test_status", "N/A")
          file_type = metadata.get("file_type", "code")

           # בניית Header עשיר במידע
          header = f"--- RESULT {i+1} | FILE: {source} | TYPE: {file_type} | IS_TEST: {is_test} | STATUS: {test_status} ---"
          des = f"DESCRIPTION: {doc.page_content}"

        formatted_results.append(f"{header}\n{des}\n{source_code}" )
        print("search_code formatted_results: ")
        print("\n\n".join(formatted_results))
        return "\n\n".join(formatted_results)

    def clear_db(self):
        """מחיקת כל הנתונים בלי להרוס את האובייקט"""
        ids = self.db._collection.get()['ids']
        if ids:
            self.db._collection.delete(ids)
            print("🗑️ Database cleared.")