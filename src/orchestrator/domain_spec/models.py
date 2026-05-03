from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Entity:
    name: str
    description: str
    fields: Dict[str, str]  # field_name: data_type

@dataclass
class DomainSpec:
    business_name: str
    business_description: str
    entities: List[Entity] = field(default_factory=list)
    processes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        md = f"# Domain Specification: {self.business_name}\n\n"
        md += f"## Description\n{self.business_description}\n\n"
        md += "## Entities\n"
        for entity in self.entities:
            md += f"### {entity.name}\n{entity.description}\n"
            md += "| Field | Type |\n|---|---|\n"
            for field_name, field_type in entity.fields.items():
                md += f"| {field_name} | {field_type} |\n"
            md += "\n"
        md += "## Processes\n"
        for proc in self.processes:
            md += f"- {proc}\n"
        return md
