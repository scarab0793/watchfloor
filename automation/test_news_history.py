"""Regression tests for preservation of published News history."""
import unittest
import build_news_feed

def item(identifier, published="2026-10-31T10:00:00+00:00"):
    return {"id": identifier, "section": "News", "published_at": published}

class HistoryTests(unittest.TestCase):
    def test_old_news_is_preserved(self):
        result = build_news_feed.preserve_history([item("new", "2026-11-01T10:00:00+00:00")],
            {"section": "News", "items": [item("old")]})
        self.assertEqual([x["id"] for x in result], ["new", "old"])

    def test_duplicate_id_is_not_readded(self):
        result = build_news_feed.preserve_history([item("same")],
            {"section": "News", "items": [item("same")]})
        self.assertEqual(len(result), 1)

    def test_analysis_in_history_aborts(self):
        bad = item("analysis")
        bad["section"] = "Analysis"
        with self.assertRaises(SystemExit):
            build_news_feed.preserve_history([item("new")], {"section": "News", "items": [bad]})

    def test_missing_id_aborts(self):
        with self.assertRaises(SystemExit):
            build_news_feed.preserve_history([item("new")],
                {"section": "News", "items": [{"section": "News", "published_at": "2026-10-31"}]})

    def test_invalid_root_aborts(self):
        with self.assertRaises(SystemExit):
            build_news_feed.preserve_history([item("new")], {"section": "Analysis", "items": []})

if __name__ == "__main__":
    unittest.main()
