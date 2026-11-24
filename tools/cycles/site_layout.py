"""
site_layout.py - ONE shared header (logo + page title + nav) for every SAlgo
US website page, so all pages always look the same and link to each other.

Used by: CreateWebPage2.py (Screener), run_stock_analysis.py (Stock Analysis),
build_strategy1.py ... build_strategy4.py, build_shortlisted.py (Preferred Stocks),
record_monthly_picks.py (Performance)
and generateStockCharts.py (per-stock dashboards, one folder deeper -> base="../").

Usage inside a generator:
    from site_layout import site_header_css, site_header_html
    ... <style>{site_header_css()} ...page css...</style> ...
    <body>{site_header_html("strategy1.html", "Strategy 1", "Top 10 by Score TTM")}

Rule: the website never links to or contains .xlsx / raw data files.
"""
import html as _html

# (file, label) - order = order in the nav bar
NAV_ITEMS = [
    ("index.html", "Screener"),
    ("StockAnalysis.html", "Stock Analysis"),
    ("strategy1.html", "Strategy 1"),
    ("strategy2.html", "Strategy 2"),
    ("strategy3.html", "Strategy 3"),
    ("strategy4.html", "Strategy 4"),
    ("shortlisted.html", "Preferred Stocks"),
    ("performance.html", "Performance"),
    ("updates.html", "Updates"),
    ("cycles/index.html", "Cycles"),
]
LOGO_FILE = "LOGO.jpeg"

# Menu groups: one entry in the nav bar that opens a drop-down with these pages
# (in NAV_ITEMS order). The group sits where its first page is in NAV_ITEMS.
NAV_GROUPS = [
    ("Strategies", ["strategy1.html", "strategy2.html", "strategy3.html", "strategy4.html", "shortlisted.html"]),
]

# Drop-down CSS lives INSIDE the nav markup, so fix_nav.py brings it to every existing
# page (incl. the 1,200+ dashboards) without rebuilding them. Same colours as the header.
_DD_CSS = (
    "<style>"
    ".sa-dd{position:relative;display:inline-block}"
    ".sa-ddbtn{font:inherit;font-size:1.02rem;font-weight:500;color:#1f2937;background:none;border:0;cursor:pointer;"
    "padding:8px 14px;border-radius:8px;white-space:nowrap;font-family:'Segoe UI','Inter',system-ui,-apple-system,sans-serif}"
    ".sa-ddbtn:after{content:'';display:inline-block;margin-left:7px;vertical-align:3px;border:4px solid transparent;border-top-color:currentColor;border-bottom:0}"
    ".sa-dd:hover .sa-ddbtn,.sa-ddbtn:focus-visible{color:#a8650a;background:#f6ecdc}"
    ".sa-ddbtn.sa-active{color:#a8650a;font-weight:600}"
    ".sa-ddmenu{display:none;position:absolute;left:0;top:100%;z-index:1000;min-width:200px;padding:6px;margin-top:2px;"
    "background:#fdf8f1;border:1px solid #efe4d2;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.12)}"
    ".sa-dd:hover .sa-ddmenu,.sa-dd:focus-within .sa-ddmenu,.sa-dd.open .sa-ddmenu{display:block}"
    ".sa-dd:before{content:'';position:absolute;left:0;right:0;top:100%;height:6px}"
    ".sa-nav .sa-ddmenu a{display:block;margin:1px 0}"
    "@media (max-width:760px){.sa-ddmenu{position:fixed;left:12px;right:12px;top:auto}}"
    "</style>"
)


def nav_html(active_file=None, base=""):
    """The whole <nav> block. Used by site_header_html() and by fix_nav.py, so new pages
    and already-built pages always get the same menu."""
    active_attr = ' class="sa-active" aria-current="page"'
    group_of = {f: name for name, files in NAV_GROUPS for f in files}
    labels = dict(NAV_ITEMS)
    out, done = [], set()
    for f, label in NAV_ITEMS:
        g = group_of.get(f)
        if g is None:
            out.append(f'<a href="{base}{f}"{active_attr if f == active_file else ""}>{label}</a>')
            continue
        if g in done:
            continue
        done.add(g)
        files = [x for x, _ in NAV_ITEMS if group_of.get(x) == g]
        on = active_file in files
        items = "".join(f'<a href="{base}{x}"{active_attr if x == active_file else ""}>{labels[x]}</a>' for x in files)
        out.append(f'<div class="sa-dd"><button type="button" class="sa-ddbtn{" sa-active" if on else ""}" aria-haspopup="true" '
                   f'onclick="this.parentNode.classList.toggle(\'open\')">{g}</button><div class="sa-ddmenu">{items}</div></div>')
    return f'<nav class="sa-nav" aria-label="SAlgo pages">{_DD_CSS}{"".join(out)}</nav>'


