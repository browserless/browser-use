"""Script generation service for browser-use."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ScriptGenerator:
	"""
	Generates scripts from browser-use action logs.

	This class converts logged browser actions into either BrowserQL or BaaS V2 scripts.
	Only successful actions are included in the generated scripts.
	"""

	def __init__(self, action_log: List[Dict] = None):
		"""
		Initialize the script generator.

		Args:
		    action_log: List of action log entries to convert
		"""
		self.action_log = action_log or []

	def set_action_log(self, action_log: List[Dict]) -> None:
		"""
		Set the action log to convert.

		Args:
		    action_log: List of action log entries
		"""
		self.action_log = action_log

	def to_browserql(self) -> str:
		"""
		Convert the action log to a BrowserQL script.

		Returns:
		    str: BrowserQL script as a string
		"""
		if not self.action_log:
			return '# No actions to convert'

		script = 'mutation AutomateTask {\n'

		for action in self.action_log:
			action_type = action.get('action_type')
			params = action.get('params', {})
			selector_info = action.get('selector')

			if action_type == 'go_to_url':
				url = params.get('url', '')
				script += f'  goto(url: "{url}") {{\n    status\n  }}\n\n'

			elif action_type == 'click_element_by_index' and selector_info:
				selector = selector_info.get('xpath', '')
				script += f'  click(selector: "{selector}") {{\n    selector\n    time\n  }}\n\n'

			elif action_type == 'input_text' and selector_info:
				selector = selector_info.get('xpath', '')
				text = params.get('text', '')
				script += f'  type(selector: "{selector}", text: "{text}") {{\n    selector\n    text\n  }}\n\n'

			elif action_type == 'scroll_down':
				script += f'  scroll(direction: "down", amount: {params.get("amount", 100)}) {{\n    status\n  }}\n\n'

			elif action_type == 'scroll_up':
				script += f'  scroll(direction: "up", amount: {params.get("amount", 100)}) {{\n    status\n  }}\n\n'

			elif action_type == 'extract_content' and selector_info:
				selector = selector_info.get('xpath', '')
				script += f'  querySelector(selector: "{selector}") {{\n    innerHTML\n  }}\n\n'

			elif action_type == 'done':
				pass

			else:
				script += f'  # Unsupported action: {action_type}\n'

		script += '}'
		return script

	def to_baas_v2(self, language: str = 'javascript') -> str:
		"""
		Convert the action log to a BaaS V2 script.

		Args:
		    language: Programming language for the script (javascript, python)

		Returns:
		    str: BaaS V2 script as a string
		"""
		if not self.action_log:
			return '# No actions to convert'

		if language.lower() == 'javascript':
			return self._to_puppeteer_js()
		elif language.lower() == 'python':
			return self._to_playwright_python()
		else:
			return f'# Unsupported language: {language}'

	def _to_puppeteer_js(self) -> str:
		"""
		Convert the action log to a Puppeteer JavaScript script.

		Returns:
		    str: Puppeteer script as a string
		"""
		script = [
			'// Puppeteer script generated from browser-use actions',
			"const puppeteer = require('puppeteer');",
			'',
			'async function run() {',
			'  const browser = await puppeteer.connect({',
			'    browserWSEndpoint: `wss://production-sfo.browserless.io?token=${TOKEN}`',
			'  });',
			'  const page = await browser.newPage();',
			'',
		]

		for action in self.action_log:
			action_type = action.get('action_type')
			params = action.get('params', {})
			selector_info = action.get('selector')

			if action_type == 'go_to_url':
				url = params.get('url', '')
				script.append(f'  await page.goto("{url}");')

			elif action_type == 'click_element_by_index' and selector_info:
				selector = selector_info.get('xpath', '')
				script.append(f'  await page.click("{selector}");')

			elif action_type == 'input_text' and selector_info:
				selector = selector_info.get('xpath', '')
				text = params.get('text', '')
				script.append(f'  await page.type("{selector}", "{text}");')

			elif action_type == 'scroll_down':
				amount = params.get('amount', 100)
				script.append(f'  await page.evaluate(() => window.scrollBy(0, {amount}));')

			elif action_type == 'scroll_up':
				amount = params.get('amount', 100)
				script.append(f'  await page.evaluate(() => window.scrollBy(0, -{amount}));')

			elif action_type == 'extract_content' and selector_info:
				selector = selector_info.get('xpath', '')
				script.append(f'  const content = await page.$eval("{selector}", el => el.textContent);')
				script.append('  console.log(content);')

			elif action_type == 'done':
				pass

			else:
				script.append(f'  // Unsupported action: {action_type}')

		script.extend(['', '  await browser.close();', '}', '', 'run().catch(console.error);'])

		return '\n'.join(script)

	def _to_playwright_python(self) -> str:
		"""
		Convert the action log to a Playwright Python script.

		Returns:
		    str: Playwright Python script as a string
		"""
		script = [
			'# Playwright Python script generated from browser-use actions',
			'import asyncio',
			'from playwright.async_api import async_playwright',
			'',
			'async def run():',
			'    async with async_playwright() as p:',
			'        browser = await p.chromium.connect_over_cdp(',
			"            endpoint_url='wss://production-sfo.browserless.io?token=YOUR_API_TOKEN_HERE'",
			'        )',
			'        page = await browser.new_page()',
			'',
		]

		for action in self.action_log:
			action_type = action.get('action_type')
			params = action.get('params', {})
			selector_info = action.get('selector')

			if action_type == 'go_to_url':
				url = params.get('url', '')
				script.append(f'        await page.goto("{url}")')

			elif action_type == 'click_element_by_index' and selector_info:
				selector = selector_info.get('xpath', '')
				script.append(f'        await page.click("{selector}")')

			elif action_type == 'input_text' and selector_info:
				selector = selector_info.get('xpath', '')
				text = params.get('text', '')
				script.append(f'        await page.fill("{selector}", "{text}")')

			elif action_type == 'scroll_down':
				amount = params.get('amount', 100)
				script.append(f'        await page.evaluate(f"window.scrollBy(0, {amount})")')

			elif action_type == 'scroll_up':
				amount = params.get('amount', 100)
				script.append(f'        await page.evaluate(f"window.scrollBy(0, -{amount})")')

			elif action_type == 'extract_content' and selector_info:
				selector = selector_info.get('xpath', '')
				script.append(f'        content = await page.text_content("{selector}")')
				script.append('        print(content)')

			elif action_type == 'done':
				pass

			else:
				script.append(f'        # Unsupported action: {action_type}')

		script.extend(['', '        await browser.close()', '', 'asyncio.run(run())'])

		return '\n'.join(script)

	def get_script(self, format_type: str, **kwargs) -> str:
		"""
		Get a script in the specified format.

		Args:
		    format_type: Script format type ('browserql' or 'baas_v2')
		    **kwargs: Additional arguments for the converter

		Returns:
		    str: Generated script
		"""
		if format_type.lower() == 'browserql':
			return self.to_browserql()
		elif format_type.lower() == 'baas_v2':
			language = kwargs.get('language', 'javascript')
			return self.to_baas_v2(language=language)
		else:
			return f'# Unsupported format: {format_type}'
