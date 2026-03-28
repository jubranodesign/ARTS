import os
from pathlib import Path
from langchain_core.documents import Document

class DocumentFactory:
    """
    השירות האחראי על הפיכת קבצי קוד לאובייקטי Document עשירים במטא-דאטה.
    """
    
    @staticmethod
    def create_document(full_path: Path, root_path: Path, is_test: bool = False, extra_metadata: dict = None) -> Document:
        """
        יוצר Document מקובץ בודד עם לוגיקה של סיווג ומטא-דאטה.
        """
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # בדיקת מינימום תוכן (מניעת הכנסת קבצים ריקים)
            if len(content.strip()) < 10:
                return None
            
            rel_path = full_path.relative_to(root_path)
            
            # בניית מטא-דאטה בסיסי
            metadata = {
                "file_name": full_path.name,
                "relative_path": str(rel_path),
                "service": rel_path.parts[0] if len(rel_path.parts) > 1 else "root",
                "file_type": DocumentFactory._classify_file(full_path.name, is_test),
                "is_test": is_test
            }
            
            # הזרקת מטא-דאטה נוסף (למשל מהגרף - סטטוס טסט, זמן ריצה וכו')
            if extra_metadata:
                metadata.update(extra_metadata)
                
            return Document(page_content=content, metadata=metadata)
            
        except Exception as e:
            print(f"❌ DocumentFactory Error reading {full_path}: {e}")
            return None

    @staticmethod
    def _classify_file(file_name: str, is_test: bool) -> str:
        """
        מסווג את סוג הקובץ לפי השם והקשר (Context).
        """
        if is_test or file_name.lower().startswith("test_"):
            return "unit_test"
            
        file_lower = file_name.lower()
        if "api" in file_lower or "route" in file_lower:
            return "api_endpoint"
        if "model" in file_lower or "schema" in file_lower:
            return "data_model"
        if "repo" in file_lower or "db" in file_lower:
            return "database_access"
            
        return "logic_component"