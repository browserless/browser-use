"""Standalone test for the ScriptGenerator class."""
import sys
import os
import unittest
from pathlib import Path

script_generation_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    "browser_use", "script_generation")
sys.path.append(script_generation_dir)

from service import ScriptGenerator


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


if __name__ == "__main__":
    unittest.main()
