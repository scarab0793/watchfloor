"""Offline tests for the News-only publication feed."""
import unittest
import build_news_feed

def story(section="News", status="approved", identifier="news-1"):
    return {
        "id": identifier, "section": section, "status": status,
        "title": "Verified military equipment update",
        "summary": "Multiple sources describe a documented equipment development.",
        "paragraphs": ["A verified source paragraph with attribution and enough detail to pass basic structural checks." for _ in range(6)],
        "published_at": "2026-10-31T10:00:00+00:00",
        "category": "Defence & security",
        "sources": [{"publisher": "Example", "url": "https://example.org/news/1"}]
    }

class NewsFeedTests(unittest.TestCase):
    def test_analysis_is_never_published(self):
        result = build_news_feed.build([story("Analysis")], {}, ["en", "hu"])
        self.assertEqual(result, [])

    def test_unreviewed_items_are_excluded(self):
        self.assertEqual(build_news_feed.build([story(status="staging_review_required")], {}, ["en"]), [])
        self.assertEqual(build_news_feed.build([story(status="candidate")], {}, ["en"]), [])

    def test_duplicate_ids_are_excluded(self):
        self.assertEqual(len(build_news_feed.build([story(), story()], {}, ["en"])), 1)

    def test_news_and_translation_are_included(self):
        original = story()
        translations = {"hu": {"news-1": {
            "t": "Ellenorzott katonai hir", "s": "Rovid osszefoglalo",
            "p": ["Magyar forditas bekezdes"] * 6}}}
        result = build_news_feed.build([original], translations, ["en", "hu"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["section"], "News")
        self.assertIn("hu", result[0]["translations"])

    def test_bad_source_url_is_excluded(self):
        original = story()
        original["sources"][0]["url"] = "javascript:alert(1)"
        self.assertEqual(build_news_feed.build([original], {}, ["en"]), [])

if __name__ == "__main__":
    unittest.main()
