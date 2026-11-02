"""Source-evidence gate tests; do not spend AI credits on unsupported News."""
import unittest
from urllib.parse import urlsplit
import editorial

class EditorialEvidenceTests(unittest.TestCase):
    def test_domain_normalization_matches_approval(self):
        urls = ["https://www.example.org/story", "https://example.org/other"]
        domains = {urlsplit(url).hostname.lower().removeprefix("www.") for url in urls}
        self.assertEqual(len(domains), 1)

    def test_different_domains_count_as_distinct(self):
        urls = ["https://example.org/story", "https://another.example.net/story"]
        domains = {urlsplit(url).hostname.lower().removeprefix("www.") for url in urls}
        self.assertEqual(len(domains), 2)

    def test_editorial_has_evidence_gate_before_api(self):
        from pathlib import Path
        code = (Path(__file__).parent / "editorial.py").read_text()
        self.assertIn('len(s["reference"]) >= CFG["min_source_article_characters"]', code)
        self.assertIn('if len(substantial) < 2:', code)
        self.assertLess(code.index('if len(substantial) < 2:'), code.index('article=api(prompt)'))

if __name__ == "__main__":
    unittest.main()
