"""
Direct API Agent - Uses NVIDIA API directly + basic tools.
Bypasses litellm issues by calling API directly.
"""

import subprocess
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("radcod.direct_agent")


class DirectNVIDIAllm:
    """Direct API LLM for NVIDIA - bypasses litellm."""
    
    API_BASE = 'https://integrate.api.nvidia.com/v1'
    
    def __init__(
        self,
        model: str = "meta/llama-3.1-70b-instruct",
        api_key: Optional[str] = None,
        timeout: int = 120,
    ):
        self.model = model
        # API key MUST come from environment - never hardcode
        self.api_key = api_key or os.environ.get('NVIDIA_API_KEY')
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY must be set in environment")
        self.timeout = timeout
        self._messages: List[dict] = []
    
    def add_system_message(self, content: str):
        """Add system message."""
        self._messages = [{"role": "system", "content": content}]
    
    def chat(self, message: str, max_retries: int = 3) -> str:
        """Send a message and get response."""
        self._messages.append({"role": "user", "content": message})
        
        for attempt in range(max_retries):
            try:
                resp = httpx.post(
                    f"{self.API_BASE}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": self._messages,
                        "max_tokens": 4096,
                        "temperature": 0.7,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=self.timeout
                )
                
                if resp.status_code == 429:
                    # Rate limited - wait and retry
                    import time
                    wait_time = (attempt + 1) * 5
                    time.sleep(wait_time)
                    continue
                
                if resp.status_code != 200:
                    raise Exception(f"API error: {resp.status_code} - {resp.text}")
                
                result = resp.json()['choices'][0]['message']['content']
                self._messages.append({"role": "assistant", "content": result})
                return result
                
            except httpx.ReadTimeout:
                import time
                time.sleep(3)
                continue
        
        raise Exception("Max retries exceeded")
    
    def reset(self):
        """Reset conversation."""
        if self._messages and self._messages[0]['role'] == 'system':
            self._messages = [self._messages[0]]
        else:
            self._messages = []


class DirectTools:
    """Simple tool wrapper - uses subprocess and pathlib."""
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
    
    def run(self, command: str) -> str:
        """Run a terminal command."""
        result = subprocess.run(
            command, shell=True, cwd=self.workspace,
            capture_output=True, text=True, timeout=60
        )
        return result.stdout or result.stderr
    
    def write(self, path: str, content: str) -> str:
        """Write a file."""
        file_path = self.workspace / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Written {len(content)} bytes to {path}"
    
    def read(self, path: str) -> str:
        """Read a file."""
        file_path = self.workspace / path
        return file_path.read_text()


class DirectAPIAgent:
    """Agent that uses direct API calls + basic tools."""
    
    SYSTEM_PROMPT = """You are an autonomous software engineer.
Your goal is to complete tasks by writing code and executing commands.

When asked to write a file, use the file_editor tool to write the content.
When asked to run a command, use the terminal tool.

Always verify your work after making changes.

Format your response as:
- If you need to write a file: "FILE: path\\ncontent"
- If you need to run a command: "CMD: command"
- If the task is complete: "DONE: summary"
"""
    
    def __init__(
        self,
        llm: Optional[DirectNVIDIAllm] = None,
        workspace: Optional[str] = None,
    ):
        self.llm = llm or DirectNVIDIAllm()
        self.workspace = Path(workspace or os.getcwd())
        self.tools = DirectTools(str(self.workspace))
        
        self._history: List[dict] = []
    
    def run(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        """Run the agent on a task."""
        logger.info(f"Starting task: {task}")
        
        # Add system prompt
        self.llm.add_system_message(self.SYSTEM_PROMPT)
        
        step = 0
        while step < max_steps:
            step += 1
            
            # Get LLM response
            response = self.llm.chat(task)
            logger.info(f"Step {step}: {response[:150]}...")
            
            self._history.append({"step": step, "response": response})
            
            # Check response format
            response = response.strip()
            
            if response.startswith("FILE:"):
                # Write file
                lines = response[5:].strip().split('\n', 1)
                if len(lines) >= 2:
                    path = lines[0].strip()
                    content = lines[1]
                    
                    # Strip markdown code blocks if present
                    content_stripped = content.strip()
                    if content_stripped.startswith('```'):
                        # Remove ```python or ```
                        lines_c = content_stripped.split('\n', 1)
                        if len(lines_c) > 1:
                            content = lines_c[1]
                        else:
                            content = content[3:]
                    if content.strip().endswith('```'):
                        content = content.rsplit('```', 1)[0].strip()
                    
                    result = self.tools.write(path, content)
                    logger.info(f"File: {result}")
                task = "Continue with the next step."
            
            elif response.startswith("CMD:"):
                # Run command
                command = response[4:].strip()
                result = self.tools.run(command)
                logger.info(f"CMD result: {result[:200]}")
                task = f"Command output: {result}\nWhat is the next step?"
            
            elif "DONE" in response[:50].upper() or "COMPLETE" in response[:50].upper():
                # Task complete
                logger.info(f"Task complete after {step} steps")
                break
            
            else:
                # Ask to continue
                task = f"Continue with the task. Last response: {response[:200]}"
        
        final = self.llm.chat("Provide a brief summary of what was done.")
        
        return {
            "status": "complete" if step < max_steps else "max_steps",
            "steps": step,
            "result": final,
            "history": self._history,
        }


def create_direct_agent(model: str = None, workspace: str = None) -> DirectAPIAgent:
    """Create a direct API agent."""
    llm = DirectNVIDIAllm(model=model) if model else DirectNVIDIAllm()
    return DirectAPIAgent(llm=llm, workspace=workspace)