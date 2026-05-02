from openhands.sdk.agent import Agent

class CodingAgentWrapper:
    def __init__(self, model_name: str, workspace_path: str):
        # Instantiate the agent using the SDK
        self.agent = Agent(model=model_name, workspace=workspace_path)

    def run_task(self, task: str):
        # Execute task through the SDK's abstraction
        return self.agent.run(task)
