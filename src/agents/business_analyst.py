import json
from openai import OpenAI
from src.orchestrator.domain_spec.models import DomainSpec, Entity
from src.orchestrator.domain_spec.prompt import DOMAIN_ANALYSIS_PROMPT

class BusinessAnalystAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def analyze(self, user_request: str) -> DomainSpec:
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": DOMAIN_ANALYSIS_PROMPT},
                {"role": "user", "content": user_request}
            ],
            response_format={ "type": "json_object" }
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # Convert JSON to DomainSpec
        entities = [
            Entity(
                name=e['name'],
                description=e['description'],
                fields=e['fields']
            ) for e in data['entities']
        ]
        
        return DomainSpec(
            business_name=data['business_name'],
            business_description=data['business_description'],
            entities=entities,
            processes=data['processes']
        )
