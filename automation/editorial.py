#!/usr/bin/env python3
"""Source-grounded editorial and translation staging. No live site writes."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import re
import urllib.request
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "editorial_config.json").read_text())
ARCHIVE = ROOT / "editorial.json"

class Extract(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip=0; self.inside=False; self.buf=[]; self.parts=[]
    def handle_starttag(self,t,a):
        if t in ("script","style","nav","footer","header","aside","form"): self.skip+=1
        if t=="p" and not self.skip: self.inside=True; self.buf=[]
    def handle_data(self,v):
        if self.inside and not self.skip: self.buf.append(v)
    def handle_endtag(self,t):
        if t=="p" and self.inside:
            s=" ".join("".join(self.buf).split())
            if 80<len(s)<2200: self.parts.append(s)
            self.inside=False
        if t in ("script","style","nav","footer","header","aside","form") and self.skip: self.skip-=1

def evidence(url):
    p=urlsplit(url)
    if p.scheme!="https" or not p.hostname: return ""
    bot="WatchFloorEditorialBot/1.0"
    robots=RobotFileParser(); robots.set_url(p.scheme+"://"+p.netloc+"/robots.txt")
    try:
        robots.read()
        if not robots.can_fetch(bot,url): return ""
        request=urllib.request.Request(url,headers={"User-Agent":bot,"Accept":"text/html"})
        with urllib.request.urlopen(request,timeout=12) as r:
            if "html" not in r.headers.get("Content-Type",""): return ""
            page=r.read(650000).decode("utf-8","replace")
        parser=Extract(); parser.feed(page)
        return "\n".join(parser.parts[:25])[:11000]
    except (OSError,ValueError,UnicodeError): return ""

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

def group_items(rows):
    used=set()
    for i,a in enumerate(rows):
        if i in used: continue
        used.add(i); group=[a]; ta=tokens(a["title"])
        for j,b in enumerate(rows):
            if j in used or b["source"]==a["source"]: continue
            tb=tokens(b["title"])
            if ta and tb and len(ta&tb)>=4 and len(ta&tb)/min(len(ta),len(tb))>=.65:
                group.append(b); used.add(j)
        yield group

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
        if sum(len(s["reference"]) >= CFG["min_source_article_characters"] for s in sources) < 2:
            print("Skipped: fewer than two substantial source articles (no AI charge)"); continue
        prompt=("Produce original, factual English military reporting from ONLY the evidence. "
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
