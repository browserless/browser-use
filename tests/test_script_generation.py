"""Tests for script generation functionality."""

import asyncio
import sys
import json
from pathlib import Path
import os
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from browser_use.script_generation.service import ScriptGenerator
from browser_use.agent.service import Agent
from langchain_anthropic import ChatAnthropic


async def test_script_generation():
	"""Test script generation functionality using natural language commands."""
	# Load environment variables
	load_dotenv()
	
	# Initialize the LLM service with Anthropic
	llm = ChatAnthropic(
		model_name="claude-3-7-sonnet-20250219",
		temperature=0.0,
		timeout=100,  # Increase timeout for complex tasks
	)
	
	# Define the task
	task = "go to google.com, click accept all, then type in the search bar browserless and click the search button.  scroll to the first result that is for browserless.io, then get me the content of that result"
	
	# Initialize the agent with task and LLM
	agent = Agent(
		task=task,
		llm=llm,
		use_vision=True,  # Enable vision for better understanding
		max_actions_per_step=1  # Limit actions per step for better control
	)
	
	try:
		# Run the task
		await agent.run()
		
		# Get the action log from the agent's history
		action_log = agent.get_action_log()
		
		# Print the action log for debugging
		print('\nAction Log:\n\n')
		print(json.dumps(action_log, indent=2))
		print('\n\n')
		
		# Print detailed information about the go_to_url action
		print('\nDetailed go_to_url action analysis:\n')
		for action in action_log:
			if action.get('action_type') == 'go_to_url':
				print('Found go_to_url action:')
				print(f'  Action type: {action.get("action_type")}')
				print(f'  Params: {json.dumps(action.get("params", {}), indent=2)}')
				print(f'  Selector: {json.dumps(action.get("selector"), indent=2)}')
				print(f'  Timestamp: {action.get("timestamp")}')
		print('\n\n')
		
		# Create script generator with the actual action log
		generator = ScriptGenerator(action_log)
		
		# Generate and print BrowserQL script
		browserql_script = generator.to_browserql()
		print('\nBrowserQL Script:')
		print(browserql_script)
		
	finally:
		# Clean up
		await agent.close()


if __name__ == '__main__':
	asyncio.run(test_script_generation())
