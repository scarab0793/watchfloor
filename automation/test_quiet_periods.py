"""Quiet-period behavior for News candidate selection."""
import datetime as dt
import unittest
import select

NOW = dt.datetime(2026, 11, 1, 12, tzinfo=dt.timezone.utc)

def candidate(source="Example", title="Verified military equipment update"):
    return {"title": title, "url": "https://example.org/article",
            "source": source, "published": NOW.isoformat(),
            "category": "Defence & security", "status": "candidate"}

class QuietPeriodTests(unittest.TestCase):
    def test_one_valid_story_can_be_selected(self):
        selected = select.select([candidate()], NOW)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["status"], "staging_unverified")

    def test_empty_candidates_are_valid(self):
        self.assertEqual(select.select([], NOW), [])

    def test_expired_story_is_not_selected(self):
        item = candidate()
        item["published"] = (NOW - dt.timedelta(days=4)).isoformat()
        self.assertEqual(select.select([item], NOW), [])

    def test_bad_source_link_is_not_selected(self):
        item = candidate()
        item["url"] = "http://example.org/article"
        self.assertEqual(select.select([item], NOW), [])

if __name__ == "__main__":
    unittest.main()
