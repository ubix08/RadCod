import json
import os
from openai import OpenAI
from src.orchestrator.domain_spec.models import (
    DomainSpec, Entity, EntityField, FieldConstraint, 
    Relationship, RelationshipType, ConstraintType,
    BusinessProcess, ProcessStep
)
from src.orchestrator.domain_spec.prompt import DOMAIN_ANALYSIS_PROMPT
from src.orchestrator.skills import load_skill

class BusinessAnalystAgent:
    """
    Analyzes business requirements and creates domain specifications.
    Uses skills system for prompt management.
    """
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.skill = load_skill("business_analyst")

    def analyze(self, user_request: str) -> DomainSpec:
        """Analyze user request and generate domain specification."""
        system_prompt = self.skill or DOMAIN_ANALYSIS_PROMPT
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            response_format={ "type": "json_object" }
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # Convert JSON to DomainSpec with enhanced models
        entities = []
        for e in data.get("entities", []):
            fields = []
            for f in e.get("fields", []):
                constraints = []
                for c in f.get("constraints", []):
                    constraints.append(FieldConstraint(
                        type=ConstraintType(c.get("type", "not_null")),
                        value=c.get("value"),
                        target_entity=c.get("target_entity"),
                        target_field=c.get("target_field")
                    ))
                fields.append(EntityField(
                    name=f["name"],
                    data_type=f["data_type"],
                    description=f.get("description", ""),
                    required=f.get("required", False),
                    default=f.get("default"),
                    max_length=f.get("max_length"),
                    constraints=constraints
                ))
            
            entities.append(Entity(
                name=e["name"],
                description=e.get("description", ""),
                fields=fields,
                relationships=e.get("relationships", [])
            ))
        
        relationships = []
        for r in data.get("relationships", []):
            relationships.append(Relationship(
                from_entity=r["from_entity"],
                to_entity=r["to_entity"],
                relationship_type=RelationshipType(r.get("relationship_type", "one_to_many")),
                from_field=r.get("from_field", "id"),
                to_field=r.get("to_field", "id")
            ))
        
        processes = []
        for p in data.get("processes", []):
            steps = []
            for s in p.get("steps", []):
                steps.append(ProcessStep(
                    name=s["name"],
                    description=s.get("description", ""),
                    actor=s.get("actor", "user"),
                    action=s.get("action", "create"),
                    entity=s.get("entity", ""),
                    trigger=s.get("trigger")
                ))
            processes.append(BusinessProcess(
                name=p["name"],
                description=p.get("description", ""),
                steps=steps,
                triggers_on=p.get("triggers_on")
            ))
        
        return DomainSpec(
            business_name=data.get("business_name", "New Business"),
            business_description=data.get("business_description", ""),
            entities=entities,
            relationships=relationships,
            processes=processes
        )
