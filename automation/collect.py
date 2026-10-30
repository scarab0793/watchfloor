#!/usr/bin/env python3
"""Collect candidate defence headlines without AI. Never publishes to the live site."""
import datetime as dt
import email.utils
import hashlib
import json
import pathlib
import re
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
                title, url = clean(title), (url or "").strip()
                if not (title and url.startswith(("https://", "http://")) and when and CUTOFF <= when <= NOW + dt.timedelta(hours=1)):
                    continue
                key = hashlib.sha256(url.split("#")[0].encode()).hexdigest()[:20]
                found[key] = {"id": key, "title": title, "url": url,
                              "source": source["name"], "published": when.isoformat(),
                              "summary": clean(summary)[:500], "status": "candidate"}
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
