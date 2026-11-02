#!/usr/bin/env python3
"""Source-grounded editorial and translation staging. No live site writes."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlencode
import re
import urllib.request
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "editorial_config.json").read_text())
ARCHIVE = ROOT / "editorial.json"

class Extract(HTMLParser):
    """Collect readable article paragraphs without losing text in nested inline tags."""
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.inside = False
        self.depth = 0
        self.buf = []
        self.parts = []
        self.jsonld = False
        self.jsonld_buf = []
        self.jsonld_bodies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.jsonld = True
            self.jsonld_buf = []
        if tag in ("script", "style", "nav", "footer", "header", "aside", "form"):
            self.skip += 1
        if tag == "p" and not self.skip:
            self.inside = True
            self.depth = 1
            self.buf = []
        elif self.inside and tag == "p":
            self.depth += 1

    def handle_data(self, value):
        if self.jsonld:
            self.jsonld_buf.append(value)
        if self.inside and not self.skip:
            self.buf.append(value)

    def handle_endtag(self, tag):
        if tag == "p" and self.inside:
            self.depth -= 1
            if self.depth == 0:
                s = " ".join(" ".join(self.buf).split())
                if 80 < len(s) < 2200:
                    self.parts.append(s)
                self.inside = False
        if tag == "script" and self.jsonld:
            try:
                self.jsonld_bodies.extend(self._bodies(json.loads("".join(self.jsonld_buf))))
            except (ValueError, TypeError):
                pass
            self.jsonld = False
        if tag in ("script", "style", "nav", "footer", "header", "aside", "form") and self.skip:
            self.skip -= 1

    @staticmethod
    def _bodies(data):
        pending = [data]
        result = []
        while pending:
            obj = pending.pop()
            if isinstance(obj, list):
                pending.extend(obj)
            elif isinstance(obj, dict):
                body = obj.get("articleBody")
                if isinstance(body, str) and len(body) >= 300:
                    result.append(body)
                pending.extend(v for v in obj.values() if isinstance(v, (list, dict)))
        return result


def evidence(url):
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname:
        return ""
    bot = "WatchFloorEditorialBot/1.0"
    robots = RobotFileParser()
    robots.set_url(p.scheme + "://" + p.netloc + "/robots.txt")
    try:
        robots.read()
        if not robots.can_fetch(bot, url):
            return ""
        request = urllib.request.Request(url, headers={"User-Agent": bot, "Accept": "text/html"})
        with urllib.request.urlopen(request, timeout=12) as response:
            if "html" not in response.headers.get("Content-Type", ""):
                return ""
            page = response.read(650000).decode("utf-8", "replace")
        parser = Extract()
        parser.feed(page)
        paragraphs = "\n".join(parser.parts[:40])[:11000]
        structured = max(parser.jsonld_bodies, key=len, default="")[:11000]
        # Structured articleBody is preferred when the HTML includes unrelated page paragraphs.
        return structured if len(structured) > len(paragraphs) else paragraphs
    except (OSError, ValueError, UnicodeError):
        return ""

def api(prompt):
    key=os.getenv("OPENAI_API_KEY","")
    if not key: raise RuntimeError("OPENAI_API_KEY not configured")
    body={"model":os.getenv("WATCHFLOOR_AI_MODEL","gpt-4.1-mini"),
          "messages":[{"role":"user","content":prompt}],
          "response_format":{"type":"json_object"},"temperature":0.1}
    request=urllib.request.Request("https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(request,timeout=60) as r: result=json.load(r)
    return json.loads(result["choices"][0]["message"]["content"])

def tokens(title):
    stop={"after","about","from","with","that","this","says","over","into","the"}
    return {x for x in re.findall(r"[a-z0-9]{4,}",title.lower()) if x not in stop}

def find_corrob_candidates(rows):
    """Best-effort, free GDELT discovery; discovered reports remain unverified."""
    known = {x["url"] for x in rows}
    expanded = list(rows)
    seen_seed_titles = set()
    for seed in rows[:8]:
        terms = list(tokens(seed["title"]))[:5]
        if len(terms) < 3:
            continue
        signature = tuple(sorted(terms))
        if signature in seen_seed_titles:
            continue
        seen_seed_titles.add(signature)
        query = " ".join(terms[:4])
        params = urlencode({"query": query, "mode": "artlist", "format": "json",
                            "maxrecords": 15, "timespan": "2d", "sort": "datedesc"})
        try:
            req = urllib.request.Request("https://api.gdeltproject.org/api/v2/doc/doc?" + params,
                                         headers={"User-Agent": "WatchFloorEditorialBot/1.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                result = json.load(response)
            added = 0
            for hit in result.get("articles", []):
                url = hit.get("url", "")
                p = urlsplit(url)
                title = hit.get("title", "")
                if (p.scheme != "https" or not p.hostname or p.username or p.password
                        or not isinstance(title, str) or not 25 <= len(title) <= 250
                        or url in known or p.hostname.lower() == urlsplit(seed["url"]).hostname.lower()):
                    continue
                # Search hits are candidates, never independent confirmation by themselves.
                expanded.append({"url": url, "title": title, "source": p.hostname,
                                 "published": hit.get("seendate", ""),
                                 "category": seed["category"], "status": "staging_unverified"})
                known.add(url)
                added += 1
                if added >= 4:
                    break
        except (OSError, ValueError, TypeError, KeyError) as ex:
            reason = getattr(ex, "reason", None)
            print("Corroboration lookup unavailable:", type(ex).__name__, str(reason or ex)[:180])
    print("Additional corroboration candidates:", len(expanded) - len(rows))
    return expanded


def group_items(rows):
    """Cheap semantic headline clustering; never treat same-topic stories as corroboration."""
    if len(rows) < 2:
        return
    # One low-cost request compares all headlines, rather than one request per story.
    headlines = [{"id": i, "title": x["title"], "category": x["category"],
                  "source": x["source"], "published": x["published"]}
                 for i, x in enumerate(rows)]
    try:
        answer = api(
            "Group ONLY headlines describing the exact same concrete news event. "
            "Different events in the same war, same weapon type, or same country are NOT matches. "
            "Require at least two different publishers and distinct source domains. "
            "Return JSON object with groups as arrays of integer ids. "
            "When uncertain, omit the pair. Headlines: " + json.dumps(headlines))
        proposed = answer.get("groups", [])
    except Exception as ex:
        print("Headline matching unavailable:", type(ex).__name__)
        proposed = []
    used = set()
    for ids in proposed if isinstance(proposed, list) else []:
        if not isinstance(ids, list) or len(ids) < 2:
            continue
        clean = []
        for i in ids:
            if type(i) is int and 0 <= i < len(rows) and i not in used and i not in clean:
                clean.append(i)
        if len(clean) < 2:
            continue
        domains = {urlsplit(rows[i]["url"]).hostname.lower().removeprefix("www.")
                   for i in clean if urlsplit(rows[i]["url"]).hostname}
        if len(domains) < 2 or len({rows[i]["source"] for i in clean}) < 2:
            continue
        used.update(clean)
        yield [rows[i] for i in clean]
    print("Matched cross-source event groups:", len(used), "headlines")

def valid(a):
    if not isinstance(a,dict): return False
    p=a.get("paragraphs")
    if not isinstance(p,list) or not 5<=len(p)<=12 or not all(isinstance(x,str) and len(x)>70 for x in p): return False
    return isinstance(a.get("title"),str) and isinstance(a.get("summary"),str) and 350<=len(" ".join(p).split())<=850

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("No API key: safely skipping editorial and translations"); return
    rows=json.loads((ROOT/"selected.json").read_text())
    # News only: Analysis is maintained manually and must never be regenerated.
    rows=[x for x in rows if str(x.get("section","News")).casefold()=="news" and str(x.get("status",""))=="staging_unverified"]
    archive=json.loads(ARCHIVE.read_text()) if ARCHIVE.exists() else {"items":[]}
    done={s["url"] for a in archive["items"] for s in a.get("sources",[])}
    count=0
    rows = find_corrob_candidates(rows)
    for group in group_items(rows):
        if count>=CFG["max_articles_per_run"]: break
        if any(x["url"] in done for x in group): continue
        # Publication requires independent corroboration from two source domains.
        # Skip single-source drafts before spending API credits.
        domains={urlsplit(x["url"]).hostname.lower().removeprefix("www.") for x in group if urlsplit(x["url"]).hostname}
        if len(group)<2 or len(domains)<2:
            print("Skipped single-source story (no AI charge)")
            continue
        sources=[{"publisher":x["source"],"url":x["url"],"headline":x["title"],"reference":evidence(x["url"])} for x in group]
        substantial = [s for s in sources if len(s["reference"]) >= CFG["min_source_article_characters"]]
        print("Evidence lengths:", [(s["publisher"], len(s["reference"])) for s in sources])
        if len(substantial) < 2:
            print("Skipped: fewer than two substantial source articles (no AI charge)"); continue
        prompt=("First verify all supplied articles describe the SAME specific event; if not return empty object. Produce original, factual English military reporting from ONLY the evidence. "
            "Never invent details, quotations or numbers. Attribute disputed battlefield claims. "
            "Do not copy source wording or structure. If facts are insufficient return empty object. "
            "Return JSON title, summary, paragraphs array; 450-700 words. Evidence: "+json.dumps(sources))
        try:
            article=api(prompt)
            if not valid(article):
                print("Rejected incomplete article"); continue
            urls=[s["url"] for s in sources]
            entry={"id":hashlib.sha256("|".join(sorted(urls)).encode()).hexdigest()[:20],
                "category":group[0]["category"],"title":article["title"],"summary":article["summary"],
                "paragraphs":article["paragraphs"],"published_at":dt.datetime.now(dt.timezone.utc).isoformat(),
                "sources":[{"publisher":s["publisher"],"url":s["url"]} for s in sources],
                "image":"","image_credit":"","ai_edited":True,"section":"News","status":"staging_review_required"}
            archive["items"].append(entry); done.update(urls); count+=1
        except Exception as ex:
            print("Article generation failed:",type(ex).__name__)
            break
    if count: ARCHIVE.write_text(json.dumps(archive,ensure_ascii=False,indent=2)+"\n")
    print("New staged English articles:",count)

if __name__=="__main__": main()
