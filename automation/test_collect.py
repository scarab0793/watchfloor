"""Offline tests for feed parsing and date filtering."""
import datetime as dt
import unittest
from unittest.mock import patch
import collect

RSS = b"""<rss><channel><item><title>Example &amp; update</title><link>https://example.org/news/1</link><pubDate>Fri, 30 Oct 2026 09:00:00 GMT</pubDate><description>Short summary</description></item></channel></rss>"""
ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom headline</title><link rel="alternate" href="https://example.org/atom/1"/><updated>2026-10-30T09:00:00Z</updated><summary>Text</summary></entry></feed>"""

class CollectorTests(unittest.TestCase):
    def test_rss(self):
        self.assertEqual(list(collect.parse(RSS))[0][0], "Example & update")

    def test_atom(self):
        row = list(collect.parse(ATOM))[0]
        self.assertEqual(row[1], "https://example.org/atom/1")
        self.assertEqual(collect.date(row[2]).year, 2026)

    def test_date(self):
        self.assertEqual(collect.date("Fri, 30 Oct 2026 09:00:00 GMT").tzinfo, dt.timezone.utc)
        self.assertIsNone(collect.date("invalid"))

    def test_classification(self):
        self.assertEqual(collect.classify("Russian drone strikes Ukraine", ""), "Ukraine")
        self.assertEqual(collect.classify("Iran launches missile", ""), "Iran")
        self.assertEqual(collect.classify("Gaza ceasefire negotiations", ""), "Gaza")
        self.assertEqual(collect.classify("NATO tests new radar", ""), "Defence & security")
        self.assertEqual(collect.classify("Iran and Israel exchange warnings", ""), "Multiple conflicts")

    def test_canonical_url(self):
        self.assertEqual(collect.canonical_url("https://EXAMPLE.org/a?utm_source=x&v=1#part"), "https://example.org/a?v=1")
        self.assertIsNone(collect.canonical_url("javascript:alert(1)"))

    def test_article_metadata_parser(self):
        parser = collect.ArticleMetadata()
        parser.feed('<html><head><meta property="article:published_time" content="2026-10-30T12:00:00Z"><meta property="og:title" content="Ukraine defence update"></head><body><h1>Fallback headline</h1></body></html>')
        self.assertEqual(collect.date(parser.dates[0]).year, 2026)
        self.assertEqual(parser.titles[0], "Ukraine defence update")

    def test_jsonld_date(self):
        chunks = ['{"@graph":[{"@type":"NewsArticle","datePublished":"2026-10-30T11:30:00Z"}]}']
        self.assertEqual(collect.jsonld_dates(chunks), ["2026-10-30T11:30:00Z"])

    def test_jsonld_malformed(self):
        self.assertEqual(collect.jsonld_dates(["not json"]), [])

    def test_article_metadata_no_date(self):
        parser = collect.ArticleMetadata()
        parser.feed("<html><h1>Undated article</h1></html>")
        self.assertEqual(parser.dates, [])

    def test_clean(self):
        self.assertEqual(collect.clean("<b>Hello</b>   world"), "Hello world")

if __name__ == "__main__":
    unittest.main()
