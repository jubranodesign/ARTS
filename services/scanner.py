import os
from pathlib import Path

class CodeScanner:
    def __init__(self, ignored_dirs=None, allowed_extensions=None):
        self.ignored_dirs = ignored_dirs or {'__pycache__', '.venv', 'venv', '.git', 'tests', '.pytest_cache', 'seed_data'}
        self.allowed_extensions = allowed_extensions or {'.py', ".md"}

    def scan(self, repo_path: str):
        root_path = Path(repo_path)
        file_paths = []

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                full_path = Path(root) / file
                if full_path.suffix in self.allowed_extensions and file != '__init__.py':
                    file_paths.append(full_path)
                    
        return file_paths, root_path