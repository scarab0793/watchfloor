#!/usr/bin/env python3
"""Collect candidate defence headlines without AI. Never publishes to the live site."""
import datetime as dt
import email.utils
import hashlib
import json
import pathlib
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "candidates.json"
NOW = dt.datetime.now(dt.timezone.utc)
CUTOFF = NOW - dt.timedelta(hours=48)
NS = {"atom": "http://www.w3.org/2005/Atom"}
MAX_PER_SOURCE = 20

def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()

def date(value):
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value).astimezone(dt.timezone.utc)
    except (TypeError, ValueError, IndexError):
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
        except (ValueError, TypeError):
            return None

def parse(xml):
    root = ET.fromstring(xml)
    entries = root.findall(".//item")
    if entries:
        for item in entries:
            yield (item.findtext("title"), item.findtext("link"),
                   item.findtext("pubDate"), item.findtext("description"))
    else:
        for item in root.findall(".//atom:entry", NS):
            links = item.findall("atom:link", NS)
            link = next((x.attrib.get("href") for x in links if x.attrib.get("rel", "alternate") == "alternate"), None)
            yield (item.findtext("atom:title", namespaces=NS), link,
                   item.findtext("atom:published", namespaces=NS) or item.findtext("atom:updated", namespaces=NS),
                   item.findtext("atom:summary", namespaces=NS))

TOPICS = {
    "Ukraine": ("ukraine", "ukrainian", "kyiv", "kharkiv", "donetsk", "zelensky", "russia", "russian", "kremlin"),
    "Iran": ("iran", "iranian", "tehran", "irgc", "strait of hormuz", "persian gulf"),
    "Gaza": ("gaza", "hamas", "israel", "israeli", "idf", "rafah", "west bank"),
}
DEFENCE_TERMS = ("military", "defence", "defense", "army", "navy", "air force", "aircraft", "missile", "drone", "warship", "fighter jet", "artillery", "weapons", "security", "nato", "warfare", "submarine", "radar", "munition")

def classify(title, summary):
    # Classify by headline first, avoiding a long unrelated RSS description.
    title = title.casefold()
    summary = summary.casefold()
    matches = [name for name, words in TOPICS.items() if any(w in title for w in words)]
    if not matches:
        matches = [name for name, words in TOPICS.items() if any(w in summary for w in words)]
    if matches:
        return matches[0] if len(matches) == 1 else "Multiple conflicts"
    return "Defence & security" if any(w in title for w in DEFENCE_TERMS) else "Other"

def canonical_url(value):
    try:
        parts = urlsplit(value.strip())
        if parts.scheme not in ("https", "http") or not parts.hostname:
            return None
        if parts.username or parts.password or parts.hostname in ("localhost",):
            return None
        query = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                           if not k.casefold().startswith(("utm_", "fbclid", "gclid"))])
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", query, ""))
    except ValueError:
        return None

def main():
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["sources"]
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    found = {x["id"]: x for x in old if x.get("id")}
    errors = []
    for source in sources:
        try:
            req = urllib.request.Request(source["url"], headers={"User-Agent": "WatchFloorFeedCollector/0.1 (news aggregation)"})
            with urllib.request.urlopen(req, timeout=20) as response:
                content = response.read(2_000_000)
            count = 0
            for title, url, published, summary in parse(content):
                when = date(published)
                title, url = clean(title), canonical_url(url or "")
                if not (title and url and when and CUTOFF <= when <= NOW + dt.timedelta(hours=1)):
                    continue
                key = hashlib.sha256(url.encode()).hexdigest()[:20]
                found[key] = {"id": key, "title": title, "url": url,
                              "source": source["name"], "published": when.isoformat(),
                              "summary": clean(summary)[:500], "category": classify(title, clean(summary)),\n                              "summary_verified": False, "status": "candidate"}
                count += 1
                if count >= MAX_PER_SOURCE:
                    break
        except (OSError, ET.ParseError, ValueError) as exc:
            errors.append(f'{source["name"]}: {type(exc).__name__}: {exc}')
    # Keep recent records, avoid unbounded repository growth.
    rows = sorted((v for v in found.values() if (date(v.get("published")) or CUTOFF) >= CUTOFF),
                  key=lambda x: x["published"], reverse=True)[:250]
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(rows)} candidates; source errors: {len(errors)}")
    for error in errors:
        print("WARNING", error)
    if errors and len(errors) == len(sources):
        raise SystemExit("All sources failed; existing candidates preserved")

if __name__ == "__main__":
    main()
