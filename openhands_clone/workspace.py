"""
OpenHands-Clone Workspace - Phase 3
=================================
Local and Remote workspace support.

Phase 3: Workspace abstractions.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Local Workspace
# =============================================================================

@dataclass
class LocalWorkspace:
    """Local file system workspace."""
    
    root: str
    
    def __post_init__(self):
        self._root = Path(self.root)
        self._root.mkdir(parents=True, exist_ok=True)
    
    def read(self, path: str) -> str:
        """Read a file."""
        full_path = self._root / path
        return full_path.read_text()
    
    def write(self, path: str, content: str) -> None:
        """Write a file."""
        full_path = self._root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    def list(self, path: str = "") -> list[str]:
        """List files in directory."""
        base = self._root / path if path else self._root
        return [str(p.relative_to(self._root)) for p in base.rglob("*")]
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return (self._root / path).exists()
    
    def delete(self, path: str) -> None:
        """Delete a file."""
        (self._root / path).unlink()
    
    def get_absolute_path(self, path: str) -> str:
        """Get absolute path."""
        return str((self._root / path).resolve())

    def execute_command(self, command: str, timeout: int = 30) -> tuple[bool, str]:
        """Execute a command."""
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)


@dataclass
class DockerWorkspace:
    """Docker sandboxed workspace."""
    
    container_name: str
    root: str = "/workspace"
    
    def read(self, path: str) -> str:
        """Read a file."""
        import subprocess
        # Using docker cp to read the file
        result = subprocess.run(
            ["docker", "cp", f"{self.container_name}:{self.root}/{path}", "-"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    
    def write(self, path: str, content: str) -> None:
        """Write a file."""
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Using docker cp to write the file
            subprocess.run(
                ["docker", "cp", tmp_path, f"{self.container_name}:{self.root}/{path}"],
                check=True
            )
        finally:
            import os
            os.remove(tmp_path)
    
    def list(self, path: str = "") -> list[str]:
        """List files."""
        # Simplified listing
        return []
        
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        import subprocess
        result = subprocess.run(
            ["docker", "exec", self.container_name, "test", "-e", f"{self.root}/{path}"],
        )
        return result.returncode == 0
    
    def delete(self, path: str) -> None:
        """Delete a file."""
        import subprocess
        subprocess.run(
            ["docker", "exec", self.container_name, "rm", f"{self.root}/{path}"],
            check=True
        )
        
    def execute_command(self, command: str, timeout: int = 30) -> tuple[bool, str]:
        """Execute a command."""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, "bash", "-c", command],
                capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
# =============================================================================
# Remote Workspace
# =============================================================================

@dataclass
class RemoteWorkspace:
    workspace_id: str
    api_url: str | None = None
    _connected: bool = field(default=False, init=False)

    async def connect(self) -> bool:
        """Connect to remote workspace."""
        if self.api_url:
            self._connected = True
            return True
        return False
    
    async def disconnect(self) -> None:
        """Disconnect."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check connection."""
        return self._connected
    
    async def read(self, path: str) -> str:
        """Read a file from remote."""
        return f"Remote content: {path}"
    
    async def write(self, path: str, content: str) -> None:
        """Write to remote."""
        pass
    
    async def list(self, path: str = "") -> list[str]:
        """List remote files."""
        return []


# =============================================================================
# Async Remote Workspace
# =============================================================================

class AsyncRemoteWorkspace:
    """Async remote workspace."""
    
    def __init__(self, workspace_id: str, api_url: str | None = None):
        self.workspace_id = workspace_id
        self.api_url = api_url
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect."""
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        """Disconnect."""
        self._connected = False


# =============================================================================
# Workspace Factory
# =============================================================================

def create_workspace(
    path: str | None = None,
    remote: bool = False,
    docker_container_name: str | None = None,
    workspace_id: str | None = None,
    api_url: str | None = None,
) -> LocalWorkspace | RemoteWorkspace | DockerWorkspace:
    """Create a workspace."""
    if docker_container_name:
        return DockerWorkspace(container_name=docker_container_name)
    if remote:
        return RemoteWorkspace(
            workspace_id=workspace_id or "default",
            api_url=api_url,
        )
    return LocalWorkspace(root=path or os.getcwd())


# =============================================================================
# File Operations
# =============================================================================

async def read_file(workspace: LocalWorkspace | RemoteWorkspace, path: str) -> str:
    """Read file (async)."""
    if isinstance(workspace, LocalWorkspace):
        return workspace.read(path)
    return await workspace.read(path)


async def write_file(
    workspace: LocalWorkspace | RemoteWorkspace,
    path: str,
    content: str,
) -> None:
    """Write file (async)."""
    if isinstance(workspace, LocalWorkspace):
        workspace.write(path, content)
    else:
        await workspace.write(path, content)