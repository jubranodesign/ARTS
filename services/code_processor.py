from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from shared.ingestion_prompts import CHUNK_SUMMARY_PROMPT
from shared.config import get_model

class CodeProcessor:
    def __init__(self, provider: str = "groq"):
        # 1. הגדרת החותך המומחה לפייתון (נשאר כפי שהיה)
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1000, 
            chunk_overlap=150
        )
        
        # 2. אתחול מודל ה-LLM עבור תהליך ה-Ingestion באמצעות ה-provider שהוזרק
        # אנו מקבעים temperature=0 כדי להבטיח תיאורים עובדתיים, מדויקים ויציבים
        print(f"🤖 CodeProcessor initializing LLM for ingestion using provider: {provider}")
        self.llm = get_model(provider=provider, temperature=0)

    def process(self, documents):
        """
        מקבל רשימת Documents מהסורק, חותך אותם לצ'אנקים, ומעשיר אותם
        במבנה Multi-Vector (התוכן הופך לתיאור, והקוד נשמר ב-Metadata).
        """
        if not documents:
            print("⚠️ No documents to process.")
            return []

        # שלב א': חיתוך גולמי של הקבצים לצ'אנקים
        print(f"✂️  Splitting {len(documents)} files into logical chunks...")
        chunks = self.splitter.split_documents(documents)
        print(f"✅ Created {len(chunks)} raw chunks. Starting semantic enrichment...")

        enriched_chunks = []

        # שלב ב': מעבר על הצ'אנקים והפיכתם ל-Multi-Vector Chunks
        for i, chunk in enumerate(chunks):
            original_code = chunk.page_content
            
            try:
                # 1. בניית הפרומפט עם קוד המקור הנוכחי
                formatted_prompt = CHUNK_SUMMARY_PROMPT.format(code_content=original_code)
                
                # 2. פנייה ל-LLM לקבלת התיאור הסמנטי
                response = self.llm.invoke(formatted_prompt)
                semantic_description = response.content.strip()
                
                # 3. ביצוע ה-Swap באובייקט ה-Chunk הקיים:
                # אנו מזריקים את קוד המקור למילון ה-Metadata
                chunk.metadata["source_code"] = original_code
                
                # אנו דורסים את ה-page_content הראשי בתיאור הסמנטי עבור ה-Embedding
                chunk.page_content = semantic_description
                
                enriched_chunks.append(chunk)
                
            except Exception as e:
                # מנגנון הגנה: אם קריאת ה-LLM נכשלת, לא שוברים את ה-Ingestion.
                # שומרים את ה-Chunk כפי שהוא (עם הקוד ב-Content) כדי שהמידע לא יאבד.
                print(f"❌ Error enriching chunk {i} in {chunk.metadata.get('file_name', 'unknown')}: {e}")
                chunk.metadata["source_code"] = original_code
                enriched_chunks.append(chunk)

        print(f"🚀 Successfully enriched {len(enriched_chunks)} chunks for Multi-Vector RAG.")
        return enriched_chunks