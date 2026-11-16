"""
update_prices.py - run every weekday by the GitHub workflow (.github/workflows/daily_prices.yml).
Nothing on the PC runs it; the website pages make no lookups themselves.

What it does
1. Reads the recorded runs (DB) from performance.html.
2. Finds every stock that still needs a price:
     - open month (not ended yet): every stock, for its running return;
     - ended month that is not CLOSED yet: stocks missing a start or an end price.
3. Downloads daily closes for those stocks from their start date: Yahoo first, Stooq if Yahoo fails.
   The whole history is rebuilt on every run, so a missed day fills itself in the next day.
4. Writes the closes into performance.html (block /*PX_START*/ ... /*PX_END*/); the page uses them to
   show each stock's latest close and % gain, and to close an ended month at its month-end close.
5. Rebuilds the All-time performance table in alltime-performance.html
   (block <!--ALLTIME_START--> ... <!--ALLTIME_END-->) with the same live figures.

record_monthly_picks.py (monthly pipeline) imports alltime_card() from here, so both pages always
use one set of rules. The monthly run's own closing (StrategyPerformance.xlsx) stays the official record.

Exit codes: 0 = ok / nothing to do, 1 = too many tickers failed (pages left unchanged).
"""
import os
import re
import sys
import json
import time
import io
import csv
import urllib.request
from datetime import datetime, timedelta, date

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.normpath(os.path.join(HERE, "..", "performance.html"))
ALLTIME = os.path.normpath(os.path.join(HERE, "..", "alltime-performance.html"))
PX_BLOCK = re.compile(r"/\*PX_START\*/window\.PX=(.*?);/\*PX_END\*/", re.S)
AT_BLOCK = re.compile(r"<!--ALLTIME_START-->.*?<!--ALLTIME_END-->", re.S)
STRATS = ("S1", "S2", "S3", "S4")


# ---------------------------------------------------------------- reading the page
def read_db(html):
    m = re.search(r"const DB = (\{.*\});\n", html)
    return json.loads(m.group(1)) if m else {"months": [], "data": {}}


def read_px(html):
    m = PX_BLOCK.search(html)
    try:
        return json.loads(m.group(1)) if m else {}
    except Exception:
        return {}


def num(v):
    try:
        f = float(str(v).replace(",", "").replace("$", ""))
        return f if f > 0 else None
    except Exception:
        return None


def month_end(month):
    return month[:7] + "-31"          # string compare: every YYYY-MM-DD of that month is <= this


# ---------------------------------------------------------------- live figures (same rules as the page JS)
def close_on(px, ticker, frm, to):
    """Latest close of ticker with frm <= date <= to."""
    h = (px or {}).get(ticker) or {}
    best = None
    for d, p in h.items():
        if frm <= d <= to and p and p > 0 and (best is None or d > best):
            best = d
    return (best, h[best]) if best else None


def live_pack(run_key, pack, px, cur_month):
    """Returns (rows_with_returns, avg, winners, losers, status).
    status: CLOSED (recorded by the monthly run), CLOSED (daily prices), ENDED - prices pending, OPEN."""
    s = pack.get("summary") or {}
    month = run_key[:7]
    rows = [dict(r) for r in pack.get("rows", [])]
    if s.get("Status") == "CLOSED":                       # closed by the monthly run: use its figures as recorded
        try:
            avg = float(s.get("AvgReturnPct"))
        except Exception:
            avg = None
        return rows, avg, s.get("Winners"), s.get("Losers"), "CLOSED"
    ended = month < cur_month
    to = month_end(month) if ended else "9999-12-31"
    missing = 0
    for r in rows:
        t, sd = r.get("Ticker"), str(r.get("StartDate") or "")
        sp = num(r.get("StartPrice"))
        if sp is None and t and sd:                       # start price missing: close on the start day
            c = close_on(px, t, sd, sd)
            if c:
                sp = round(c[1], 2)
                r["StartPrice"] = sp
        ep = num(r.get("EndPrice"))
        if t and sd and (ep is None or not ended):        # open month: always the latest close
            c = close_on(px, t, sd, to)
            if c:
                ep = round(c[1], 2)
                r["EndPrice"], r["EndDate"] = ep, c[0]
        if sp and ep:
            r["ReturnPct"] = round((ep / sp - 1) * 100, 2)
        else:
            missing += 1
    rets = [r["ReturnPct"] for r in rows if isinstance(r.get("ReturnPct"), (int, float))]
    avg = (sum(rets) / len(rets)) if rets else None
    if ended:
        status = "CLOSED (daily prices)" if rows and not missing else "ENDED - prices pending"
    else:
        status = "OPEN"
    return rows, avg, sum(1 for x in rets if x > 0), sum(1 for x in rets if x <= 0), status


