#!/usr/bin/env python3
"""Incremental News-only translation staging; never changes Analysis."""
import json
import os
from pathlib import Path
import urllib.request

BASE = Path(__file__).resolve().parent.parent
ARCHIVE = BASE / "automation" / "editorial.json"
OUTPUT = BASE / "automation" / "news_translations.json"

def translate(article, language, key):
    prompt = ("Translate this News article faithfully to " + language +
              ". Keep all facts, attribution and uncertainty. Return JSON keys t, s, p; "
              "p must be an array matching the original paragraphs. " +
              json.dumps(article, ensure_ascii=False))
    payload = {"model": os.getenv("WATCHFLOOR_AI_MODEL", "gpt-4.1-mini"),
               "messages": [{"role": "user", "content": prompt}],
               "response_format": {"type": "json_object"}, "temperature": 0}
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    return json.loads(result["choices"][0]["message"]["content"])

def main():
    if not ARCHIVE.exists():
        print("No staged articles")
        return
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        print("No API key, skipping translations")
        return
    languages = [name for name in json.loads((BASE / "i18n" / "ui.json").read_text()) if name != "en"]
    articles = json.loads(ARCHIVE.read_text()).get("items", [])
    existing = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {}
    remaining = max(0, min(30, int(os.getenv("WATCHFLOOR_MAX_TRANSLATIONS", "12"))))
    for article in articles:
        if remaining == 0:
            break
        if article.get("section") != "News" or article.get("status") != "staging_review_required":
            continue
        for language in languages:
            if remaining == 0:
                break
            if article["id"] in existing.get(language, {}):
                continue
            original = {"title": article["title"], "summary": article["summary"],
                        "paragraphs": article["paragraphs"]}
            try:
                translated = translate(original, language, key)
                paragraphs = translated.get("p")
                if not isinstance(translated.get("t"), str) or not isinstance(translated.get("s"), str):
                    continue
                if not isinstance(paragraphs, list) or len(paragraphs) != len(original["paragraphs"]):
                    continue
                if not all(isinstance(p, str) and len(p) > 20 for p in paragraphs):
                    continue
                existing.setdefault(language, {})[article["id"]] = translated
                remaining -= 1
            except Exception as exc:
                print("Translation stopped:", type(exc).__name__)
                remaining = 0
    OUTPUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n")
    print("News-only translation staging completed")

if __name__ == "__main__":
    main()
