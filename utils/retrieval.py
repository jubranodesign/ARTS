import io
import re
import tokenize

# def python_code_tokenizer(text: str) -> list[str]:
#     tokens = []
#     try:
#         # פירוק הקוד בצורה נייטיבית לפי חוקי השפה
#         for tok in tokenize.tokenize(io.BytesIO(text.encode('utf-8')).readline):
#             # שומרים רק שמות (משתנים/פונקציות/מחלקות) או ערכים
#             if tok.type in (tokenize.NAME, tokenize.STRING, tokenize.NUMBER):
#                 tokens.append(tok.string.lower())
#     except Exception:
#         # פולבק בטוח למקרה של בעיית סינטקס
#         import re
#         return re.findall(r'\b\w+\b', text.lower())
#     return tokens

def python_code_tokenizer(text: str) -> list[str]:
    tokens = []
    try:
        raw_tokens = list(tokenize.tokenize(io.BytesIO(text.encode('utf-8')).readline))
        
        for i, tok in enumerate(raw_tokens):
            if tok.type in (tokenize.NAME, tokenize.STRING, tokenize.NUMBER):
                token_str = tok.string.lower()
                tokens.append(token_str)
                
                # 🎯 הקסם: אם הטוקן הנוכחי הוא 'def' או 'class', ניצור טוקן משולב עם המילה הבאה!
                if token_str in ('def', 'class') and (i + 1) < len(raw_tokens):
                    next_tok = raw_tokens[i + 1]
                    if next_tok.type == tokenize.NAME:
                        # יוצר טוקן ייחודי כמו 'def_save_study' או 'def_get_session'
                        tokens.append(f"{token_str}_{next_tok.string.lower()}")
                        
    except Exception:
        # פולבק מבוסס Regex למקרה של כשל סינטקטי
        words = re.findall(r'\b\w+\b', text.lower())
        tokens.extend(words)
        # מייצרים ביגרמים בסיסיים בפולבק במידה ויש def
        for i in range(len(words) - 1):
            if words[i] in ('def', 'class'):
                tokens.append(f"{words[i]}_{words[i+1]}")
                
    return tokens

from langchain_core.documents import Document

def prepare_bm25_documents(chunks: list) -> list[Document]:
    """
    Filters out test files, strips source_code from metadata to save memory,
    and returns a clean list of LangChain Document objects indexed by raw source code.
    """
    code_only_chunks = [c for c in chunks if not c.metadata.get("is_test", False)]
    bm25_documents = []
    
    for doc in code_only_chunks:
        actual_code = doc.metadata.get("source_code", "")
        if actual_code:
            clean_metadata = doc.metadata.copy()
            if "source_code" in clean_metadata:
                del clean_metadata["source_code"]
                
            bm25_documents.append(
                Document(page_content=actual_code, metadata=clean_metadata)
            )
            
    return bm25_documents

def print_chunks_summary(chunks: list) -> None:
    """Prints a clean visual summary of the generated chunks."""
    if not chunks:
        return
        
    print("\n🔍 " + "="*20 + " MULTI-VECTOR CHUNKS SUMMARY REPORT " + "="*20)
    print(f"Total Chunks Generated: {len(chunks)}")
    print("-" * 76)
    
    for index, chunk in enumerate(chunks, start=1):
        file_name = chunk.metadata.get('file_name', 'unknown')
        description = chunk.page_content.replace('\n', ' ')
        original_code = chunk.metadata.get('source_code', '')
        relative_path = chunk.metadata.get('relative_path', 'unknown')
        
        code_lines = original_code.split('\n')
        code_preview = '\n       '.join(code_lines[:3])
        
        print(f"🧩 Chunk #{index} | 📄 File: {file_name} | relative_path: {relative_path} ")
        print(f"   ↳ 📌 Description: {description}")
        print(f"   ↳ 💻 Code Preview:\n       {code_preview}\n       ...")
        print("-" * 76)
        
    print("=" * 76 + "\n")