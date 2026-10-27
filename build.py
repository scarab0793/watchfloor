#!/usr/bin/env python3
"""Build the multilingual Watchfloor page.
usage: build.py ENGLISH_PAGE.html [OUT.html]
Takes the English page's data lines (sources, categories, LOGO, IMG, items) and
injects them, plus i18n/ui.json and i18n/<lang>.json (id -> {t,s,p}), into template.html."""
import json,re,sys,os
d=os.path.dirname(os.path.abspath(__file__))
en=open(sys.argv[1],encoding='utf8').read()
out=sys.argv[2] if len(sys.argv)>2 else os.path.join(d,'multi.html')
head=[]
for pat in (r'const AR=.*\n',r'const cats=.*\n',r'const LOGO=.*\n',r'const IMG=.*\n'):
    m=re.search(pat,en); assert m,pat; head.append(m.group(0))
m=re.search(r'const items=\[[\s\S]*?\n\];',en); assert m
tpl=open(os.path.join(d,'template.html'),encoding='utf8').read()
ui=json.load(open(os.path.join(d,'i18n','ui.json'),encoding='utf8'))
tr={}
for k in ui:
    if k=='en': continue
    f=os.path.join(d,'i18n',k+'.json')
    tr[k]=json.load(open(f,encoding='utf8')) if os.path.exists(f) else {}
i18n='const UI='+json.dumps(ui,ensure_ascii=False)+';\nconst TR='+json.dumps(tr,ensure_ascii=False,separators=(',',':'))+';'
html=tpl.replace('/*@@HEAD@@*/\n',''.join(head)).replace('/*@@ITEMS@@*/',m.group(0)).replace('/*@@I18N@@*/',i18n)
open(out,'w',encoding='utf8').write(html)
print(out,len(html))
