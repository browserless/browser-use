"""Tests for script generation functionality."""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI

from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser


async def test_script_generation():
	"""Test script generation functionality."""
	llm = ChatOpenAI(
		model='gpt-4o',
		temperature=0,
	)

	browser = Browser()
	agent = Agent(
		task="Navigate to example.com and click on the 'More information' link",
		llm=llm,
		browser=browser,
	)

	try:
		await agent.run(max_steps=3)
	except Exception as e:
		print(f'Agent run error (expected for test): {e}')

	action_log = agent.get_action_log()
	print(f'\nAction Log ({len(action_log)} actions):')
	for i, action in enumerate(action_log):
		print(f'Action {i + 1}: {action["action_type"]}')
		if action.get('selector'):
			print(f'  Selector: {action["selector"].get("xpath", "N/A")}')

	browserql_script = agent.get_script('browserql')
	print('\nBrowserQL Script:')
	print(browserql_script)

	baas_js_script = agent.get_script('baas_v2', language='javascript')
	print('\nBaaS V2 Script (JavaScript):')
	print(baas_js_script)

	baas_py_script = agent.get_script('baas_v2', language='python')
	print('\nBaaS V2 Script (Python):')
	print(baas_py_script)

	await agent.close()
	await browser.close()


if __name__ == '__main__':
	asyncio.run(test_script_generation())