def cur_month_of(px):
    asof = (px or {}).get("asof") or ""
    return max(asof[:7], date.today().strftime("%Y-%m")) if asof else date.today().strftime("%Y-%m")


def alltime_card(db, px):
    """HTML of the All-time performance card (wrapped in ALLTIME markers)."""
    cur = cur_month_of(px)
    asof = (px or {}).get("asof") or ""

    def cell(v):
        return "<td>&mdash;</td>" if v is None else f'<td class="{"pos" if v >= 0 else "neg"}">{v:+.2f}%</td>'

    runs = []
    for key in db.get("months", []):
        packs = db["data"].get(key, {})
        month = key[:7]
        src = ""
        for p in packs.values():
            src = str((p.get("summary") or {}).get("SourceDate") or "")[:10] or src
        res = {st: live_pack(key, packs[st], px.get("px", {}), cur) for st in STRATS if st in packs}
        runs.append((month, src, res))
    runs.sort(key=lambda x: (x[0], x[1]))
    body = ""
    for month, src, res in runs:
        tds = "".join(cell(res[st][1]) if st in res else "<td>&mdash;</td>" for st in STRATS)
        sts = {st: res[st][4] for st in res}
        if all(v.startswith("CLOSED") for v in sts.values()):
            status = "CLOSED" if all(v == "CLOSED" for v in sts.values()) else "CLOSED (daily prices)"
        elif any(v == "OPEN" for v in sts.values()):
            status = f"OPEN (daily close {asof})" if asof else "OPEN"
        else:
            status = "ENDED - prices pending (" + ", ".join(st for st, v in sts.items() if not v.startswith("CLOSED")) + ")"
        body += f"<tr><td>{month}</td><td>{src or 'legacy'}</td>{tds}<td>{status}</td></tr>"
    # totals: latest run of each month, closed months only (recorded or closed from daily prices)
    latest = {}
    for month, src, res in runs:                     # sorted, so the last run of a month wins
        for st, v in res.items():
            latest[(month, st)] = v
    tot = ""
    for label, fn in (("Months closed", lambda v: f"{len(v)}"),
                      ("Average / month", lambda v: f"{sum(v) / len(v):+.2f}%"),
                      ("Compounded", lambda v: f"{(_prod([1 + x / 100 for x in v]) - 1) * 100:+.2f}%"),
                      ("Winning months", lambda v: f"{sum(1 for x in v if x > 0)} / {len(v)}")):
        tds = ""
        for st in STRATS:
            v = [x[1] for (m, s2), x in sorted(latest.items()) if s2 == st and x[4].startswith("CLOSED") and x[1] is not None]
            tds += f"<td><b>{fn(v) if v else '&mdash;'}</b></td>"
        tot += f"<tr><td colspan='2'><b>{label}</b></td>{tds}<td></td></tr>"
    ths = "".join(f"<th>{st}</th>" for st in STRATS)
    note = (f" Open months and months closed from daily prices use daily closes (latest {asof}); "
            "the monthly pipeline run records the official month-end figures.") if asof else ""
    return ("<!--ALLTIME_START--><div class=\"card\"><h2 style=\"margin:0\">All-time performance (all strategies)</h2>"
            "<p style=\"color:#64748b;font-size:.85rem\">Average return of each recorded run. Totals use the latest run of each "
            f"closed month. S1/S2 = Top-10; S3/S4 = every stock passing the rule.{note}</p>"
            f"<table><thead><tr><th>Month</th><th>Source list</th>{ths}<th>Status</th></tr></thead>"
            f"<tbody>{body}{tot}</tbody></table></div><!--ALLTIME_END-->")


def _prod(xs):
    p = 1.0
    for x in xs:
        p *= x
    return p


# ---------------------------------------------------------------- which stocks need prices
def needed(db, cur_month):
    """{ticker: (earliest start date, latest date needed or None = up to today)}"""
    need = {}
    for key, packs in db.get("data", {}).items():
        month = key[:7]
        ended = month < cur_month
        for pack in packs.values():
            if (pack.get("summary") or {}).get("Status") == "CLOSED":
                continue
            for r in pack.get("rows", []):
                t, sd = r.get("Ticker"), str(r.get("StartDate") or "")[:10]
                if not t or not sd:
                    continue
                if ended and num(r.get("StartPrice")) and num(r.get("EndPrice")):
                    continue
                cap = month_end(month) if ended else None
                if t in need:
                    s0, c0 = need[t]
                    need[t] = (min(s0, sd), None if (c0 is None or cap is None) else max(c0, cap))
                else:
                    need[t] = (sd, cap)
    return need


