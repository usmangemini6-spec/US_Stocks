import os, sys
sys.path.insert(0, os.path.dirname(os.getcwd()))           # scripts folder: site_layout.py
from site_layout import site_header_css, site_header_html
import json, re, html
H=open('pagehead3.html').read(); head=H[:H.rindex('</head>')].replace('</head>','')
head=head[:head.index('<body>')]+head[head.index('<body>')+6:] if '<body>' in head else head
head=head[:head.index('<header')] if '<header' in head else head
head=re.sub(r'<title>.*?</title>','<title>{TITLE}</title>',head)
extra='''<style>'''+site_header_css()+'''\n.sitehdr{margin:-8px 0 0}.sitehdr .sa-header{margin:0}
.sa-top{background:#0b0b0b;color:#fff;padding:10px max(5vw,16px);display:flex;flex-wrap:wrap;gap:6px 18px;align-items:center;font-size:14px}
.sa-top b{font:700 16px "Inter Tight",Inter;margin-right:10px}.sa-top span{opacity:.7}.sa-top a{color:#fff;text-decoration:none}.sa-top .on{opacity:1;border-bottom:2px solid #eb6834;padding-bottom:2px}
.sub{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.sub a{display:inline-flex;align-items:center;min-height:40px;padding:0 14px;border:1px solid var(--line);border-radius:999px;color:var(--ink);text-decoration:none;background:var(--bg);font-size:14px}
.sub a[aria-current]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-top:18px}
.card{display:block;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:16px;color:var(--ink);text-decoration:none}
.card b{font:600 19px/1.2 "Inter Tight",Inter;display:block}.card p{margin:6px 0 0;font-size:14px;color:var(--mut)}.card .badge{margin-top:10px}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:14px}.facts div{background:var(--bg);border-radius:8px;padding:12px 14px}.facts b{display:block;font:600 22px/1.1 "Inter Tight",Inter,sans-serif;font-variant-numeric:tabular-nums}.facts span{font-size:13px;color:var(--mut)}
.pend{border:1px dashed var(--line);border-radius:10px;padding:18px;color:var(--mut);margin-top:14px}
ul.tight{margin:6px 0 0;padding-left:20px}ul.tight li{margin:4px 0}

/* ---- SAlgo website colours (same as Screener / Strategy / Performance pages) ---- */
:root,:root[data-theme=dark],:root[data-theme=light]{color-scheme:light;--bg:#ffffff;--panel:#faf6ef;--ink:#1f2937;--mut:#6b7280;--line:#e7dcc8;
 --s1:#1f5f2a;--s2:#a8650a;--s3:#0b5fa5;--red:#dc2626;--good:#15803d;--warn:#a8650a}
body{background:#faf6ef;color:#1f2937;font:15px/1.55 'Segoe UI','Inter',system-ui,-apple-system,sans-serif}
h1,h2,h3,.card b,.facts b{font-family:'Segoe UI','Inter',system-ui,sans-serif}
h1,h2{color:#1f5f2a}h3{color:#1f2937}
.band{background:#faf6ef}.band.top{background:#faf6ef;padding-bottom:18px}
.band>.wrap{background:#fff;border:1px solid #e7dcc8;border-radius:12px;padding:20px 24px;box-shadow:0 2px 8px rgba(0,0,0,.04);max-width:1280px;margin-inline:auto;box-sizing:border-box}
.band.top>.wrap{background:transparent;border:0;box-shadow:none;padding:0}
.band{padding-top:10px;padding-bottom:10px}
.facts div{background:#fff;border:1px solid #e7dcc8;border-radius:10px}
.sub a{border:1px solid #e7dcc8;border-radius:8px;background:#fff;color:#1f2937;font-weight:600}
.sub a:hover{background:#f6ecdc;color:#a8650a}
.sub a[aria-current]{background:#f6ecdc;color:#a8650a;border-color:#a8650a}
.card{border-color:#e7dcc8;border-radius:12px}.card:hover{border-color:#a8650a;background:#fdf8f1}
/* tables: bordered columns like the rest of the site, numbers right-aligned in equal-width digits */
.scroll{overflow-x:auto}
table{font-size:14px;border:1px solid #e7dcc8}
th,td{border:1px solid #e7dcc8;padding:7px 10px;vertical-align:middle}
th{background:#f6ecdc;color:#1f2937;font-size:13px;font-weight:600;white-space:nowrap}
tbody tr:nth-child(even) td{background:#fdfaf5}
tbody tr:hover td{background:#fdf3e3}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td{font-variant-numeric:tabular-nums}
td a{color:#0b5fa5;font-weight:600;text-decoration:none}td a:hover{text-decoration:underline}
.fig{background:#fff}
</style></head><body>'''
OUTDIR=os.environ.get("CYCLES_OUT") or os.path.join(os.path.dirname(os.getcwd()),"website","US_Stocks","cycles")   # GitHub workflow sets CYCLES_OUT
os.makedirs(OUTDIR,exist_ok=True)
SUBS=[("index.html","Overview"),("us-stocks.html","US stocks"),("ai-bubble.html","AI bubble"),("gold.html","Gold & miners"),("silver.html","Silver"),("tasi.html","Saudi TASI"),("psx.html","Pakistan KSE-100"),("oil.html","Oil"),("real-estate.html","Real estate"),("rates.html","Rates & inflation")]
def top(cur):
    return ('<div class="sitehdr">'+site_header_html("cycles/index.html","Cycles","Market cycles, forecasts and outlook",base="../")+'</div>'
            +'<nav class="sub" aria-label="Cycles pages">'+''.join(f'<a href="{f}"{" aria-current=page" if f==cur else ""}>{l}</a>' for f,l in SUBS)+'</nav>')
D=json.load(open('work/data4.json')); JS=open('tail4.js').read()
def page(fname,title,header_html,body_html,keys):
    d={k:D[k] for k in keys}
    s=head.replace('{TITLE}',title)+extra+f'<header class="band top"><div class="wrap">{top(fname)}{header_html}</div></header>'+body_html
    if keys: s+=f'<script>window.KEYS={json.dumps(keys)};const D={json.dumps(d)};\n'+JS+'</script>'
    s+='<section class="band mk"><div class="wrap"><p class="small">Cycle views and comments are historical patterns and public information, not financial advice. Data: Yahoo Finance, US Federal Reserve (FRED) and other public sources, month-end prices; built '+__import__('datetime').datetime.now().strftime('%d %b %Y')+'.</p></div></section><script>'+open('numcols.js',encoding='utf-8').read()+'</script></body></html>'
    open(os.path.join(OUTDIR,fname),'w',encoding='utf-8').write(s)
_page=page
def page(fname,title,header_html,body_html,keys):
    if '<main id="main"></main>' in body_html:
        body_html=body_html.replace('<main id="main"></main>', CSS+HOWTO+''.join(section(k) for k in keys))
    _page(fname,title,header_html,body_html,[])
exec(open('pages.py',encoding='utf-8').read())
