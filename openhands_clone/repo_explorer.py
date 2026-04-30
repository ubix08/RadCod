"""
RadCod Repo Explorer
===================
Advanced repository exploration and understanding.

Capabilities:
- File tree navigation
- Code parsing and understanding
- Dependency analysis
- Pattern detection
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path


# =============================================================================
# File Node
# =============================================================================

@dataclass
class FileNode:
    """Represents a file in the repository."""
    
    path: str
    name: str
    is_dir: bool
    size: int = 0
    extension: str = ""
    language: str = ""
    content: str | None = None
    
    def to_dict(self) -> dict:
        """Serialize."""
        return {
            "path": self.path,
            "name": self.name,
            "is_dir": self.is_dir,
            "size": self.size,
            "extension": self.extension,
            "language": self.language,
        }


# =============================================================================
# Language Detection
# =============================================================================

LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".rs": "rust",
    ".vue": "vue",
    ".svelte": "svelte",
}


# =============================================================================
# Repo Explorer
# =============================================================================

class RepoExplorer:
    """
    Explore and understand repository structure.
    """
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self._file_tree: list[FileNode] = []
    
    def explore(self) -> dict:
        """Full exploration."""
        self._build_file_tree()
        
        return {
            "structure": self.get_structure(),
            "languages": self.get_languages(),
            "tests": self.get_test_files(),
            "config": self.get_config_files(),
            "main": self.find_entry_points(),
        }
    
    def _build_file_tree(self) -> None:
        """Build file tree."""
        self._file_tree = []
        
        for root, dirs, files in os.walk(self.workspace):
            # Skip hidden and common directories
            dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
            rel_root = os.path.relpath(root, self.workspace)
            
            for name in dirs:
                path = os.path.join(rel_root, name)
                self._file_tree.append(FileNode(
                    path=path,
                    name=name,
                    is_dir=True,
                ))
            
            for name in files:
                if name.startswith('.'):
                    continue
                
                path = os.path.join(rel_root, name)
                full_path = os.path.join(self.workspace, path)
                
                try:
                    size = os.path.getsize(full_path)
                except:
                    size = 0
                
                ext = Path(name).suffix
                lang = LANGUAGE_EXTENSIONS.get(ext, "")
                
                self._file_tree.append(FileNode(
                    path=path,
                    name=name,
                    is_dir=False,
                    size=size,
                    extension=ext,
                    language=lang,
                ))
    
    def _should_skip_dir(self, name: str) -> bool:
        """Check if directory should be skipped."""
        skip = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 
                'dist', 'build', '.pytest_cache', '.mypy_cache'}
        return name.startswith('.') or name in skip
    
    def get_structure(self) -> dict:
        """Get directory structure."""
        dirs = {}
        files = {}
        
        for node in self._file_tree:
            if node.is_dir:
                dirs[node.path] = node.name
            else:
                # Get parent dir
                parent = os.path.dirname(node.path)
                if parent not in files:
                    files[parent] = []
                files[parent].append(node.name)
        
        return {"dirs": dirs, "files": files}
    
    def get_languages(self) -> dict:
        """Get language statistics."""
        stats = {}
        
        for node in self._file_tree:
            if not node.is_dir and node.language:
                stats[node.language] = stats.get(node.language, 0) + 1
        
        return stats
    
    def get_test_files(self) -> list[dict]:
        """Get test files."""
        tests = []
        
        for node in self._file_tree:
            if not node.is_dir:
                name = node.name.lower()
                if any(p in name for p in ['test', '_test', 'spec']):
                    tests.append(node.to_dict())
        
        return tests
    
    def get_config_files(self) -> list[dict]:
        """Get configuration files."""
        config_names = {
            'pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt',
            'package.json', 'Cargo.toml', 'go.mod',
            '.gitignore', 'pytest.ini', 'tox.ini', 'Makefile',
            'dockerfile', '.dockerignore',
        }
        
        configs = []
        
        for node in self._file_tree:
            if not node.is_dir and node.name in config_names:
                configs.append(node.to_dict())
        
        return configs
    
    def find_entry_points(self) -> list[dict]:
        """Find entry points."""
        entry_names = {
            'main.py', 'app.py', 'index.py', 'server.py',
            'index.js', 'main.js', 'app.js',
            'main.ts', 'index.ts',
            'main.rs', 'lib.rs',
        }
        
        entries = []
        
        for node in self._file_tree:
            if not node.is_dir and node.name in entry_names:
                entries.append(node.to_dict())
        
        return entries
    
    def read_file(self, path: str) -> str:
        """Read a file."""
        full_path = os.path.join(self.workspace, path)
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"Error reading {path}: {e}"
    
    def search(self, pattern: str, file_pattern: str = "*.py") -> list[dict]:
        """Search for pattern in files."""
        import fnmatch
        
        results = []
        
        for node in self._file_tree:
            if node.is_dir:
                continue
            
            if not fnmatch.fnmatch(node.name, file_pattern):
                continue
            
            content = self.read_file(node.path)
            
            if re.search(pattern, content, re.IGNORECASE):
                # Find line numbers
                lines = content.split('\n')
                line_nums = [
                    i+1 for i, line in enumerate(lines)
                    if re.search(pattern, line, re.IGNORECASE)
                ]
                
                results.append({
                    "file": node.path,
                    "matches": len(line_nums),
                    "lines": line_nums[:10],  # First 10
                })
        
        return results


# =============================================================================
# Code Parser
# =============================================================================

class CodeParser:
    """Parse code for structure and dependencies."""
    
    @staticmethod
    def parse_imports(code: str) -> list[str]:
        """Parse imports from code."""
        imports = []
        
        # Python imports
        py_imports = re.findall(r'^import\s+(\S+)', code, re.MULTILINE)
        py_from = re.findall(r'^from\s+(\S+)\s+import', code, re.MULTILINE)
        
        imports.extend(py_imports)
        imports.extend(py_from)
        
        return list(set(imports))
    
    @staticmethod
    def parse_functions(code: str) -> list[dict]:
        """Parse functions."""
        functions = []
        
        # Python functions
        for match in re.finditer(r'def\s+(\w+)\s*\((.*?)\):', code):
            functions.append({
                "name": match.group(1),
                "params": match.group(2),
                "line": code[:match.start()].count('\n') + 1,
            })
        
        return functions
    
    @staticmethod
    def parse_classes(code: str) -> list[dict]:
        """Parse classes."""
        classes = []
        
        for match in re.finditer(r'class\s+(\w+)\s*[\(:](.*?)[\(:]', code):
            classes.append({
                "name": match.group(1),
                "bases": match.group(2).strip(),
                "line": code[:match.start()].count('\n') + 1,
            })
        
        return classes
    
    @staticmethod
    def parse_docstring(code: str, line: int) -> str | None:
        """Parse docstring at line."""
        lines = code.split('\n')
        
        if line > len(lines):
            return None
        
        # Look for docstring
        start = line - 1
        while start < len(lines) and '"""' not in lines[start] and "'''" not in lines[start]:
            start += 1
        
        if start >= len(lines):
            return None
        
        quote = '"""' if '"""' in lines[start] else "'''"
        start += 1
        
        end = start
        while end < len(lines) and quote not in lines[end]:
            end += 1
        
        return '\n'.join(lines[start:end]).strip()


# =============================================================================
# Functions
# =============================================================================

def explore_repo(workspace: str) -> dict:
    """Explore repository."""
    return RepoExplorer(workspace).explore()


def search_code(workspace: str, pattern: str) -> list[dict]:
    """Search code in repository."""
    return RepoExplorer(workspace).search(pattern)


def parse_file(path: str) -> dict:
    """Parse a file's structure."""
    explorer = RepoExplorer(os.path.dirname(path))
    code = explorer.read_file(path)
    
    return {
        "imports": CodeParser.parse_imports(code),
        "functions": CodeParser.parse_functions(code),
        "classes": CodeParser.parse_classes(code),
    }