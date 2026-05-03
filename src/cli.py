#!/usr/bin/env python3
"""
Radcode CLI - Simple interface for Single Agent architecture.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coordinator import RadcodeCoordinator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("radcod.cli")


def cmd_run(args):
    """Execute a request using the single agent."""
    coordinator = RadcodeCoordinator(
        api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        workspace="./workspace"
    )
    
    logger.info(f"Executing: {args.request}")
    
    result = coordinator.run(args.request)
    
    if result["status"] == "success":
        print(f"\n✅ Completed!")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown')}")


def cmd_config(args):
    """Show configuration."""
    print("Radcode Configuration")
    print("=" * 40)
    
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"LLM_API_KEY: {'*' * 8}{api_key[-4:]}")
    else:
        print("LLM_API_KEY: (not set)")
    
    print(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'anthropic/claude-sonnet-4-5-20250929')}")
    print(f"WORKSPACE: ./workspace")


def cmd_server(args):
    """Start the FastAPI server."""
    import uvicorn
    from src.server import app
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


def main():
    parser = argparse.ArgumentParser(prog="radcode")
    subparsers = parser.add_subparsers(dest="command")
    
    # run command
    run_parser = subparsers.add_parser("run", help="Execute a request")
    run_parser.add_argument("request", help="What to build")
    
    # config command
    subparsers.add_parser("config", help="Show configuration")
    
    # server command
    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    if args.command == "run":
        cmd_run(args)
    elif args.command == "config":
        cmd_config(args)
    elif args.command == "server":
        cmd_server(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()