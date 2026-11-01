#!/usr/bin/env python3
"""Offline safety tests for News editorial isolation and translations."""
import json
import pathlib
import unittest

BASE = pathlib.Path(__file__).resolve().parent

class NewsSafetyTests(unittest.TestCase):
    def test_config_protects_analysis(self):
        config = json.loads((BASE / "editorial_config.json").read_text())
        self.assertEqual(config["allowed_sections"], ["News"])
        self.assertIn("Analysis", config["protected_sections"])
        self.assertFalse(config["analysis_automation_enabled"])

    def test_editorial_output_is_news_only(self):
        code = (BASE / "editorial.py").read_text()
        self.assertIn('x.get("section","News")', code)
        self.assertIn('"section":"News"', code)

    def test_translation_excludes_analysis(self):
        code = (BASE / "translate_news.py").read_text()
        self.assertIn('article.get("section") != "News"', code)
        self.assertIn('news_translations.json', code)
        self.assertNotIn('i18n" / language', code)

    def test_template_only_adds_news(self):
        template = (BASE.parent / "template.html").read_text()
        self.assertIn('feed.section!=="News"', template)
        self.assertIn('a.section!=="News"', template)
        self.assertIn('existing.has(a.id)', template)
        self.assertIn("loadAutomatedNews();", template)

    def test_live_files_not_modified_by_workflow(self):
        workflow = (BASE.parent / ".github" / "workflows" / "editorial-staging.yml").read_text()
        self.assertIn("automation/news_translations.json", workflow)
        self.assertNotIn("git add index.html", workflow)
        self.assertNotIn("git add i18n/", workflow)

if __name__ == "__main__":
    unittest.main()
