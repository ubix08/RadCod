from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum

# Relationship types
class RelationshipType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"

# Field constraint types
class ConstraintType(str, Enum):
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    NOT_NULL = "not_null"
    DEFAULT = "default"
    CHECK = "check"

@dataclass
class FieldConstraint:
    """Defines a constraint on a field."""
    type: ConstraintType
    value: Optional[str] = None  # For DEFAULT, CHECK constraints
    target_entity: Optional[str] = None  # For FOREIGN_KEY
    target_field: Optional[str] = None  # For FOREIGN_KEY

@dataclass
class Relationship:
    """Defines a relationship between entities."""
    from_entity: str
    to_entity: str
    relationship_type: RelationshipType
    from_field: str  # Field on the "one" side
    to_field: str = "id"  # Field on the "many" side (usually 'id')

@dataclass
class EntityIndex:
    """Database index definition."""
    fields: List[str]
    unique: bool = False
    name: Optional[str] = None

@dataclass
class EntityField:
    """Enhanced field with type, constraints, and metadata."""
    name: str
    data_type: str  # string, integer, float, boolean, datetime, text, json
    description: str = ""
    constraints: List[FieldConstraint] = field(default_factory=list)
    required: bool = False
    default: Optional[str] = None
    max_length: Optional[int] = None  # For string/text fields

    @property
    def is_primary_key(self) -> bool:
        return any(c.type == ConstraintType.PRIMARY_KEY for c in self.constraints)

    @property
    def is_foreign_key(self) -> bool:
        return any(c.type == ConstraintType.FOREIGN_KEY for c in self.constraints)

@dataclass
class Entity:
    """Business entity with enhanced field definitions."""
    name: str
    description: str
    fields: List[EntityField] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)  # Relationship names
    indexes: List[EntityIndex] = field(default_factory=list)

    def get_field(self, name: str) -> Optional[EntityField]:
        """Get field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def get_primary_key(self) -> Optional[EntityField]:
        """Get primary key field."""
        for f in self.fields:
            if f.is_primary_key:
                return f
        return None

    def get_foreign_keys(self) -> List[EntityField]:
        """Get all foreign key fields."""
        return [f for f in self.fields if f.is_foreign_key]


@dataclass
class ProcessStep:
    """A single step in a business process."""
    name: str
    description: str
    actor: str  # Who performs this: user, system, agent
    action: str  # What action: create, update, delete, review, approve
    entity: str  # Which entity
    trigger: Optional[str] = None  # What triggers this step (event/condition)

@dataclass
class BusinessProcess:
    """Structured business process with steps."""
    name: str
    description: str
    steps: List[ProcessStep] = field(default_factory=list)
    triggers_on: Optional[str] = None  # Event that starts this process


@dataclass
class DomainSpec:
    """Complete domain specification with relationships and processes."""
    business_name: str
    business_description: str
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    processes: List[BusinessProcess] = field(default_factory=list)

    def get_entity(self, name: str) -> Optional[Entity]:
        """Get entity by name."""
        for e in self.entities:
            if e.name.lower() == name.lower():
                return e
        return None

    def get_relationships_for(self, entity_name: str) -> List[Relationship]:
        """Get all relationships involving an entity."""
        return [r for r in self.relationships 
                if r.from_entity.lower() == entity_name.lower() 
                or r.to_entity.lower() == entity_name.lower()]

    # Backward compatibility: support old List[Entity] interface
    @property
    def entities_list(self) -> List[Entity]:
        return self.entities

    # Legacy compatibility for old code
    def to_markdown(self) -> str:
        md = f"# Domain Specification: {self.business_name}\n\n"
        md += f"## Description\n{self.business_description}\n\n"
        
        md += "## Entities\n"
        for entity in self.entities:
            md += f"### {entity.name}\n{entity.description}\n"
            md += "| Field | Type | Constraints |\n|---|---|---|\n"
            for field in entity.fields:
                constraints = ", ".join([c.type.value for c in field.constraints])
                md += f"| {field.name} | {field.data_type} | {constraints} |\n"
            md += "\n"

        if self.relationships:
            md += "## Relationships\n"
            for rel in self.relationships:
                md += f"- {rel.from_entity}.{rel.from_field} {rel.relationship_type.value} {rel.to_entity}.{rel.to_field}\n"
            md += "\n"

        md += "## Processes\n"
        for proc in self.processes:
            md += f"### {proc.name}\n{proc.description}\n"
            for step in proc.steps:
                md += f"- [{step.actor}] {step.action} {step.entity}: {step.description}\n"
            md += "\n"
        
        return md
