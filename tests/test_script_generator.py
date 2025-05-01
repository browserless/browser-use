"""Unit tests for the ScriptGenerator class."""
import sys
from pathlib import Path
import unittest

sys.path.append(str(Path(__file__).parent.parent))

from browser_use.script_generation.service import ScriptGenerator


class TestScriptGenerator(unittest.TestCase):
    """Test the ScriptGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.action_log = [
            {
                "action_type": "go_to_url",
                "params": {"url": "https://example.com"},
                "selector": None,
                "timestamp": 1620000000.0
            },
            {
                "action_type": "click_element_by_index",
                "params": {"index": 1},
                "selector": {
                    "xpath": "//a[@href='https://www.iana.org/domains/example']",
                    "tag_name": "a",
                    "attributes": {"href": "https://www.iana.org/domains/example"},
                    "index": 1,
                    "is_visible": True,
                    "is_interactive": True
                },
                "timestamp": 1620000001.0
            },
            {
                "action_type": "input_text",
                "params": {"index": 2, "text": "search term"},
                "selector": {
                    "xpath": "//input[@id='search']",
                    "tag_name": "input",
                    "attributes": {"id": "search", "type": "text"},
                    "index": 2,
                    "is_visible": True,
                    "is_interactive": True
                },
                "timestamp": 1620000002.0
            }
        ]
        self.generator = ScriptGenerator(self.action_log)

    def test_browserql_generation(self):
        """Test BrowserQL script generation."""
        script = self.generator.to_browserql()
        
        self.assertIn('goto(url: "https://example.com")', script)
        self.assertIn('click(selector: "//a[@href=\'https://www.iana.org/domains/example\']")', script)
        self.assertIn('type(selector: "//input[@id=\'search\']", text: "search term")', script)
        
        self.assertTrue(script.startswith("mutation AutomateTask {"))
        self.assertTrue(script.endswith("}"))

    def test_baas_v2_javascript_generation(self):
        """Test BaaS V2 JavaScript script generation."""
        script = self.generator.to_baas_v2(language="javascript")
        
        self.assertIn('await page.goto("https://example.com");', script)
        self.assertIn('await page.click("//a[@href=\'https://www.iana.org/domains/example\']");', script)
        self.assertIn('await page.type("//input[@id=\'search\']", "search term");', script)
        
        self.assertIn("const puppeteer = require('puppeteer');", script)
        self.assertIn("async function run() {", script)
        self.assertIn("await browser.close();", script)

    def test_baas_v2_python_generation(self):
        """Test BaaS V2 Python script generation."""
        script = self.generator.to_baas_v2(language="python")
        
        self.assertIn('await page.goto("https://example.com")', script)
        self.assertIn('await page.click("//a[@href=\'https://www.iana.org/domains/example\']")', script)
        self.assertIn('await page.fill("//input[@id=\'search\']", "search term")', script)
        
        self.assertIn("import asyncio", script)
        self.assertIn("from playwright.async_api import async_playwright", script)
        self.assertIn("async def run():", script)
        self.assertIn("await browser.close()", script)

    def test_empty_action_log(self):
        """Test script generation with empty action log."""
        empty_generator = ScriptGenerator([])
        
        browserql_script = empty_generator.to_browserql()
        self.assertEqual(browserql_script, "# No actions to convert")
        
        baas_js_script = empty_generator.to_baas_v2(language="javascript")
        self.assertEqual(baas_js_script, "# No actions to convert")
        
        baas_py_script = empty_generator.to_baas_v2(language="python")
        self.assertEqual(baas_py_script, "# No actions to convert")

    def test_unsupported_action_types(self):
        """Test handling of unsupported action types."""
        action_log_with_unsupported = self.action_log + [
            {
                "action_type": "unsupported_action",
                "params": {},
                "selector": None,
                "timestamp": 1620000003.0
            }
        ]
        
        generator = ScriptGenerator(action_log_with_unsupported)
        
        browserql_script = generator.to_browserql()
        self.assertIn("# Unsupported action: unsupported_action", browserql_script)
        
        baas_js_script = generator.to_baas_v2(language="javascript")
        self.assertIn("// Unsupported action: unsupported_action", baas_js_script)
        
        baas_py_script = generator.to_baas_v2(language="python")
        self.assertIn("# Unsupported action: unsupported_action", baas_py_script)


if __name__ == "__main__":
    unittest.main()
