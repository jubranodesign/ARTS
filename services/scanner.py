import os
from pathlib import Path
from langchain_core.documents import Document

class CodeScanner:
    def __init__(self, ignored_dirs=None, allowed_extensions=None):
        # הגדרות ששמורות בתוך המופע של ה-Scanner
        self.ignored_dirs = ignored_dirs or {'__pycache__', '.venv', 'venv', '.git', 'tests', '.pytest_cache'}
        self.allowed_extensions = allowed_extensions or {'.py', ".md"}

    def scan(self, repo_path: str):
        root_path = Path(repo_path)
        final_documents = []

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                full_path = Path(root) / file
                
                if full_path.suffix in self.allowed_extensions and file != '__init__.py':
                    doc = self._process_single_file(full_path, root_path)
                    if doc:
                        final_documents.append(doc)
                    
        return final_documents

    def _process_single_file(self, full_path: Path, root_path: Path):
        """מעבד קובץ בודד והופך אותו ל-Document"""
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content.strip()) < 10:
                return None
            
            rel_path = full_path.relative_to(root_path)
            return Document(
                page_content=content,
                metadata={
                    "file_name": full_path.name,
                    "relative_path": str(rel_path),
                    "service": rel_path.parts[0] if len(rel_path.parts) > 1 else "root",
                    "file_type": self._classify_file(full_path.name)
                }
            )
        except Exception as e:
            print(f"Error reading {full_path}: {e}")
            return None

    @staticmethod
    def _classify_file(file_name: str):
        """זו מתודה סטטית - לוגיקה טהורה שלא תלויה במופע"""
        file_lower = file_name.lower()
        if "api" in file_lower or "route" in file_lower:
            return "api_endpoint"
        if "model" in file_lower or "schema" in file_lower:
            return "data_model"
        if "repo" in file_lower or "db" in file_lower:
            return "database_access"
        return "logic"