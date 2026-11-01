#!/usr/bin/env python3
"""Build an approved News-only feed, never publishing unreviewed drafts or Analysis."""
import json
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent.parent
EDITORIAL = BASE / "automation" / "editorial.json"
TRANSLATIONS = BASE / "automation" / "news_translations.json"
OUTPUT = BASE / "data" / "automated-news.json"

def valid_source(source):
    if not isinstance(source, dict):
        return False
    url = urlsplit(source.get("url", ""))
    return url.scheme == "https" and bool(url.hostname) and bool(source.get("publisher"))

def build(articles, translations, languages):
    result = []
    seen = set()
    for article in articles:
        if article.get("section") != "News" or article.get("status") != "approved":
            continue
        item_id = article.get("id")
        paragraphs = article.get("paragraphs", [])
        sources = article.get("sources", [])
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            continue
        if not isinstance(paragraphs, list) or len(paragraphs) < 5:
            continue
        if not all(isinstance(p, str) and len(p) > 70 for p in paragraphs):
            continue
        if not sources or not all(valid_source(s) for s in sources):
            continue
        if not all(isinstance(article.get(k), str) and article[k].strip() for k in ("title", "summary", "published_at")):
            continue
        localized = {}
        complete = True
        for lang in languages:
            if lang == "en":
                continue
            t = translations.get(lang, {}).get(item_id)
            if not isinstance(t, dict) or not all(isinstance(t.get(k), str) and t[k].strip() for k in ("t", "s")):
                complete = False
                break
            if not isinstance(t.get("p"), list) or len(t["p"]) != len(paragraphs) or not all(isinstance(p, str) and len(p) >= 20 for p in t["p"]):
                complete = False
                break
            localized[lang] = t
        if not complete:
            continue
        result.append({
            "id": item_id, "section": "News", "title": article["title"],
            "summary": article["summary"], "paragraphs": paragraphs,
            "published_at": article["published_at"], "category": article.get("category", ""),
            "sources": sources, "image": article.get("image", ""),
            "image_credit": article.get("image_credit", ""),
            "translations": localized
        })
        seen.add(item_id)
    return sorted(result, key=lambda item: item["published_at"], reverse=True)

def preserve_history(items, previous):
    """Merge new News with published News, refusing malformed history."""
    if previous.get("section") != "News" or not isinstance(previous.get("items"), list):
        raise SystemExit("Invalid existing News feed; refusing overwrite")
    merged = list(items)
    existing_ids = {item["id"] for item in merged}
    for prior in previous["items"]:
        if not isinstance(prior, dict) or prior.get("section") != "News":
            raise SystemExit("Unexpected non-News entry in existing feed; refusing overwrite")
        prior_id = prior.get("id")
        if not isinstance(prior_id, str) or not prior_id:
            raise SystemExit("Existing News entry missing valid ID; refusing overwrite")
        if not isinstance(prior.get("published_at"), str) or not prior["published_at"]:
            raise SystemExit("Existing News entry missing timestamp; refusing overwrite")
        if prior_id not in existing_ids:
            merged.append(prior)
            existing_ids.add(prior_id)
    return sorted(merged, key=lambda item: item["published_at"], reverse=True)

def main():
    if not EDITORIAL.exists():
        print("No editorial archive; preserving existing News feed")
        return
    articles = json.loads(EDITORIAL.read_text()).get("items", [])
    translations = json.loads(TRANSLATIONS.read_text()) if TRANSLATIONS.exists() else {}
    languages = json.loads((BASE / "i18n" / "ui.json").read_text()).keys()
    items = build(articles, translations, languages)
    if not items:
        print("No approved News articles; preserving existing News feed")
        return
    if OUTPUT.exists():
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        items = preserve_history(items, previous)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"schema_version": 1, "section": "News", "items": items},
                                  ensure_ascii=False, indent=2) + "\n")
    print("Built News-only feed:", len(items), "items. Analysis untouched.")

if __name__ == "__main__":
    main()
