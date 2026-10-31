#!/usr/bin/env python3
"""Select a conservative, AI-free staging news digest; never publish to the site."""
import datetime as dt
import hashlib
import json
import pathlib
import re
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent
CANDIDATES = ROOT / "candidates.json"
OUTPUT = ROOT / "selected.json"
MAX_ITEMS = 12
MAX_PER_SOURCE = 3
TOPICS = ("Ukraine", "Iran", "Gaza", "Multiple conflicts", "Defence & security")

def key_title(value):
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

def select(rows, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=48)
    eligible = []
    for item in rows:
        try:
            when = dt.datetime.fromisoformat(item["published"])
            if when.tzinfo is None or not cutoff <= when <= now + dt.timedelta(hours=1):
                continue
            url = urlsplit(item["url"])
            if url.scheme != "https" or not url.hostname:
                continue
            if item.get("status") != "candidate" or item.get("category") not in TOPICS:
                continue
            title = item["title"].strip()
            if len(title) < 20 or not item.get("source"):
                continue
            eligible.append((when, item))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    eligible.sort(key=lambda x: x[0], reverse=True)
    seen_titles, seen_urls, source_counts = set(), set(), {}
    selected = []
    for _, item in eligible:
        title_key = key_title(item["title"])
        url = item["url"].split("#", 1)[0]
        source = item["source"]
        if title_key in seen_titles or url in seen_urls or source_counts.get(source, 0) >= MAX_PER_SOURCE:
            continue
        seen_titles.add(title_key)
        seen_urls.add(url)
        source_counts[source] = source_counts.get(source, 0) + 1
        selected.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:20],
            "title": item["title"], "url": url, "source": source,
            "published": item["published"], "category": item["category"],
            "status": "staging_unverified", "summary_verified": False
        })
        if len(selected) == MAX_ITEMS:
            break
    return selected

def main():
    rows = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    selected = select(rows)
    if len(selected) < 6 or len({x["source"] for x in selected}) < 3:
        raise SystemExit("Selection failed: fewer than 6 stories or 3 sources; no staging update")
    OUTPUT.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("STAGING SELECTED", len(selected), "from", len({x["source"] for x in selected}), "sources")
    print("No live HTML or publishing files modified.")

if __name__ == "__main__":
    main()
