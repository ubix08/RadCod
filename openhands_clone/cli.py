#!/usr/bin/env python3
"""
OpenHands-Clone CLI
========================
Command-line interface for the coding agent.

Features:
- Single task execution
- Interactive REPL mode
- Streaming support
- Web UI integration
- Agentic mode
"""

import argparse
import os
import sys

from openhands_clone import (
    coding_agent,
    DEFAULT_MODEL,
    MAX_ITERATIONS,
)
from openhands_clone.agentic import execute_task


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="radcod",
        description="RadCod - Agentic Coding System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  radcod "Create a hello world app"
  radcod "Fix this bug" --model anthropic/claude-opus-4-20250513
  radcod --stream "List files"
  radcod --workspace /path/to/project "Review code"
  radcod --agentic "Refactor calculate() to be async"
  radcod --web  # Start web UI
  radcod --repl  # Interactive REPL
        """,
    )
    
    parser.add_argument(
        "task",
        nargs="?",
        default="",
        help="Task to give to the agent",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"LLM model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        default=os.getcwd(),
        help="Working directory",
    )
    parser.add_argument(
        "--max-iterations",
        "-n",
        type=int,
        default=MAX_ITERATIONS,
        help=f"Max iterations (default: {MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Stream responses",
    )
    parser.add_argument(
        "--agentic",
        "-a",
        action="store_true",
        help="Use agentic reasoning-action loop",
    )
    parser.add_argument(
        "--repl",
        "-i",
        action="store_true",
        help="Interactive REPL mode",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start web UI server",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8080,
        help="Web UI port (default: 8080)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.3.0",
    )
    
    args = parser.parse_args()
    
    # Web UI mode
    if args.web:
        start_web_server(args)
        return
    
    # Interactive REPL mode
    if args.repl:
        run_repl(args)
        return
    
    # Handle empty task
    if not args.task:
        print("Usage: radcod <task>")
        print("  or: radcod --repl")
        print("  or: radcod --web")
        sys.exit(1)
    
    # Run the task
    try:
        if args.agentic:
            # Use agentic loop
            result = execute_task(
                task=args.task,
                model=args.model,
                workspace=args.workspace,
                max_iterations=args.max_iterations,
                verbose=args.verbose,
            )
            print(result)
        else:
            # Use SDK conversation
            convo = coding_agent(
                model=args.model,
                workspace=args.workspace,
                max_iterations=args.max_iterations,
            )
            
            convo.send_message(args.task)
            
            if args.stream:
                convo.run(streaming=True)
            else:
                convo.run()
            
            # Show metrics
            metrics = convo.get_metrics()
            if metrics:
                print("\n" + "="*50)
                print("Metrics:", metrics)
                
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_repl(args):
    """Run in interactive REPL mode."""
    print("RadCod REPL")
    print("Type 'exit' or 'quit' to stop")
    print("Type 'agentic' to toggle agentic mode")
    print("-" * 40)
    
    agentic_mode = args.agentic
    
    while True:
        try:
            task = input("\n📋 > ").strip()
            if not task:
                continue
            if task.lower() in ("exit", "quit"):
                break
            if task.lower() == "agentic":
                agentic_mode = not agentic_mode
                print(f"  Agentic mode: {'ON' if agentic_mode else 'OFF'}")
                continue
            
            if agentic_mode:
                result = execute_task(
                    task=task,
                    model=args.model,
                    workspace=args.workspace,
                    max_iterations=args.max_iterations,
                    verbose=args.verbose,
                )
                print(result)
            else:
                convo = coding_agent(
                    model=args.model,
                    workspace=args.workspace,
                    max_iterations=args.max_iterations,
                )
                convo.send_message(task)
                convo.run(streaming=args.stream)
                
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except EOFError:
            break
    
    print("\nGoodbye!")


def start_web_server(args):
    """Start the web UI server."""
    try:
        from openhands_clone.webui import app
        print(f"Starting web UI on port {args.web_port}...")
        app.run(host="0.0.0.0", port=args.web_port, debug=False)
    except ImportError:
        print("Web UI module not found. Install: pip install radcod[web]")
        sys.exit(1)


if __name__ == "__main__":
    main()