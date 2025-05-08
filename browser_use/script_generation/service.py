"""Script generation service for browser-use."""

import logging
from typing import Dict, List, Optional
from collections import defaultdict

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
		self._action_counts = defaultdict(int)

	def set_action_log(self, action_log: List[Dict]) -> None:
		"""
		Set the action log to convert.

		Args:
		    action_log: List of action log entries
		"""
		self.action_log = action_log
		self._action_counts.clear()

	def _get_action_alias(self, action_type: str) -> str:
		"""
		Get an alias for a repeated action type.
		
		Args:
		    action_type: The type of action
		    
		Returns:
		    str: The alias for the action
		"""
		self._action_counts[action_type] += 1
		count = self._action_counts[action_type]
		if count == 1:
			return ""
		return f"{action_type}{count}:"

	def _xpath_to_css(self, xpath: str) -> Optional[str]:
		"""
		Convert an XPath selector to a CSS selector.
		
		Args:
		    xpath: The XPath selector to convert
		    
		Returns:
		    Optional[str]: The CSS selector, or None if conversion fails
		"""
		if not xpath:
			return None
			
		# Remove any xpath= prefix
		if xpath.startswith('xpath='):
			xpath = xpath[6:]
			
		# Handle absolute paths
		if xpath.startswith('/'):
			xpath = xpath[1:]
			
		# Split into parts
		parts = xpath.split('/')
		css_parts = []
		
		for i, part in enumerate(parts):
			if not part:
				continue
				
			# Handle element name and predicates
			if '[' in part:
				element, predicates = part.split('[', 1)
				predicates = predicates.rstrip(']')
				
				# Add element name if present
				current_part = element if element else '*'
				
				# Handle predicates
				if predicates:
					# Handle @id
					if predicates.startswith('@id='):
						id_value = predicates[4:].strip('"').strip("'")
						current_part += f"#{id_value}"
					# Handle @class
					elif predicates.startswith('@class='):
						class_value = predicates[7:].strip('"').strip("'")
						current_part += f".{class_value.replace(' ', '.')}"
					# Handle @href
					elif predicates.startswith('@href='):
						href_value = predicates[6:].strip('"').strip("'")
						current_part += f'[href="{href_value}"]'
					# Handle position
					elif predicates.isdigit():
						current_part += f":nth-child({int(predicates) + 1})"
				
				css_parts.append(current_part)
			else:
				css_parts.append(part)
					
		return ' > '.join(css_parts)

	def _get_url_from_params(self, params: Dict) -> str:
		"""
		Extract URL from params, handling both nested and direct structures.
		
		Args:
		    params: The params dictionary from the action log
		    
		Returns:
		    str: The extracted URL or empty string if not found
		"""
		# Handle nested structure (params.go_to_url.url)
		if 'go_to_url' in params and isinstance(params['go_to_url'], dict):
			return params['go_to_url'].get('url', '')
		# Handle direct structure (params.url)
		return params.get('url', '')

	def _get_text_from_params(self, params: Dict) -> str:
		"""
		Extract text from params, handling both nested and direct structures.
		
		Args:
		    params: The params dictionary from the action log
		    
		Returns:
		    str: The extracted text or empty string if not found
		"""
		# Handle nested structure (params.input_text.text)
		if 'input_text' in params and isinstance(params['input_text'], dict):
			return params['input_text'].get('text', '')
		# Handle direct structure (params.text)
		return params.get('text', '')

	def to_browserql(self) -> str:
		"""
		Convert the action log to a BrowserQL script.

		Returns:
		    str: BrowserQL script as a string
		"""
		if not self.action_log:
			return '# No actions to convert'

		script_parts = ['mutation AutomateTask {']

		for action in self.action_log:
			action_type = action.get('action_type')
			params = action.get('params', {})
			selector_info = action.get('selector')

			if action_type == 'go_to_url':
				url = self._get_url_from_params(params)
				script_parts.append(f'  goto(url: "{url}") {{')
				script_parts.append('    status')
				script_parts.append('  }')

			elif action_type == 'click_element_by_index' and selector_info:
				xpath = selector_info.get('xpath', '')
				css_selector = self._xpath_to_css(xpath)
				if css_selector:
					alias = self._get_action_alias('click')
					script_parts.append(f'  {alias}click(selector: "{css_selector}") {{')
					script_parts.append('    selector')
					script_parts.append('    time')
					script_parts.append('  }')
				else:
					script_parts.append(f'  # Failed to convert XPath to CSS: {xpath}')

			elif action_type == 'input_text' and selector_info:
				xpath = selector_info.get('xpath', '')
				css_selector = self._xpath_to_css(xpath)
				text = self._get_text_from_params(params)
				if css_selector:
					script_parts.append(f'  type(selector: "{css_selector}", text: "{text}") {{')
					script_parts.append('    selector')
					script_parts.append('    text')
					script_parts.append('  }')
				else:
					script_parts.append(f'  # Failed to convert XPath to CSS: {xpath}')

			elif action_type == 'scroll_down':
				script_parts.append(f'  scroll(direction: "down", amount: {params.get("amount", 100)}) {{')
				script_parts.append('    status')
				script_parts.append('  }')

			elif action_type == 'scroll_up':
				script_parts.append(f'  scroll(direction: "up", amount: {params.get("amount", 100)}) {{')
				script_parts.append('    status')
				script_parts.append('  }')

			elif action_type == 'extract_content' and selector_info:
				xpath = selector_info.get('xpath', '')
				css_selector = self._xpath_to_css(xpath)
				if css_selector:
					script_parts.append(f'  querySelector(selector: "{css_selector}") {{')
					script_parts.append('    innerHTML')
					script_parts.append('  }')
				else:
					script_parts.append(f'  # Failed to convert XPath to CSS: {xpath}')

			elif action_type == 'done':
				pass

			else:
				script_parts.append(f'  # Unsupported action: {action_type}')

			# Add newline between actions except for the last one
			if action_type != 'done':
				script_parts.append('')

		# Remove the last empty line if it exists
		if script_parts[-1] == '':
			script_parts.pop()
			
		script_parts.append('}')
		return '\n'.join(script_parts)

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
