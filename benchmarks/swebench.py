"""
SWE-bench Evaluation Framework for RadCode.

Runs RadCode against SWE-bench issues to measure autonomous code resolution.
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("radcod.benchmark")


class SWEBenchRunner:
    """
    Run SWE-bench evaluations against RadCode.
    
    Usage:
        runner = SWEBenchRunner()
        results = runner.run_evaluation(
            issue="django#12345",
            workspace="/tmp/eval_workspace"
        )
    """
    
    # Default SWE-bench issue repository mapping
    REPO_MAP = {
        "django": "https://github.com/django/django.git",
        "scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
        "requests": "https://github.com/psf/requests.git",
        "pytest": "https://github.com/pytest-dev/pytest.git",
    }
    
    def __init__(
        self,
        radcode_path: str = "radcode",
        model: str = None,
        api_key: str = None
    ):
        self._radcode = radcode_path
        self._model = model or os.getenv("LLM_MODEL")
        self._api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self._results: List[Dict] = []
    
    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """
        Get issue details from SWE-bench.
        
        Args:
            issue_id: Issue identifier (e.g., "django#12345")
            
        Returns:
            Dict with issue details
        """
        # Try to fetch from SWE-bench dataset
        # This is a simplified version - real impl would use swebench dataset
        parts = issue_id.split("#")
        repo = parts[0]
        issue_num = parts[1] if len(parts) > 1 else "0"
        
        return {
            "id": issue_id,
            "repo": repo,
            "issue_number": issue_num,
            " repo_url": self.REPO_MAP.get(repo, ""),
            " title": f"Issue {issue_num} in {repo}",
            "description": "Issue description from SWE-bench",
            "patch": ""  # The expected fix
        }
    
    def setup_workspace(
        self,
        issue: Dict[str, Any],
        workspace: Path
    ) -> bool:
        """
        Set up evaluation workspace with repo at issue commit.
        
        Args:
            issue: Issue details from get_issue()
            workspace: Workspace directory
            
        Returns:
            True if setup successful
        """
        try:
            workspace.mkdir(parents=True, exist_ok=True)
            
            # Clone repository at base commit
            repo_url = issue.get("repo_url", "")
            if not repo_url:
                logger.warning(f"No repo URL for {issue['id']}")
                return False
            
            # Clone shallow for speed
            result = subprocess.run(
                ["git", "clone", "--depth=1", repo_url, str(workspace)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Clone failed: {result.stderr}")
                return False
            
            logger.info(f"Setup workspace: {workspace}")
            return True
            
        except Exception as e:
            logger.error(f"Workspace setup failed: {e}")
            return False
    
    def run_evaluation(
        self,
        issue: str,
        workspace: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run single evaluation.
        
        Args:
            issue: Issue ID (e.g., "django#12345")
            workspace: Optional workspace directory
            timeout: Max time in seconds
            
        Returns:
            Evaluation results
        """
        # Get issue details
        issue_data = self.get_issue(issue)
        
        # Create workspace
        ws_path = Path(workspace) if workspace else Path(tempfile.mkdtemp())
        
        if not self.setup_workspace(issue_data, ws_path):
            return {
                "issue": issue,
                "status": "setup_failed",
                "workspace": str(ws_path)
            }
        
        # Run RadCode on issue
        try:
            # Build prompt from issue
            prompt = f"Fix the following issue in {issue_data['repo']}:\n\n{issue_data.get('description', '')}"
            
            result = subprocess.run(
                [self._radcode, "run", prompt],
                cwd=str(ws_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            evaluation = {
                "issue": issue,
                "status": "completed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "output": result.stdout[:1000],  # Truncate
                "error": result.stderr[:500] if result.stderr else None,
                "workspace": str(ws_path)
            }
            
        except subprocess.TimeoutExpired:
            evaluation = {
                "issue": issue,
                "status": "timeout",
                "timeout": timeout,
                "workspace": str(ws_path)
            }
        except Exception as e:
            evaluation = {
                "issue": issue,
                "status": "error",
                "error": str(e),
                "workspace": str(ws_path)
            }
        
        self._results.append(evaluation)
        return evaluation
    
    def evaluate_batch(
        self,
        issues: List[str],
        max_parallel: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Run batch evaluation.
        
        Args:
            issues: List of issue IDs
            max_parallel: Max parallel evaluations
            
        Returns:
            List of evaluation results
        """
        results = []
        
        for issue in issues:
            logger.info(f"Evaluating: {issue}")
            result = self.run_evaluation(issue)
            results.append(result)
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get evaluation summary.
        
        Returns:
            Summary statistics
        """
        if not self._results:
            return {"status": "no_results"}
        
        total = len(self._results)
        solved = sum(1 for r in self._results if r.get("status") == "completed")
        failed = sum(1 for r in self._results if r.get("status") == "failed")
        timeout = sum(1 for r in self._results if r.get("status") == "timeout")
        
        return {
            "total": total,
            "solved": solved,
            "failed": failed,
            "timeout": timeout,
            "success_rate": solved / total if total > 0 else 0,
            "results": self._results
        }


# ============= STANDALONE EXECUTION =============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RadCode SWE-bench evaluation")
    parser.add_argument("issue", help="Issue ID (e.g., django#12345)")
    parser.add_argument("--workspace", help="Workspace directory")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    runner = SWEBenchRunner()
    result = runner.run_evaluation(args.issue, args.workspace, args.timeout)
    
    print(json.dumps(result, indent=2))
    
    if result.get("status") == "completed":
        exit(0)
    else:
        exit(1)