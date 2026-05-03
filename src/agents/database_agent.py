"""
Database Agent - Generates database schemas and SQL.

Generates SQL, ORM models, and migrations based on domain specifications.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.orchestrator.skills import load_skill
from src.orchestrator.domain_spec.models import (
    DomainSpec, Entity, EntityField, Relationship, RelationshipType, 
    FieldConstraint, ConstraintType
)

logger = logging.getLogger("radcod.database_agent")


@dataclass
class SchemaOutput:
    """Generated database schema output."""
    sql_ddl: str = ""
    sqlalchemy_models: str = ""
    pydantic_schemas: str = ""
    migrations: str = ""


class DatabaseAgent:
    """
    Database specialist that generates schemas, SQL, and ORM models.
    """
    
    def __init__(self):
        self.skill = load_skill("database_agent")
        logger.info("Database Agent initialized.")
    
    def _load_skill(self) -> str:
        """Get skill - now uses shared loader."""
        return self.skill
    
    def generate_schema(self, domain_spec: DomainSpec) -> SchemaOutput:
        """
        Generate complete database schema for a domain specification.
        
        Args:
            domain_spec: The domain specification
            
        Returns:
            SchemaOutput with SQL, ORM models, etc.
        """
        output = SchemaOutput()
        
        # Generate SQL DDL
        output.sql_ddl = self._generate_sql_ddl(domain_spec)
        
        # Generate SQLAlchemy models
        output.sqlalchemy_models = self._generate_sqlalchemy(domain_spec)
        
        # Generate Pydantic schemas
        output.pydantic_schemas = self._generate_pydantic(domain_spec)
        
        logger.info(f"Schema generated for {domain_spec.business_name}")
        return output
    
    def _map_type(self, domain_type: str, db_type: str = "postgresql") -> str:
        """Map domain type to database type."""
        mappings = {
            "postgresql": {
                "string": "VARCHAR(255)",
                "text": "TEXT",
                "integer": "INTEGER",
                "float": "REAL",
                "boolean": "BOOLEAN",
                "datetime": "TIMESTAMP",
                "json": "JSONB",
                "uuid": "UUID"
            },
            "mysql": {
                "string": "VARCHAR(255)",
                "text": "TEXT",
                "integer": "INT",
                "float": "FLOAT",
                "boolean": "TINYINT(1)",
                "datetime": "DATETIME",
                "json": "JSON"
            },
            "sqlite": {
                "string": "TEXT",
                "text": "TEXT",
                "integer": "INTEGER",
                "float": "REAL",
                "boolean": "INTEGER",
                "datetime": "TEXT",
                "json": "TEXT"
            }
        }
        return mappings.get(db_type, mappings["postgresql"]).get(domain_type, "TEXT")
    
    def _generate_sql_ddl(self, domain_spec: DomainSpec) -> str:
        """Generate SQL DDL statements."""
        ddl = "-- Database Schema for {}\n\n".format(domain_spec.business_name)
        
        for entity in domain_spec.entities:
            table_name = self._to_snake_case(entity.name)
            
            ddl += f"CREATE TABLE {table_name} (\n"
            
            columns = []
            # Add fields
            for field in entity.fields:
                col_def = f"  {self._to_snake_case(field.name)} {self._map_type(field.data_type)}"
                
                # Add constraints
                if field.is_primary_key:
                    col_def += " PRIMARY KEY"
                if field.is_foreign_key:
                    for c in field.constraints:
                        if c.type == ConstraintType.FOREIGN_KEY:
                            target = self._to_snake_case(c.target_entity or "")
                            col_def += f" REFERENCES {target}(id)"
                if not field.required:
                    col_def += " NULL"
                else:
                    col_def += " NOT NULL"
                if field.default:
                    col_def += f" DEFAULT {field.default}"
                    
                columns.append(col_def)
            
            # Add created_at, updated_at
            columns.append("  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            ddl += ",\n".join(columns)
            ddl += "\n);\n\n"
            
            # Add relationships
            for rel in domain_spec.get_relationships_for(entity.name):
                if rel.from_entity == entity.name and rel.relationship_type == RelationshipType.ONE_TO_MANY:
                    child_table = self._to_snake_case(rel.to_entity)
                    parent_table = self._to_snake_case(rel.from_entity)
                    ddl += f"""
ALTER TABLE {child_table}
ADD CONSTRAINT fk_{child_table}_{parent_table}
FOREIGN KEY ({self._to_snake_case(rel.from_field)}) 
REFERENCES {parent_table}(id);
"""
        
        return ddl
    
    def _generate_sqlalchemy(self, domain_spec: DomainSpec) -> str:
        """Generate SQLAlchemy models."""
        code = '''"""SQLAlchemy models for {}."""\n\n'''.format(domain_spec.business_name)
        code += """from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

"""
        
        for entity in domain_spec.entities:
            class_name = entity.name
            table_name = self._to_snake_case(entity.name)
            
            code += f"class {class_name}(Base):\n"
            code += f'    __tablename__ = "{table_name}"\n\n'
            
            # Add fields
            for field in entity.fields:
                col_name = self._to_snake_case(field.name)
                
                if field.is_primary_key:
                    code += f"    id = Column(Integer, primary_key=True)\n"
                elif field.data_type == "string":
                    max_len = field.max_length or 255
                    code += f"    {col_name} = Column(String({max_len}))\n"
                elif field.data_type == "text":
                    code += f"    {col_name} = Column(Text)\n"
                elif field.data_type == "integer":
                    code += f"    {col_name} = Column(Integer)\n"
                elif field.data_type == "float":
                    code += f"    {col_name} = Column(Float)\n"
                elif field.data_type == "boolean":
                    code += f"    {col_name} = Column(Boolean)\n"
                elif field.data_type == "datetime":
                    code += f"    {col_name} = Column(DateTime, default=datetime.utcnow)\n"
                elif field.data_type == "json":
                    code += f"    {col_name} = Column(JSON)\n"
            
            code += "    created_at = Column(DateTime, default=datetime.utcnow)\n"
            code += "    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\n"
            code += "\n"
        
        return code
    
    def _generate_pydantic(self, domain_spec: DomainSpec) -> str:
        """Generate Pydantic schemas for FastAPI."""
        code = '''"""Pydantic schemas for {}."""\n\n'''.format(domain_spec.business_name)
        code += """from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

"""
        
        for entity in domain_spec.entities:
            class_name = entity.name
            
            # Base schema
            code += f"class {class_name}Base(BaseModel):\n"
            for field in entity.fields:
                if field.is_primary_key:
                    continue
                py_type = self._to_python_type(field.data_type)
                default = "None" if not field.required else "..."
                code += f'    {field.name}: Optional[{py_type}] = {default}\n'
            code += "\n"
            
            # Create schema
            code += f"class {class_name}Create({class_name}Base):\n"
            code += "    pass\n\n"
            
            # InDB schema
            code += f"class {class_name}InDB({class_name}Base):\n"
            code += "    id: int\n"
            code += "    created_at: datetime\n"
            code += "    updated_at: datetime\n\n"
            code += '    class Config:\n'
            code += '        from_attributes = True\n\n'
        
        return code
    
    def _to_python_type(self, domain_type: str) -> str:
        """Map domain type to Python type."""
        mappings = {
            "string": "str",
            "text": "str",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "datetime": "datetime",
            "json": "dict"
        }
        return mappings.get(domain_type, "str")
    
    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    
    def generate_migrations(self, domain_spec: DomainSpec) -> str:
        """Generate migration scripts."""
        # Simplified - real implementation would use Alembic
        return self._generate_sql_ddl(domain_spec)