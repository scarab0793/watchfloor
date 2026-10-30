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

    def test_clean(self):
        self.assertEqual(collect.clean("<b>Hello</b>   world"), "Hello world")

if __name__ == "__main__":
    unittest.main()
