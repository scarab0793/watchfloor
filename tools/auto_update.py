#!/usr/bin/env python3
"""Watchfloor self-update (English only): RSS -> article text -> Anthropic API (write item) -> index.html.

Env: ANTHROPIC_API_KEY (required), ANTHROPIC_MODEL (default claude-sonnet-5-5), MAX_NEW (default 8), DRY_RUN=1.
Only stdlib; no image handling (pictures are added manually). Afterwards run tools/gen_share.py.
"""
import html, json, os, re, sys, time, datetime, urllib.request, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_NEW = int(os.environ.get("MAX_NEW", "8"))
MAX_AGE_H = int(os.environ.get("MAX_AGE_H", "30"))
UA = {"User-Agent": "Mozilla/5.0 (compatible; WatchfloorBot/1.0)"}

# name, feed url, default status label
FEEDS = [
    ("The Defense Post", "https://thedefensepost.com/feed/", "Reported"),
    ("The War Zone", "https://www.twz.com/feed", "Reported"),
    ("Naval Today", "https://www.navaltoday.com/feed/", "Reported"),
    ("Naval News", "https://www.navalnews.com/feed/", "Reported"),
    ("Defence Industry Europe", "https://defence-industry.eu/feed/", "Reported"),
    ("Militarnyi", "https://militarnyi.com/en/feed/", "Reported"),
    ("Army Recognition", "https://www.armyrecognition.com/rss", "Reported"),
    ("Calibre Defence", "https://www.calibredefence.co.uk/feed/", "Company claim"),
    ("TASS", "https://tass.com/rss/v2.xml", "Official claim"),
]
SKIP_WORDS = re.compile(r"\b(stock|shares|ETF|short interest|sponsored|podcast)\b", re.I)

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()

def node_eval(src):
    import subprocess, tempfile
    a = src.index("const AR=")
    b = src.index("\n];", src.index("const items=[")) + 3
    code = src[a:b] + "\nconsole.log(JSON.stringify({items,IMG,LOGO}));\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "d.js"); open(p, "w", encoding="utf-8").write(code)
        out = subprocess.run(["node", p], capture_output=True, text=True, check=True).stdout
    return json.loads(out)

def block(src, bid):
    m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % bid, src, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))

def feed_entries():
    out = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for name, url, st in FEEDS:
        try:
            root = ET.fromstring(get(url))
        except Exception as e:
            print("feed failed", name, e); continue
        for it in root.iter("item"):
            link = (it.findtext("link") or "").strip()
            title = html.unescape((it.findtext("title") or "").strip())
            pd = it.findtext("pubDate")
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pd)
                if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
                if (now - dt).total_seconds() > MAX_AGE_H * 3600: continue
            except Exception:
                continue
            if link and title and not SKIP_WORDS.search(title):
                out.append(dict(source=name, url=link, title=title, st=st, dt=dt))
    out.sort(key=lambda e: e["dt"], reverse=True)
    return out

def article_text(url):
    h = get(url)
    h = re.sub(r"(?is)<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", h)
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", h)
    txt = "\n".join(html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in paras)
    return re.sub(r"\n{2,}", "\n", txt)[:7000]

PROMPT = """You write items for Watchfloor, an English-language military and defence news site.
Today is {today}. Source: {source} ({url}). Default verification label: {st}.
Article headline: {title}
Article text (may be partial):
{text}

Rules: write ONLY from facts in the article text above, in your own words (no copying), accurate numbers/dates/names. Two or three paragraphs. State caveats; claims by a party to a war, state media or companies must be attributed and labelled. No promotional wording. Never mention AI. If the text is too thin, paywalled, a duplicate-looking opinion piece, not defence/military news, or you cannot write it reliably, return {{"skip":true}}.
Choose exactly one region key: "r" in {regions} OR (for war coverage) "w" in {wars}. Choose "c" (topic) from {cats}. Choose "st" from {sts}.
Return ONLY a JSON object:
{{"r"|"w":..., "c":..., "st":..., "t":headline, "s":one-sentence summary, "p":[paragraphs], "cav":short caveat (not displayed),
}}"""

