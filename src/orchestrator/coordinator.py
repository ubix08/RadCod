from src.agents.business_analyst import BusinessAnalystAgent
from src.integrations.coding_agent.wrapper import CodingAgentWrapper

class RadcodCoordinator:
    def __init__(self, openai_api_key: str, coding_agent_model: str, workspace_path: str):
        # Initialize specialized agents
        self.ba_agent = BusinessAnalystAgent(api_key=openai_api_key)
        self.coder = CodingAgentWrapper(model_name=coding_agent_model, workspace_path=workspace_path)

    def process_request(self, user_request: str):
        # 1. Analyze and Spec (Business Analyst Agent)
        print(f"[*] Analyzing request: {user_request}")
        domain_spec = self.ba_agent.analyze(user_request)
        
        # 2. Prepare context for the coder
        spec_md = domain_spec.to_markdown()
        
        # 3. Construct task for the coder
        coding_task = f"""
        Implement a CRUD business application based on this domain specification:
        
        {spec_md}
        
        Requirements:
        - Create the necessary file structure for a business application.
        - Define database models (e.g., SQL or ORM) based on the entities.
        - Implement CRUD API endpoints for the defined entities.
        - Ensure all processes defined in the spec are supported.
        """
        
        # 4. Delegate to Coding Agent
        print(f"[*] Delegating to coding agent for business: {domain_spec.business_name}")
        return self.coder.run_task(coding_task)
