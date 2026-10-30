#!/usr/bin/env python3
"""Collect candidate defence headlines without AI. Never publishes to the live site."""
import datetime as dt
import html
from html.parser import HTMLParser
from urllib.robotparser import RobotFileParser
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


class ArticleLinks(HTMLParser):
    """Extract dated article links and optional time elements from a public index."""
    def __init__(self, base):
        super().__init__()
        self.base = base
        self.items = []
        self.link = None
        self.in_time = False
        self.time_value = None

    def handle_starttag(self, tag, attrs):
        from urllib.parse import urljoin
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            url = canonical_url(urljoin(self.base, a["href"]))
            self.link = [url, []] if url else None
        if tag == "time":
            self.in_time = True
            self.time_value = a.get("datetime")

    def handle_data(self, data):
        if self.link:
            self.link[1].append(data)
        if self.in_time and not self.time_value:
            self.time_value = data.strip()

    def handle_endtag(self, tag):
        if tag == "a" and self.link:
            url, parts = self.link
            title = clean(" ".join(parts))
            if url and len(title) >= 24 and len(title) <= 220:
                self.items.append((title, url, None, ""))
            self.link = None
        if tag == "time":
            self.in_time = False


def html_fallback(source):
    """Best-effort HTML discovery; undated links remain unpublishable candidates."""
    from urllib.parse import urlsplit
    url = source.get("html_url")
    if not url:
        return []
    agent = "WatchFloorFeedCollector/0.2"
    parsed = urlsplit(url)
    robots_url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"
    robots = RobotFileParser()
    robots.set_url(robots_url)
    try:
        robots.read()
    except (OSError, ValueError):
        raise ValueError("Cannot verify robots.txt; HTML fallback disabled")
    if not robots.can_fetch(agent, url):
        raise ValueError("robots.txt disallows HTML fallback")
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=20) as response:
        page = response.read(2_000_000).decode("utf-8", errors="replace")
    parser = ArticleLinks(url)
    parser.feed(page)
    host = parsed.hostname
    seen = set()
    rows = []
    for title, link, published, summary in parser.items:
        target = urlsplit(link)
        if target.hostname != host or link == url or link in seen:
            continue
        if not re.search(r"/(?:news|article|analysis|commentary|daily-news|\d{4}/\d{2})[/-]", target.path, re.I):
            continue
        seen.add(link)
        rows.append((html.unescape(title), link, published, summary))
    print("HTML DISCOVERY", source["name"], "links:", len(rows), "(undated; not auto-published)")
    return rows[:MAX_PER_SOURCE]

def main():
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["sources"]
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    found = {x["id"]: x for x in old if x.get("id")}
    errors = []
    for source in sources:
        try:
            entries = None
            failures = []
            for feed_url in source.get("urls", [source.get("url")]):
                try:
                    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (compatible; WatchFloorFeedCollector/0.2)"})
                    with urllib.request.urlopen(req, timeout=20) as response:
                        content = response.read(2_000_000)
                    entries = list(parse(content))
                    if not entries:
                        raise ValueError("Feed contains no entries")
                    print("SOURCE OK", source["name"], feed_url, "entries:", len(entries))
                    break
                except (OSError, ET.ParseError, ValueError) as exc:
                    failures.append(f"{feed_url}: {type(exc).__name__}: {exc}")
            if entries is None and source.get("html_url"):
                try:
                    entries = html_fallback(source)
                    if not entries:
                        raise ValueError("No matching article links found")
                except (OSError, ValueError) as exc:
                    failures.append(f"HTML: {type(exc).__name__}: {exc}")
            if entries is None:
                raise ValueError("; ".join(failures))
            count = 0
            for title, url, published, summary in entries:
                when = date(published)
                title, url = clean(title), canonical_url(url or "")
                if not (title and url and when and CUTOFF <= when <= NOW + dt.timedelta(hours=1)):
                    continue
                key = hashlib.sha256(url.encode()).hexdigest()[:20]
                found[key] = {"id": key, "title": title, "url": url,
                              "source": source["name"], "published": when.isoformat(),
                              "summary": clean(summary)[:500], "category": classify(title, clean(summary)),
                              "summary_verified": False, "status": "candidate"}
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