def call_model(prompt):
    body = json.dumps({"model": MODEL, "max_tokens": 3000, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        d = json.loads(r.read())
    return "".join(b.get("text", "") for b in d["content"] if b["type"] == "text")

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:48].strip("-")

def validate(d, cats, sts, regions, wars):
    if d.get("skip"): return "skip"
    if bool(d.get("r")) == bool(d.get("w")): return "need exactly one of r/w"
    if d.get("r") and d["r"] not in regions: return "bad region"
    if d.get("w") and d["w"] not in wars: return "bad war"
    if d.get("c") not in cats: return "bad category " + str(d.get("c"))
    if d.get("st") not in sts: return "bad status"
    if not (isinstance(d.get("p"), list) and 2 <= len(d["p"]) <= 3): return "paragraph count"
    for k in ("t", "s", "cav"):
        if not isinstance(d.get(k), str) or not d[k].strip(): return "missing " + k
    if re.search(r"\b(AI-generated|generated by AI)\b", json.dumps(d), re.I): return "AI mention"
    return None

def apply(src, item_json_list):
    return src.replace("const items=[", "const items=[" + ",".join(item_json_list) + ",", 1)

def main():
    src = read("index.html")
    data = node_eval(src); items = data["items"]
    ui = block(src, "ui-data")
    cats, sts = set(ui["en"]["cat"]), set(ui["en"]["st"])
    regions, wars = set(ui["en"]["reg"]), set(ui["en"]["war"])
    known_urls = {s[1].rstrip("/") for x in items for s in x["src"]}
    known_ids = {x["id"] for x in items}
    known_titles = {slug(x["t"]) for x in items}
    today = datetime.date.today()
    new_items, done = [], 0
    for e in feed_entries():
        if done >= MAX_NEW: break
        if e["url"].rstrip("/") in known_urls or slug(e["title"]) in known_titles: continue
        try:
            text = article_text(e["url"])
        except Exception as ex:
            print("fetch failed", e["url"], ex); continue
        if len(text) < 600: print("too short", e["url"]); continue
        prompt = PROMPT.format(today=today.strftime("%d %B %Y"), source=e["source"], url=e["url"], st=e["st"],
            title=e["title"], text=text, regions=sorted(regions), wars=sorted(wars), cats=sorted(cats), sts=sorted(sts))
        try:
            raw = call_model(prompt)
            d = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except Exception as ex:
            print("model failed", e["url"], ex); continue
        err = validate(d, cats, sts, regions, wars)
        if err: print("rejected", e["url"], err); continue
        tm = e["dt"].strftime("%d %b").lstrip("0")
        reg = (d.get("r") or d.get("w") or "x")[:2].lower()
        iid = "%s-%s-%s" % (reg, slug(d["t"])[:40].strip("-"), tm.lower().replace(" ", ""))
        n = 2
        while iid in known_ids: iid = "%s-%d" % (iid.rsplit("-", 1)[0], n); n += 1
        known_ids.add(iid); known_urls.add(e["url"].rstrip("/"))
        it = {"id": iid, "c": d["c"], "st": d["st"], "time": tm, "t": d["t"], "s": d["s"], "p": d["p"], "cav": d["cav"],
              "src": [[e["source"], e["url"]]]}
        it["r" if d.get("r") else "w"] = d.get("r") or d.get("w")
        new_items.append(json.dumps(it, ensure_ascii=False, separators=(",", ":")))
        done += 1; print("added", iid); time.sleep(1)
    if not new_items:
        print("nothing new"); return 0
    # newest first: items were collected newest-first, keep that order
    if os.environ.get("DRY_RUN"): print("dry run, %d items" % len(new_items)); return 0
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(apply(read("index.html"), new_items))
    print("updated index.html with %d items" % len(new_items))
    return 0

if __name__ == "__main__":
    sys.exit(main())
