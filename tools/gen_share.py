#!/usr/bin/env python3
"""Generate per-article share pages (Facebook / X / messengers) for Watchfloor.

Social crawlers do not run JavaScript and never see the part of a URL after '#',
so every article gets a tiny static page with its own Open Graph tags:

    a/<id>.html      English  -> redirects to  /#/<id>            (or /#/analysis/<id>)
    a/hu-<id>.html   Hungarian -> redirects to /hu.html#/<id>     (or /hu.html#/analysis/<id>)

Usage (from the repo root, after index.html / hu.html were updated):
    python3 tools/gen_share.py

Needs: python3 + Pillow, node. Idempotent: only rewrites files whose content changed.
"""
import base64, html, io, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://watchfloor.info"
OGW, OGH = 1200, 630
DEFAULT_IMG = "og-default.jpg"


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def json_block(src, bid):
    m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % bid, src, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))


def load_items(src):
    """Evaluate the data part of the main script (AR..items) with node."""
    a = src.index("const AR=")
    b = src.index("\n];", src.index("const items=[")) + 3
    code = src[a:b] + "\nconsole.log(JSON.stringify({items,IMG,LOGO}));\n"
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "data.js")
        with open(p, "w", encoding="utf-8") as f:
            f.write(code)
        out = subprocess.run(["node", p], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def plain(s, limit=300):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(re.sub(r"\s+", " ", s)).strip()
    if len(s) > limit:
        s = s[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return s


def commons(fn, w=1200):
    from urllib.parse import quote
    q = quote(fn.replace(" ", "_"), safe="").replace("%28", "(").replace("%29", ")")
    return "https://commons.wikimedia.org/wiki/Special:FilePath/%s?width=%d" % (q, w)


def ensure_default_image():
    path = os.path.join(ROOT, "img", DEFAULT_IMG)
    if os.path.exists(path):
        return
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (OGW, OGH), "#1f2b25")
    d = ImageDraw.Draw(im)

    def font(sz):
        for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            if os.path.exists(f):
                return ImageFont.truetype(f, sz)
        return ImageFont.load_default()

    f1, f2 = font(190), font(40)
    w1 = d.textlength("Watch", font=f1)
    w2 = d.textlength("floor", font=f1)
    x = (OGW - w1 - w2) / 2
    d.text((x, 190), "Watch", font=f1, fill="#e6e9e1")
    d.text((x + w1, 190), "floor", font=f1, fill="#ff7a52")
    tag = "Defence and military news"
    d.text(((OGW - d.textlength(tag, font=f2)) / 2, 440), tag, font=f2, fill="#97a399")
    d.rectangle([0, OGH - 14, OGW, OGH], fill="#ff7a52")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "JPEG", quality=88)


def cover_file(aid, cover, ana_img):
    """Make img/<aid>.jpg (1200x630 crop of the cover) unless it already exists."""
    rel = "img/%s.jpg" % aid
    path = os.path.join(ROOT, rel)
    if os.path.exists(path):
        return rel
    data = ana_img.get(cover or "")
    if not data or "," not in data:
        return None
    from PIL import Image
    im = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[1]))).convert("RGB")
    r = max(OGW / im.width, OGH / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - OGW) // 2, (im.height - OGH) // 2
    im = im.crop((l, t, l + OGW, t + OGH))
    im.save(path, "JPEG", quality=86)
    return rel


PAGE = """<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} – Watchfloor</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Watchfloor">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">{imgsize}
<meta property="og:url" content="{url}"><meta property="og:locale" content="{locale}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{image}">
<link rel="canonical" href="{url}">
<script>location.replace("{target}")</script></head>
<body><p><a href="{target}">{title}</a></p></body></html>
"""


def write_if_changed(rel, text):
    path = os.path.join(ROOT, rel)
    if os.path.exists(path) and open(path, encoding="utf-8").read() == text:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def page(lang, aid, title, desc, image, local_img, route):
    pre = "hu-" if lang == "hu" else ""
    url = "%s/a/%s%s.html" % (SITE, pre, aid)
    base = SITE + ("/hu.html" if lang == "hu" else "/")
    target = base + "#/" + route
    esc = lambda s: html.escape(s, quote=True)
    size = '<meta property="og:image:width" content="%d"><meta property="og:image:height" content="%d">' % (OGW, OGH) if local_img else ""
    return pre + aid, PAGE.format(
        lang=lang, title=esc(title), desc=esc(desc), image=esc(image), imgsize=size, url=url,
        locale="hu_HU" if lang == "hu" else "en_GB", target=esc(target))


def main():
    src = read("index.html")
    news = {n["id"]: n for n in json_block(src, "news-data")}
    ana = json_block(src, "ana-data")
    ana_img = json_block(src, "ana-img")
    data = load_items(src)
    ensure_default_image()
    default_url = "%s/img/%s" % (SITE, DEFAULT_IMG)
    changed = total = 0

    for it in data["items"]:
        aid = it["id"]
        hu = news.get(aid, {}).get("hu")
        if aid in data["IMG"]:
            image, local = commons(data["IMG"][aid]), False
        elif it.get("img"):
            u = it["img"]
            image, local = (u.replace("width=640", "width=1200") if "Special:FilePath" in u else u), False
        else:
            image, local = default_url, True
        langs = [("en", it["t"], it["s"])]
        if hu:
            langs.append(("hu", hu[0], hu[1]))
        for lang, t, s in langs:
            name, text = page(lang, aid, plain(t, 200), plain(s), image, local, aid)
            changed += write_if_changed("a/%s.html" % name, text)
            total += 1

    for aid, a in ana.items():
        rel = cover_file(aid, a.get("cover"), ana_img)
        image, local = ("%s/%s" % (SITE, rel), True) if rel else (default_url, True)
        for lang in ("en", "hu"):
            x = a.get(lang) or a.get("en")
            name, text = page(lang, aid, plain(x["t"], 200), plain(x["s"]), image, local, "analysis/" + aid)
            changed += write_if_changed("a/%s.html" % name, text)
            total += 1

    print("share pages: %d total, %d written/updated" % (total, changed))


if __name__ == "__main__":
    sys.exit(main())
