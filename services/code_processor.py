import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from shared.ingestion_prompts import CHUNK_SUMMARY_PROMPT
from shared.llm_factory import get_model

logger = logging.getLogger(__name__)


class CodeProcessor:
    def __init__(self, provider: str = "groq", summary_prompt=CHUNK_SUMMARY_PROMPT):
        # 1. הגדרת החותך המומחה לפייתון (נשאר כפי שהיה)
        self.splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.PYTHON,
            chunk_size=1000, 
            chunk_overlap=150
        )
        
        # 2. אתחול מודל ה-LLM עבור תהליך ה-Ingestion באמצעות ה-provider שהוזרק
        # אנו מקבעים temperature=0 כדי להבטיח תיאורים עובדתיים, מדויקים ויציבים
        logger.info("CodeProcessor initializing LLM for ingestion using provider: %s", provider)
        self.llm = get_model(provider=provider, temperature=0)
        self.summary_prompt = summary_prompt

    def process(self, documents):
        """
        מקבל רשימת Documents מהסורק, חותך אותם לצ'אנקים, ומעשיר אותם
        במבנה Multi-Vector (התוכן הופך לתיאור, והקוד נשמר ב-Metadata).
        """
        if not documents:
            logger.warning("No documents to process.")
            return []

        # שלב א': חיתוך גולמי של הקבצים לצ'אנקים
        logger.info("Splitting %s files into logical chunks...", len(documents))
        chunks = self.splitter.split_documents(documents)
        logger.info("Created %s raw chunks. Starting semantic enrichment...", len(chunks))

        enriched_chunks = []

        # שלב ב': מעבר על הצ'אנקים והפיכתם ל-Multi-Vector Chunks
        for i, chunk in enumerate(chunks):
            original_code = chunk.page_content
            
            try:
                # 1. בניית הפרומפט עם קוד המקור הנוכחי
                formatted_prompt = self.summary_prompt.format(code_content=original_code)
                
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
                logger.error(
                    "Error enriching chunk %s in %s: %s",
                    i,
                    chunk.metadata.get("file_name", "unknown"),
                    e,
                )
                chunk.metadata["source_code"] = original_code
                enriched_chunks.append(chunk)

        logger.info("Successfully enriched %s chunks for Multi-Vector RAG.", len(enriched_chunks))
        return enriched_chunks