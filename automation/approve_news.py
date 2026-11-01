#!/usr/bin/env python3
"""Conservative News-only automatic approval; never changes Analysis."""
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "editorial.json"
TRANSLATIONS = ROOT / "news_translations.json"
LANGUAGES = ROOT.parent / "i18n" / "ui.json"

def eligible(article, translations, languages, now):
    if article.get("section") != "News" or article.get("status") != "staging_review_required":
        return False
    if not article.get("ai_edited"):
        return False
    sources = article.get("sources", [])
    if not isinstance(sources, list) or len(sources) < 2:
        return False
    domains = set()
    for source in sources:
        if not isinstance(source, dict) or not source.get("publisher"):
            return False
        parsed = urlsplit(source.get("url", ""))
        if parsed.scheme != "https" or not parsed.hostname:
            return False
        domains.add(parsed.hostname.lower().removeprefix("www."))
    if len(domains) < 2:
        return False
    paragraphs = article.get("paragraphs", [])
    if not isinstance(paragraphs, list) or not 5 <= len(paragraphs) <= 12:
        return False
    if not all(isinstance(p, str) and len(p) >= 70 for p in paragraphs):
        return False
    if not 350 <= len(" ".join(paragraphs).split()) <= 850:
        return False
    if not isinstance(article.get("title"), str) or not article["title"].strip():
        return False
    if not isinstance(article.get("summary"), str) or not article["summary"].strip():
        return False
    try:
        published = dt.datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
        if published.tzinfo is None:
            return False
        age = now - published.astimezone(dt.timezone.utc)
        if not dt.timedelta(0) <= age <= dt.timedelta(days=7):
            return False
    except (ValueError, KeyError, TypeError):
        return False
    for language in languages:
        if language == "en":
            continue
        translated = translations.get(language, {}).get(article.get("id"))
        if not isinstance(translated, dict):
            return False
        if not all(isinstance(translated.get(k), str) and translated[k].strip() for k in ("t", "s")):
            return False
        if not isinstance(translated.get("p"), list) or len(translated["p"]) != len(paragraphs):
            return False
        if not all(isinstance(p, str) and len(p) >= 20 for p in translated["p"]):
            return False
    return True

def main():
    if not ARCHIVE.exists() or not TRANSLATIONS.exists():
        print("Approval withheld: missing editorial archive or translations")
        return
    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    translations = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    languages = list(json.loads(LANGUAGES.read_text(encoding="utf-8")))
    now = dt.datetime.now(dt.timezone.utc)
    approved = 0
    for article in archive.get("items", []):
        if eligible(article, translations, languages, now):
            article["status"] = "approved"
            approved += 1
    if approved:
        ARCHIVE.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("News articles automatically approved:", approved, "(Analysis unchanged)")

if __name__ == "__main__":
    main()
