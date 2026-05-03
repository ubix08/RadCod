import logging
from openhands.sdk.agent import Agent

# Configure logging for the coding agent
logger = logging.getLogger("radcod.coding_agent")

class CodingAgentWrapper:
    def __init__(self, model_name: str, workspace_path: str, max_iterations: int = 50):
        self.logger = logger
        self.logger.info(f"Initializing CodingAgent with model: {model_name}")
        
        # Instantiate the agent using the SDK
        # We pass max_iterations to control the loop length
        self.agent = Agent(
            model=model_name, 
            workspace=workspace_path,
            max_iterations=max_iterations
        )
        self.logger.info("CodingAgent initialized successfully.")

    def run_task(self, task: str):
        self.logger.info(f"Executing task: {task}")
        try:
            # The SDK's run method drives the agent loop
            result = self.agent.run(task)
            self.logger.info("Task completed successfully.")
            return result
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            raise e
