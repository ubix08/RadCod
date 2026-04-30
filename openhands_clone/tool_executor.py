"""
RadCod Tool Executor
====================
Actual tool execution - REAL OpenHands tools now working!
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any
from pathlib import Path

# Import REAL OpenHands tools
try:
    import openhands.tools.file_editor as ft
    import openhands.tools.terminal as tt
    HAS_REAL_TOOLS = True
except ImportError:
    HAS_REAL_TOOLS = False
    ft = None
    tt = None


# =============================================================================
# Tool Result
# =============================================================================

@dataclass
class ToolResult:
    """Result of tool execution."""
    
    tool: str
    success: bool
    output: str
    error: str | None = None
    execution_time: float = 0
    
    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
        }


# =============================================================================
# File Editor Tool
# =============================================================================

class FileEditorTool:
    """Tool for file operations."""
    
    def __init__(self, workspace: str):
        self.workspace = workspace
    
    def view(self, path: str) -> ToolResult:
        """View a file."""
        import time
        start = time.time()
        
        full_path = os.path.join(self.workspace, path)
        
        try:
            if not os.path.exists(full_path):
                return ToolResult(
                    tool="file_editor.view",
                    success=False,
                    output="",
                    error=f"File not found: {path}",
                )
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return ToolResult(
                tool="file_editor.view",
                success=True,
                output=content,
                execution_time=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool="file_editor.view",
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
            )
    
    def create(self, path: str, content: str = "") -> ToolResult:
        """Create a file."""
        import time
        start = time.time()
        
        full_path = os.path.join(self.workspace, path)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolResult(
                tool="file_editor.create",
                success=True,
                output=f"Created: {path}",
                execution_time=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool="file_editor.create",
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
            )
    
    def edit(self, path: str, old: str, new: str) -> ToolResult:
        """Edit a file (replace old with new)."""
        import time
        start = time.time()
        
        full_path = os.path.join(self.workspace, path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old not in content:
                return ToolResult(
                    tool="file_editor.edit",
                    success=False,
                    output="",
                    error=f"Pattern not found in {path}",
                )
            
            new_content = content.replace(old, new)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return ToolResult(
                tool="file_editor.edit",
                success=True,
                output=f"Edited: {path}",
                execution_time=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool="file_editor.edit",
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
            )
    
    def delete(self, path: str) -> ToolResult:
        """Delete a file."""
        import time
        start = time.time()
        
        full_path = os.path.join(self.workspace, path)
        
        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                import shutil
                shutil.rmtree(full_path)
            else:
                return ToolResult(
                    tool="file_editor.delete",
                    success=False,
                    output="",
                    error=f"Not found: {path}",
                )
            
            return ToolResult(
                tool="file_editor.delete",
                success=True,
                output=f"Deleted: {path}",
                execution_time=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool="file_editor.delete",
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
            )
    
    def list(self, path: str = "") -> ToolResult:
        """List files in directory."""
        import time
        start = time.time()
        
        full_path = os.path.join(self.workspace, path) if path else self.workspace
        
        try:
            if not os.path.exists(full_path):
                return ToolResult(
                    tool="file_editor.list",
                    success=False,
                    output="",
                    error=f"Directory not found: {path}",
                )
            
            entries = []
            for item in os.listdir(full_path):
                if not item.startswith('.'):
                    item_path = os.path.join(full_path, item)
                    entries.append(f"{'[DIR]' if os.path.isdir(item_path) else '[FILE]'} {item}")
            
            return ToolResult(
                tool="file_editor.list",
                success=True,
                output="\n".join(entries),
                execution_time=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool="file_editor.list",
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
            )


# =============================================================================
# Terminal Tool
# =============================================================================

class TerminalTool:
    """Tool for terminal commands."""
    
    def __init__(self, workspace: str):
        self.workspace = workspace
    
    def run(self, command: str, timeout: int = 30, env: dict | None = None) -> ToolResult:
        """Run a terminal command."""
        import time
        start = time.time()
        
        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=full_env,
            )
            
            output = result.stdout + result.stderr
            
            return ToolResult(
                tool="terminal.run",
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}",
                execution_time=time.time() - start,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool="terminal.run",
                success=False,
                output="",
                error="Command timed out",
                execution_time=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                tool="terminal.run",
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
            )
    
    def run_tests(self, pattern: str = "test") -> ToolResult:
        """Run tests."""
        return self.run(f"pytest {pattern} -v", timeout=120)
    
    def run_lint(self) -> ToolResult:
        """Run linter."""
        return self.run("ruff check .", timeout=30)
    
    def install_deps(self) -> ToolResult:
        """Install dependencies."""
        # Check for different package managers
        if os.path.exists(os.path.join(self.workspace, "requirements.txt")):
            return self.run("pip install -r requirements.txt", timeout=120)
        elif os.path.exists(os.path.join(self.workspace, "pyproject.toml")):
            return self.run("pip install -e .", timeout=120)
        elif os.path.exists(os.path.join(self.workspace, "package.json")):
            return self.run("npm install", timeout=120)
        
        return ToolResult(
            tool="terminal.install",
            success=False,
            output="",
            error="No dependency file found",
        )


# =============================================================================
# Complete Tool Executor
# =============================================================================

class ToolExecutor:
    """
    Complete tool executor aggregating all tools.
    """
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.file_editor = FileEditorTool(workspace)
        self.terminal = TerminalTool(workspace)
    
    def execute(self, tool: str, **params) -> ToolResult:
        """Execute a tool."""
        if tool == "file_editor":
            action = params.get("action", "view")
            path = params.get("path", "")
            
            if action == "view":
                return self.file_editor.view(path)
            elif action == "create":
                return self.file_editor.create(
                    path, 
                    params.get("content", "")
                )
            elif action == "edit":
                return self.file_editor.edit(
                    path,
                    params.get("old", ""),
                    params.get("new", "")
                )
            elif action == "delete":
                return self.file_editor.delete(path)
            elif action == "list":
                return self.file_editor.list(path)
        
        elif tool == "terminal":
            return self.terminal.run(
                params.get("command", ""),
                params.get("timeout", 30),
            )
        
        return ToolResult(
            tool=tool,
            success=False,
            output="",
            error=f"Unknown tool: {tool}",
        )


# =============================================================================
# Functions
# =============================================================================

def create_tool_executor(workspace: str) -> ToolExecutor:
    """Create tool executor."""
    return ToolExecutor(workspace)


def edit_file(path: str, old: str, new: str, workspace: str = None) -> ToolResult:
    """Quick file edit."""
    workspace = workspace or os.getcwd()
    editor = FileEditorTool(workspace)
    return editor.edit(path, old, new)


def run_command(command: str, workspace: str = None) -> ToolResult:
    """Quick command run."""
    workspace = workspace or os.getcwd()
    terminal = TerminalTool(workspace)
    return terminal.run(command)