def site_header_css():
    """CSS for the shared header. All classes are prefixed 'sa-' so they never
    clash with a page's own styles. Plain string (not an f-string template),
    safe to drop into a generator's f-string via {site_header_css()}."""
    return """
/* ---- SAlgo shared header (site_layout.py) ---- */
.sa-header{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;
  background:#fdf8f1;border:1px solid #efe4d2;border-radius:12px;padding:10px 24px;margin:0 0 20px 0;
  font-family:'Segoe UI','Inter',system-ui,-apple-system,sans-serif;box-sizing:border-box}
.sa-brand{display:flex;align-items:center;gap:14px;min-width:0;text-decoration:none}
.sa-logo{height:56px;width:56px;object-fit:contain;border-radius:8px;background:#fff;flex:0 0 auto}
.sa-title{display:flex;flex-direction:column;min-width:0}
.sa-title h1{margin:0;font-size:1.3rem;font-weight:700;color:#1f5f2a;line-height:1.2}
.sa-title p{margin:2px 0 0 0;font-size:.85rem;color:#6b7280}
.sa-nav{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.sa-nav a{color:#1f2937;text-decoration:none;font-size:1.02rem;font-weight:500;padding:8px 14px;
  border-radius:8px;white-space:nowrap;transition:color .15s,background .15s}
.sa-nav a:hover{color:#a8650a;background:#f6ecdc}
.sa-nav a.sa-active{color:#a8650a;font-weight:600}
@media (max-width:760px){
  .sa-header{padding:10px 14px}
  .sa-nav{width:100%;overflow-x:auto;flex-wrap:nowrap}
  .sa-nav a{padding:6px 10px;font-size:.95rem}
  .sa-logo{height:44px;width:44px}
}
"""


def site_header_html(active_file, title, subtitle="", base="", extra_html=""):
    """Header markup. active_file = this page's file name from NAV_ITEMS
    (or None for pages not in the nav, e.g. dashboards). base = relative path
    back to the US_Stocks folder ("" for top-level pages, "../" for
    html_dashboards). extra_html = optional widget shown on the right."""
    sub = f"<p>{_html.escape(subtitle)}</p>" if subtitle else ""
    return f"""
<header class="sa-header">
  <a class="sa-brand" href="{base}index.html">
    <img class="sa-logo" src="{base}{LOGO_FILE}" alt="SAlgo logo">
    <div class="sa-title"><h1>{_html.escape(title)}</h1>{sub}</div>
  </a>
  {nav_html(active_file, base)}{extra_html}
</header>
"""


# ---------------------------------------------------------------------------
# Shared column-name rules (so every page names things the same way)
# ---------------------------------------------------------------------------
import re as _re

_GF_RE = _re.compile(r"\bGF(?=[\s+_(\-A-Z]|$)")   # GF Score, GF+FCF, Price-to-GF-Value, GFValue
_SALMAN_RE = _re.compile(r"^(STORY\s+)?Salman\s+Score(\s+\d+)?$", _re.I)


def display_name(name):
    """Name shown on web pages: third-party vendor prefix 'GF' -> 'ThirdParty'
    (GF Score -> ThirdParty Score, GF+FCF -> ThirdParty+FCF)."""
    return _GF_RE.sub("ThirdParty", str(name))


def canon_salman(name):
    """'Salman Score 11/13/14/15' (and the STORY twin) are ONE KPI -> 'Salman Score'
    / 'STORY Salman Score'. Any other name is returned unchanged."""
    if not isinstance(name, str):
        return name
    m = _SALMAN_RE.match(_re.sub(r"\s+", " ", name).strip())
    if not m:
        return name
    return "STORY Salman Score" if m.group(1) else "Salman Score"


def is_story_col(name):
    """STORY ... columns are never shown on web pages."""
    return _re.sub(r"\s+", " ", str(name)).strip().upper().startswith("STORY")