# ---------------------------------------------------------------- price sources
def from_yahoo(ticker, start):
    import yfinance as yf
    sym = ticker.replace(".", "-")
    for attempt in range(3):
        try:
            h = yf.Ticker(sym).history(start=start, auto_adjust=False)
            if h is not None and len(h):
                return {d.strftime("%Y-%m-%d"): round(float(c), 2)
                        for d, c in zip(h.index, h["Close"]) if c == c and c > 0}
        except Exception as e:
            print(f"  {ticker}: Yahoo attempt {attempt + 1} failed: {e}")
        time.sleep(2 * (attempt + 1))
    return None


def from_stooq(ticker, start):
    sym = ticker.replace(".", "-").lower() + ".us"
    d1 = start.replace("-", "")
    d2 = (date.today() + timedelta(days=1)).strftime("%Y%m%d")
    url = f"https://stooq.com/q/d/l/?s={sym}&d1={d1}&d2={d2}&i=d"
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
            rows = list(csv.DictReader(io.StringIO(txt)))
            out = {}
            for r in rows:
                c = num(r.get("Close"))
                if r.get("Date") and c:
                    out[r["Date"]] = round(c, 2)
            if out:
                return out
            print(f"  {ticker}: Stooq returned no data ({txt[:60]!r})")
            return None
        except Exception as e:
            print(f"  {ticker}: Stooq attempt {attempt + 1} failed: {e}")
            time.sleep(3)
    return None


def fetch(ticker, start):
    s = from_yahoo(ticker, start)
    if s:
        return s, "yahoo"
    s = from_stooq(ticker, start)
    if s:
        return s, "stooq"
    return None, None


# ---------------------------------------------------------------- main
def main():
    html = open(PAGE, encoding="utf-8").read()
    if not PX_BLOCK.search(html):
        print("PX block markers not found in performance.html - nothing done.")
        return 1
    db = read_db(html)
    old = read_px(html)
    cur = date.today().strftime("%Y-%m")
    need = needed(db, cur)
    old_px, old_src = old.get("px", {}), old.get("src", {})
    px, src, failed = {}, {}, []
    latest_seen = ""                  # latest market day in any download (before cutting ended months)
    for t, (sd, cap) in sorted(need.items()):
        start = (datetime.strptime(sd, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
        series, where = fetch(t, start)
        if series:
            latest_seen = max(latest_seen, max(series))
            px[t] = {d: p for d, p in series.items() if d >= sd and (cap is None or d <= cap)}
            if where != "yahoo":
                src[t] = where
        elif t in old_px:
            px[t] = old_px[t]           # keep what we had for a ticker no source answered today
            if t in old_src:
                src[t] = old_src[t]
            failed.append(t)
        else:
            failed.append(t)
    print(f"{len(need)} tickers needed, {len(px)} priced, {len(failed)} failed: {failed}")
    if need and len(failed) > max(3, len(need) * 0.3):
        print("Too many failures - pages left unchanged.")
        return 1
    asof = max([latest_seen] + [max(v) for v in px.values() if v]) or old.get("asof", "")
    newpx = {"asof": asof, "px": px}
    if src:
        newpx["src"] = src
    block = "/*PX_START*/window.PX=" + json.dumps(newpx, separators=(",", ":")) + ";/*PX_END*/"
    new_html = PX_BLOCK.sub(lambda m: block, html, count=1)
    if new_html != html:
        open(PAGE, "w", encoding="utf-8", newline="").write(new_html)
        print(f"performance.html updated, prices as of {asof}")
    else:
        print("performance.html: no change.")
    try:
        at = open(ALLTIME, encoding="utf-8").read()
        if AT_BLOCK.search(at):
            new_at = AT_BLOCK.sub(lambda m: alltime_card(db, newpx), at, count=1)
            if new_at != at:
                open(ALLTIME, "w", encoding="utf-8", newline="").write(new_at)
                print("alltime-performance.html updated.")
            else:
                print("alltime-performance.html: no change.")
        else:
            print("alltime-performance.html has no ALLTIME markers yet - left unchanged.")
    except FileNotFoundError:
        print("alltime-performance.html not found - skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
