#!/usr/bin/env python3
"""
OpenHands-Clone CLI
==================
Command-line interface for the coding agent.
"""

import argparse
import os
import sys

from openhands_clone import (
    coding_agent,
    DEFAULT_MODEL,
    MAX_ITERATIONS,
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="openhands-clone",
        description="OpenHands-Clone Agentic Coding System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ohand "Create a hello world app"
  ohand "Fix this bug" --model anthropic/claude-opus-4-20250513
  ohand --stream "List files"
  ohand --workspace /path/to/project "Review code"
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
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    args = parser.parse_args()
    
    # Handle interactive mode
    if args.interactive:
        run_interactive(args)
        return
    
    # Handle empty task
    if not args.task:
        print("Usage: ohand <task>")
        print("  or: ohand --interactive")
        sys.exit(1)
    
    # Run the task
    try:
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


def run_interactive(args):
    """Run in interactive mode."""
    from openhands_clone import coding_agent
    
    print("OpenHands-Clone Interactive Mode")
    print("Type 'exit' or 'quit' to stop")
    print("-" * 40)
    
    convo = coding_agent(
        model=args.model,
        workspace=args.workspace,
        max_iterations=args.max_iterations,
    )
    
    while True:
        try:
            task = input("\n> ").strip()
            if not task:
                continue
            if task.lower() in ("exit", "quit"):
                break
            
            convo.send_message(task)
            convo.run(streaming=args.stream)
            
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except EOFError:
            break
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()