#!/usr/bin/env python3
"""
Radcod CLI - Command-line interface for Radcod autonomous AI software engineer.

Usage:
    radcod analyze <request>   - Analyze business requirements
    radcod build <request>     - Build complete CRUD application
    radcod schema <request>   - Generate database schema
    radcod serve            - Start API server (future)
    radcod config           - Show configuration
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.coordinator import RadcodCoordinator
from src.orchestrator.domain_spec.models import DomainSpec

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("radcod.cli")


def cmd_analyze(args):
    """Analyze business requirements."""
    from unittest.mock import MagicMock
    
    coordinator = RadcodCoordinator(
        enable_validation=False,
        enable_deep_search=args.research
    )
    
    logger.info(f"Analyzing: {args.request}")
    
    # Mock mode for testing without API
    if args.mock:
        mock_spec = DomainSpec(
            business_name="Mock Business",
            business_description="Mock business for testing",
            entities=[],
            relationships=[],
            processes=[]
        )
        print("\n[Mock Mode] Generated mock domain specification")
        domain_spec = mock_spec
    else:
        domain_spec = coordinator.analyze_only(args.request)
    
    print(f"\n{'='*60}")
    print(f"Domain: {domain_spec.business_name}")
    print(f"{'='*60}")
    print(f"\n{domain_spec.business_description}")
    print(f"\nEntities ({len(domain_spec.entities)}):")
    for entity in domain_spec.entities:
        print(f"  - {entity.name}: {entity.description}")
        for field in entity.fields:
            print(f"      • {field.name} ({field.data_type})")
    
    print(f"\nRelationships ({len(domain_spec.relationships)}):")
    for rel in domain_spec.relationships:
        print(f"  - {rel.from_entity} → {rel.to_entity} ({rel.relationship_type.value})")
    
    print(f"\nProcesses ({len(domain_spec.processes)}):")
    for proc in domain_spec.processes:
        print(f"  - {proc.name}: {proc.description}")
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(domain_spec.to_markdown())
        logger.info(f"Saved to: {args.output}")


def cmd_build(args):
    """Build complete CRUD application."""
    coordinator = RadcodCoordinator(
        enable_validation=not args.no_validation,
        enable_deep_search=args.research,
        enable_browser_testing=args.test,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Validation callback
    def validate(spec: DomainSpec) -> bool:
        print(f"\n{'='*60}")
        print(f"Domain: {spec.business_name}")
        print(f"{'='*60}")
        print(f"\n{spec.business_description}")
        print(f"\nEntities: {len(spec.entities)}")
        for entity in spec.entities:
            print(f"  - {entity.name}")
        
        response = input("\nApprove this specification? [y/N]: ")
        return response.lower() in ("y", "yes")
    
    if args.approve:
        coordinator.set_validation_callback(lambda s: True)
    else:
        coordinator.set_validation_callback(validate)
    
    logger.info(f"Building: {args.request}")
    result = coordinator.process_request(
        args.request,
        browser_test_url=args.test_url
    )
    
    if result["status"] == "success":
        print(f"\n✅ Build complete!")
        print(f"   Business: {result['business_name']}")
        print(f"   Duration: {coordinator.state.duration_seconds:.1f}s")
        print(f"   Phases: {len(coordinator.state.phase_history)}")
    else:
        print(f"\n❌ Build failed: {result.get('error', 'Unknown error')}")
        print(f"   Phase: {result.get('phase', 'unknown')}")


def cmd_schema(args):
    """Generate database schema."""
    from src.agents.database_agent import DatabaseAgent
    
    coordinator = RadcodCoordinator(enable_validation=False)
    domain_spec = coordinator.analyze_only(args.request)
    
    db_agent = DatabaseAgent()
    schema = db_agent.generate_schema(domain_spec)
    
    if args.sql:
        print(schema.sql_ddl)
    elif args.orm:
        print(schema.sqlalchemy_models)
    elif args.pydantic:
        print(schema.pydantic_schemas)
    else:
        print("SQL DDL:")
        print(schema.sql_ddl[:500] + "..." if len(schema.sql_ddl) > 500 else schema.sql_ddl)


def cmd_config(args):
    """Show current configuration."""
    print("Radcod Configuration")
    print("=" * 40)
    print(f"OPENAI_API_KEY: {'*' * 8}{os.getenv('OPENAI_API_KEY', '')[-4:] if os.getenv('OPENAI_API_KEY') else '(not set)'}")
    print(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'default')}")
    print(f"WORKSPACE: ./workspace")
    print(f"TAVILY_API_KEY: {'set' if os.getenv('TAVILY_API_KEY') else '(not set)'}")


def main():
    parser = argparse.ArgumentParser(
        prog="radcod",
        description="Radcod - Autonomous AI Software Engineer"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze business requirements")
    analyze_parser.add_argument("request", help="Business description")
    analyze_parser.add_argument("-r", "--research", action="store_true", help="Enable research")
    analyze_parser.add_argument("-o", "--output", help="Output file (markdown)")
    analyze_parser.add_argument("-m", "--mock", action="store_true", help="Mock mode (testing without API)")
    
    # build command
    build_parser = subparsers.add_parser("build", help="Build CRUD application")
    build_parser.add_argument("request", help="Business description")
    build_parser.add_argument("--no-validation", action="store_true", help="Skip validation")
    build_parser.add_argument("-r", "--research", action="store_true", help="Enable research")
    build_parser.add_argument("--test", action="store_true", help="Run browser tests")
    build_parser.add_argument("--test-url", help="URL to test")
    build_parser.add_argument("--approve", action="store_true", help="Auto-approve")
    
    # schema command
    schema_parser = subparsers.add_parser("schema", help="Generate database schema")
    schema_parser.add_argument("request", help="Business description")
    schema_parser.add_argument("--sql", action="store_true", help="Show SQL DDL")
    schema_parser.add_argument("--orm", action="store_true", help="Show SQLAlchemy")
    schema_parser.add_argument("--pydantic", action="store_true", help="Show Pydantic")
    
    # config command
    config_parser = subparsers.add_parser("config", help="Show configuration")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "schema":
        cmd_schema(args)
    elif args.command == "config":
        cmd_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()