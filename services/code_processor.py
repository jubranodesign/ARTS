from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

class CodeProcessor:
    def __init__(self):
        # הגדרת החותך המומחה לפייתון
        # זה מבטיח שהחיתוך יתחשב ב-def, class וכו'
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1000, 
            chunk_overlap=150  # חפיפה קטנה כדי לשמור על הקשר בין פונקציות
        )

    def process(self, documents):
        """
        מקבל רשימת Documents מהסורק ומחזיר רשימת Chunks
        """
        if not documents:
            print("⚠️ No documents to process.")
            return []

        print(f"✂️  Splitting {len(documents)} files into logical chunks...")
        chunks = self.splitter.split_documents(documents)
        print(f"✅ Created {len(chunks)} chunks ready for embedding.")
        
        return chunks