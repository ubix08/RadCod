"""
Deployment helpers for RadCode.

Provides deployment capabilities to Vercel, Docker, and cloud platforms.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any

logger = logging.getLogger("radcod.deploy")


class DeploymentHelper:
    """
    Deployment utilities for various platforms.
    
    Usage:
        deployer = DeploymentHelper()
        result = deployer.deploy_vercel("/path/to/project")
    """
    
    @staticmethod
    def deploy_vercel(
        project_path: str,
        project_name: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy to Vercel.
        
        Args:
            project_path: Path to project
            project_name: Optional Vercel project name
            token: Vercel token (or use VERCEL_TOKEN env)
            
        Returns:
            Deployment result with URL
        """
        token = token or os.getenv("VERCEL_TOKEN")
        if not token:
            return {"status": "error", "error": "No Vercel token provided"}
        
        project = Path(project_path)
        if not project.exists():
            return {"status": "error", "error": f"Project not found: {project_path}"}
        
        try:
            # Try Vercel CLI
            result = subprocess.run(
                ["vercel", "--yes", "--token", token],
                cwd=str(project),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse deployment URL from output
            url = None
            for line in result.stdout.split("\n"):
                if "https://" in line:
                    url = line.strip()
                    break
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "url": url,
                "output": result.stdout[:500],
                "error": result.stderr[:200] if result.stderr else None
            }
            
        except FileNotFoundError:
            return {"status": "error", "error": "Vercel CLI not installed. Run: npm i -g vercel"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def deploy_docker(
        project_path: str,
        image_name: str,
        tag: str = "latest",
        registry: Optional[str] = None,
        push: bool = False
    ) -> Dict[str, Any]:
        """
        Build and optionally push Docker image.
        
        Args:
            project_path: Path to project
            image_name: Image name
            tag: Image tag
            registry: Optional registry (e.g., ghcr.io/username)
            push: Whether to push after build
            
        Returns:
            Deployment result
        """
        project = Path(project_path)
        if not project.exists():
            return {"status": "error", "error": f"Project not found: {project_path}"}
        
        full_image = f"{image_name}:{tag}"
        if registry:
            full_image = f"{registry}/{full_image}"
        
        try:
            # Build image
            build_cmd = ["docker", "build", "-t", full_image, "."]
            build_result = subprocess.run(
                build_cmd,
                cwd=str(project),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode != 0:
                return {
                    "status": "build_failed",
                    "error": build_result.stderr[:300]
                }
            
            result = {"status": "built", "image": full_image}
            
            # Push if requested
            if push:
                push_cmd = ["docker", "push", full_image]
                push_result = subprocess.run(
                    push_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                result["status"] = "pushed" if push_result.returncode == 0 else "push_failed"
                result["pushed_to"] = full_image
            
            return result
            
        except FileNotFoundError:
            return {"status": "error", "error": "Docker not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def deploy_render(
        project_path: str,
        service_name: str,
        token: Optional[str] = None,
        repo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy to Render.com.
        
        Args:
            project_path: Path to project
            service_name: Render service name
            token: Render token (or use RENDER_TOKEN env)
            repo_url: GitHub repo for auto-deploy
            
        Returns:
            Deployment result
        """
        token = token or os.getenv("RENDER_TOKEN")
        if not token:
            return {"status": "error", "error": "No Render token provided"}
        
        # Render uses webhooks - this creates/deploys a service
        # Note: Full implementation would use Render API
        try:
            import requests
            
            # Create or update service
            api_base = "https://api.render.com/v1"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            if repo_url:
                # Create from GitHub
                data = {
                    "serviceName": service_name,
                    "type": "web_service",
                    "repoUrl": repo_url,
                    "branch": "main"
                }
            else:
                return {"status": "error", "error": "repo_url required for Render deploy"}
            
            resp = requests.post(
                f"{api_base}/services",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if resp.status_code in (200, 201):
                service = resp.json()
                return {
                    "status": "deployed",
                    "service_id": service.get("id"),
                    "service_name": service.get("serviceName"),
                    "deploy_url": service.get("serviceDetails", {}).get("url")
                }
            else:
                return {
                    "status": "error",
                    "error": resp.text[:200],
                    "status_code": resp.status_code
                }
                
        except ImportError:
            return {"status": "error", "error": "requests library required: pip install requests"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def deploy_fly(
        project_path: str,
        app_name: str,
        org: str = "personal",
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy to Fly.io.
        
        Args:
            project_path: Path to project  
            app_name: Fly app name
            org: Organization (default: personal)
            token: Fly token (or use FLY_TOKEN env)
            
        Returns:
            Deployment result
        """
        token = token or os.getenv("FLY_TOKEN")
        project = Path(project_path)
        
        if not project.exists():
            return {"status": "error", "error": f"Project not found: {project_path}"}
        
        # Check for fly.toml
        fly_config = project / "fly.toml"
        if not fly_config.exists():
            # Generate basic config
            return {"status": "config_needed", "error": "fly.toml not found. Run: fly launch"}
        
        try:
            result = subprocess.run(
                ["fly", "deploy", "--app", app_name, "--org", org],
                cwd=str(project),
                capture_output=True,
                text=True,
                timeout=180
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout[:300],
                "error": result.stderr[:200] if result.stderr else None
            }
            
        except FileNotFoundError:
            return {"status": "error", "error": "Fly CLI not installed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ============= STANDALONE =============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RadCode deployment")
    parser.add_argument("platform", choices=["vercel", "docker", "render", "fly"])
    parser.add_argument("path", help="Project path")
    parser.add_argument("--name", help="Project/service name")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--push", action="store_true", help="Push after build")
    
    args = parser.parse_args()
    
    if args.platform == "vercel":
        result = DeploymentHelper.deploy_vercel(args.path, args.name, args.token)
    elif args.platform == "docker":
        name = args.name or "myapp"
        result = DeploymentHelper.deploy_docker(args.path, name, push=args.push)
    elif args.platform == "render":
        name = args.name or "myapp"
        result = DeploymentHelper.deploy_render(args.path, name, args.token)
    elif args.platform == "fly":
        name = args.name or "myapp"
        result = DeploymentHelper.deploy_fly(args.path, name, token=args.token)
    
    print(json.dumps(result, indent=2))