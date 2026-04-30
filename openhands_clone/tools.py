"""
OpenHands-Clone Custom Tools
===========================
Custom tool implementations for the coding agent.

This module provides custom tools that work outside the broken openhands-tools package.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from openhands.sdk.tool import Tool, ToolDefinition
from pydantic import Field


# =============================================================================
# Tool Definitions
# =============================================================================

class TerminalToolDefinition(ToolDefinition):
    """Tool for running terminal commands."""
    
    name: str = "terminal"
    description: str = "Run terminal commands and get output"
    
    def action_from_arguments(self, command: str) -> "TerminalAction":
        return TerminalAction(command=command)


class TerminalAction:
    """Terminal command execution."""
    
    def __init__(self, command: str):
        self.command = command
    
    def execute(self, workspace: Any) -> str:
        result = subprocess.run(
            self.command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=workspace,
        )
        output = result.stdout + result.stderr
        return output or "(no output)"


class FileEditorToolDefinition(ToolDefinition):
    """Tool for reading and writing files."""
    
    name: str = "file_editor"
    description: str = "Read, write, and edit files"
    
    def action_from_arguments(
        self,
        command: str,
        path: str,
        file_text: str = "",
        old_str: str = "",
        new_str: str = "",
    ) -> "FileEditorAction":
        return FileEditorAction(
            command=command,
            path=path,
            file_text=file_text,
            old_str=old_str,
            new_str=new_str,
        )


class FileEditorAction:
    """File editor actions."""
    
    def __init__(
        self,
        command: str,
        path: str,
        file_text: str = "",
        old_str: str = "",
        new_str: str = "",
    ):
        self.command = command
        self.path = Path(path)
        self.file_text = file_text
        self.old_str = old_str
        self.new_str = new_str
    
    def execute(self, workspace: Any) -> str:
        workspace_path = Path(workspace)
        
        if self.command == "view":
            if not self.path.exists():
                return f"File not found: {self.path}"
            content = self.path.read_text()
            # Show first 50 lines
            lines = content.split("\n")
            if len(lines) > 50:
                return "\n".join(lines[:50]) + f"\n... ({len(lines)} total lines)"
            return content
            
        elif self.command == "create":
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self.file_text)
            return f"Created: {self.path}"
            
        elif self.command == "str_replace":
            if not self.path.exists():
                return f"File not found: {self.path}"
            content = self.path.read_text()
            if self.old_str not in content:
                return f"Text not found: {self.old_str}"
            content = content.replace(self.old_str, self.new_str)
            self.path.write_text(content)
            return f"Updated: {self.path}"
        
        return f"Unknown command: {self.command}"


class TaskTrackerToolDefinition(ToolDefinition):
    """Tool for tracking tasks."""
    
    name: str = "task_tracker"
    description: str = "Track and manage tasks"
    
    def action_from_arguments(
        self,
        command: str,
        task_list: list[dict] = [],
    ) -> "TaskTrackerAction":
        return TaskTrackerAction(command=command, task_list=task_list)


class TaskTrackerAction:
    """Task tracker actions."""
    
    def __init__(self, command: str, task_list: list[dict] = []):
        self.command = command
        self.task_list = task_list
    
    def execute(self, workspace: Any) -> str:
        tasks_file = Path(workspace) / ".openhands_tasks.json"
        
        if self.command == "view":
            if not tasks_file.exists():
                return "No tasks found"
            tasks = json.loads(tasks_file.read_text())
            return json.dumps(tasks, indent=2)
            
        elif self.command == "plan":
            tasks_file.write_text(json.dumps(self.task_list, indent=2))
            return f"Tasks saved: {len(self.task_list)}"
        
        return f"Unknown command: {self.command}"


# =============================================================================
# Tool Factory
# =============================================================================

def get_tool_definitions() -> list[ToolDefinition]:
    """Get all custom tool definitions."""
    return [
        TerminalToolDefinition(),
        FileEditorToolDefinition(),
        TaskTrackerToolDefinition(),
    ]


def create_tools() -> list[Tool]:
    """Create tool instances."""
    return [Tool(definition=td) for td in get_tool_definitions()]