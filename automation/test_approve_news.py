"""Approval gate unit tests: News only, no unverified automatic publishing."""
import datetime as dt
import unittest
import approve_news

NOW = dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc)

def article(section="News"):
    return {
        "id": "example-1", "section": section, "status": "staging_review_required",
        "ai_edited": True, "title": "Verified military equipment update",
        "summary": "Two independent reports document a military equipment update.",
        "paragraphs": ["A verified military report with attributed information and sufficient contextual detail " * 7 for _ in range(6)],
        "published_at": "2026-11-01T10:00:00+00:00",
        "sources": [
            {"publisher": "Publisher A", "url": "https://example.org/news/1"},
            {"publisher": "Publisher B", "url": "https://another.example.com/news/2"}
        ]
    }

def translations():
    return {"hu": {"example-1": {"t": "Katonai hir", "s": "Osszefoglalo",
        "p": ["Magyarul irt bekezdes hosszabb szoveggel"] * 6}}}

class ApprovalTests(unittest.TestCase):
    def test_analysis_never_approved(self):
        self.assertFalse(approve_news.eligible(article("Analysis"), translations(), ["en", "hu"], NOW))

    def test_missing_translation_blocks_approval(self):
        self.assertFalse(approve_news.eligible(article(), {}, ["en", "hu"], NOW))

    def test_single_source_blocks_approval(self):
        item = article()
        item["sources"] = item["sources"][:1]
        self.assertFalse(approve_news.eligible(item, translations(), ["en", "hu"], NOW))

    def test_stale_article_blocks_approval(self):
        item = article()
        item["published_at"] = "2026-09-01T10:00:00+00:00"
        self.assertFalse(approve_news.eligible(item, translations(), ["en", "hu"], NOW))

    def test_complete_news_is_eligible(self):
        self.assertTrue(approve_news.eligible(article(), translations(), ["en", "hu"], NOW))

if __name__ == "__main__":
    unittest.main()
