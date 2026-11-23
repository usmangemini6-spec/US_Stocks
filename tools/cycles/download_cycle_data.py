r"""
download_cycle_data.py - monthly (and daily) data for the Cycles pages, saved in scripts\\cycles_data\\.

Every item has a list of SOURCES. They are tried one by one, in order; the first that works is used,
and every attempt is printed, so you can see exactly which source failed and why.

Optional keys (set once in Windows, then reopen the command window):
    setx TE_API_KEY  "your-trading-economics-key"    (tradingeconomics.com, paid plans; used for KSE-100 and macro data)
    setx FRED_API_KEY "your-free-fred-key"            (fred.stlouisfed.org, free; official API instead of the CSV link)
Manual fallback: put a CSV with columns Date,Close (daily or monthly) into scripts\\cycles_data\\manual\\<key>.csv
(e.g. psx.csv downloaded by hand from investing.com or the PSX website). It is used when every online source fails.
World Economics (worldeconomics.com) has no public data API, so it is used the same way: download the series from
its Data Download Portal and save it as scripts\cycles_data\manual\worldeconomics_<key>.csv (e.g. worldeconomics_cpi.csv).
Note: World Economics data is mostly yearly, so it is only a last resort for the monthly cycle charts.

Run: python download_cycle_data.py
"""
import io, json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cycles_data")
MANUAL = os.path.join(OUT, "manual")
os.makedirs(MANUAL, exist_ok=True)
TE_KEY = os.environ.get("TE_API_KEY", "").strip()
FRED_KEY = os.environ.get("FRED_API_KEY", "").strip()


# ---------- helpers ----------
def get(url, timeout=45, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def monthly(df):
    """df with a 'Date' column (any date format) and Close (+ optional High/Low) -> monthly OHLC indexed by YYYY-MM"""
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Close"]).sort_values("Date")
    for c in ("Close", "High", "Low", "Open"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ("High", "Low", "Open"):
        if c not in df:
            df[c] = df["Close"]
    g = df.groupby(df["Date"].dt.strftime("%Y-%m"))
    m = pd.DataFrame({"Open": g["Open"].first(), "High": g["High"].max(), "Low": g["Low"].min(), "Close": g["Close"].last()})
    m.index.name = "Date"
    if m.empty:
        raise ValueError("no rows")
    return m


# ---------- source types ----------
def yahoo(sym):
    import yfinance as yf
    h = yf.Ticker(sym).history(period="max", interval="1d", auto_adjust=False)
    if h is None or len(h) < 250:
        # some markets (e.g. Saudi TASI) return little or no daily history: use monthly bars instead
        mh = yf.Ticker(sym).history(period="max", interval="1mo", auto_adjust=False)
        if mh is None or mh.empty:
            raise ValueError("no data (symbol may be delisted)")
        mh = mh[["Open", "High", "Low", "Close"]].dropna()
        mh.index = pd.to_datetime(mh.index).tz_localize(None)
        md = mh.reset_index()
        md.columns = ["Date", "Open", "High", "Low", "Close"]
        return monthly(md), None
    h = h[["Open", "High", "Low", "Close"]].dropna()
    h.index = pd.to_datetime(h.index).tz_localize(None)
    daily = h.reset_index().rename(columns={"index": "Date"})
    daily.columns = ["Date", "Open", "High", "Low", "Close"]
    return monthly(daily), daily


def stooq(sym):
    txt = get(f"https://stooq.com/q/d/l/?s={sym}&i=d")
    if not txt.startswith("Date"):
        raise ValueError("no data")
    d = pd.read_csv(io.StringIO(txt))
    return monthly(d), d


def fred_csv(sid):
    d = pd.read_csv(io.StringIO(get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=60)))
    d.columns = ["Date", "Close"]
    d = d[pd.to_numeric(d["Close"], errors="coerce") > 0]
    return monthly(d), None


def fred_api(sid):
    if not FRED_KEY:
        raise ValueError("FRED_API_KEY not set")
    js = json.loads(get(f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}&api_key={FRED_KEY}&file_type=json", timeout=60))
    d = pd.DataFrame([(o["date"], o["value"]) for o in js["observations"] if o["value"] != "."], columns=["Date", "Close"])
    return monthly(d), None


def csv_url(url, dcol, vcol):
    d = pd.read_csv(io.StringIO(get(url)))[[dcol, vcol]]
    d.columns = ["Date", "Close"]
    return monthly(d), None


def dbnomics(series):
    """DBnomics (db.nomics.world): free mirror of official statistics, e.g. BLS/cu/CUUR0000SA0 (US CPI)."""
    js = json.loads(get(f"https://api.db.nomics.world/v22/series/{series}?observations=1&format=json", timeout=60))
    doc = js["series"]["docs"][0]
    d = pd.DataFrame({"Date": doc["period_start_day"], "Close": doc["value"]})
    d = d[d["Close"] != "NA"]
    return monthly(d), None


def bls_cpi(_):
    y = datetime.now().year
    body = json.dumps({"seriesid": ["CUUR0000SA0"], "startyear": str(y - 9), "endyear": str(y)}).encode()
    js = json.loads(get("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body, headers={"Content-type": "application/json"}, timeout=60))
    rows = [(f"{r['year']}-{r['period'][1:]}-01", float(r["value"])) for r in js["Results"]["series"][0]["data"]
            if r["period"].startswith("M") and r["period"] != "M13"]
    return monthly(pd.DataFrame(rows, columns=["Date", "Close"])), None


def psx_portal(sym):
    txt = get(f"https://dps.psx.com.pk/timeseries/eod/{sym}",
              headers={"X-Requested-With": "XMLHttpRequest", "Referer": f"https://dps.psx.com.pk/indices/{sym}",
                       "Accept": "application/json, text/javascript, */*; q=0.01"})
    js = json.loads(txt)
    rows = js.get("data", js) if isinstance(js, dict) else js
    d = pd.DataFrame([(r[0], r[1]) for r in rows], columns=["ts", "Close"])
    d["Date"] = pd.to_datetime(d["ts"], unit="s")
    d = d[["Date", "Close"]]
    return monthly(d), d


def psx_site(arg):
    """PSX website (psx.com.pk / dps.psx.com.pk): today's index value only. Each run adds today's value to
    cycles_data\\manual\\<key>_live.csv, so the history grows month by month; it is merged with any
    hand-downloaded history in cycles_data\\manual\\<key>.csv."""
    import re
    key, sym = arg
    val, last_err = None, None
    for url in ("https://www.psx.com.pk/", "https://dps.psx.com.pk/indices", "https://dps.psx.com.pk/"):
        try:
            txt = re.sub(r"<[^>]+>", " ", get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}))
            m = re.search(rf"\b{sym}\s+([\d,]{{5,}}\.\d+)", re.sub(r"\s+", " ", txt))
            if m:
                val = float(m.group(1).replace(",", ""))
                break
            last_err = f"{sym} value not found on {url}"
        except Exception as e:
            last_err = f"{url}: {e}"
    if val is None:
        raise ValueError(last_err)
    live = os.path.join(MANUAL, f"{key}_live.csv")
    d = pd.read_csv(live) if os.path.exists(live) else pd.DataFrame(columns=["Date", "Close"])
    d = pd.concat([d[d["Date"] != datetime.now().strftime("%Y-%m-%d")],
                   pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), val]], columns=["Date", "Close"])])
    d.to_csv(live, index=False)
    hist = os.path.join(MANUAL, f"{key}.csv")
    if os.path.exists(hist):
        h, _ = manual(key)
        lm = monthly(d)
        h = pd.concat([h[~h.index.isin(lm.index)], lm]).sort_index()
        return h, None
    return monthly(d), d


def trading_economics(path):
    """Trading Economics API (tradingeconomics.com). Needs TE_API_KEY; path e.g. 'markets/historical/KSE100:IND'."""
    if not TE_KEY:
        raise ValueError("TE_API_KEY not set")
    sep = "&" if "?" in path else "?"
    js = json.loads(get(f"https://api.tradingeconomics.com/{path}{sep}c={urllib.parse.quote(TE_KEY)}&f=json", timeout=60))
    d = pd.DataFrame([(r.get("Date") or r.get("DateTime"), r.get("Close", r.get("Value"))) for r in js], columns=["Date", "Close"])
    return monthly(d), None


def manual(key):
    f = os.path.join(MANUAL, f"{key}.csv")
    if not os.path.exists(f):
        raise ValueError(f"no file {os.path.relpath(f, HERE)}")
    d = pd.read_csv(f)
    d.columns = [c.strip().title() for c in d.columns]
    if "Price" in d and "Close" not in d:          # investing.com export
        d = d.rename(columns={"Price": "Close"})
    cols = ["Close"] + [c for c in ("High", "Low", "Open") if c in d]
    for c in cols:
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", ""), errors="coerce")
    return monthly(d[["Date"] + cols]), None


# ---------- what to download: key -> (name, [ (label, function, argument), ... ]) ----------
Y, S = "Yahoo", "Stooq"
ITEMS = {
    # long histories for the long-term cycles (old data is fine; the latest months come from "sp" / "gold")
    "sp_long":  ("S&P 500 since 1871",    [("GitHub datasets", lambda a: csv_url(a, "Date", "SP500"), "https://raw.githubusercontent.com/datasets/s-and-p-500/main/data/data.csv")]),
    "gold_long": ("Gold since 1833",      [("GitHub datasets", lambda a: csv_url(a, "Date", "Price"), "https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv")]),
    "sp":       ("S&P 500",               [(Y, yahoo, "^GSPC"), (S, stooq, "^spx")]),
    "nasdaq":   ("NASDAQ Composite",      [(Y, yahoo, "^IXIC"), (S, stooq, "^ndq")]),
    "dji":      ("Dow Jones",             [(Y, yahoo, "^DJI"), (S, stooq, "^dji")]),
    "tasi":     ("Saudi TASI",            [(Y, yahoo, "^TASI.SR"), ("Trading Economics", trading_economics, "markets/historical/TASI:IND")]),
    "psx":      ("Pakistan KSE-100 (PSX)", [("PSX data portal", psx_portal, "KSE100"),
                                            ("PSX website (today's value)", psx_site, ("psx", "KSE100")),
                                            ("Trading Economics", trading_economics, "markets/historical/KSE100:IND"),
                                            ("Manual file", manual, "psx"), ("World Economics (downloaded file)", manual, "worldeconomics_psx")]),
    "kmi30":    ("Pakistan KMI-30 (Shariah)", [("PSX data portal", psx_portal, "KMI30"), ("PSX website (today's value)", psx_site, ("kmi30", "KMI30")), ("Manual file", manual, "kmi30"), ("World Economics (downloaded file)", manual, "worldeconomics_kmi30")]),
    "gold":     ("Gold",                  [(Y, yahoo, "GC=F"), (S, stooq, "xauusd")]),
    "silver":   ("Silver",                [(Y, yahoo, "SI=F"), (S, stooq, "xagusd")]),
    "dollar":   ("US Dollar Index",       [(Y, yahoo, "DX-Y.NYB")]),
    "us10y":    ("US 10-year yield",      [(Y, yahoo, "^TNX"), ("FRED API", fred_api, "GS10"), ("FRED CSV", fred_csv, "GS10")]),
    "fedfunds": ("Fed funds rate",        [("FRED API", fred_api, "FEDFUNDS"), ("FRED CSV", fred_csv, "FEDFUNDS"),
                                           ("DBnomics", dbnomics, "FED/H15/RIFSPFF_N.M"), (Y + " 13-week T-bill", yahoo, "^IRX"), ("World Economics (downloaded file)", manual, "worldeconomics_fedfunds")]),
    "oil":      ("Crude oil WTI",         [(Y, yahoo, "CL=F"), ("FRED API", fred_api, "MCOILWTICO"), ("FRED CSV", fred_csv, "MCOILWTICO")]),
    "brent":    ("Crude oil Brent",       [(Y, yahoo, "BZ=F")]),
    "cpi":      ("US CPI index",          [("FRED API", fred_api, "CPIAUCSL"), ("FRED CSV", fred_csv, "CPIAUCSL"),
                                           ("DBnomics (BLS)", dbnomics, "BLS/cu/CUUR0000SA0"),
                                           ("GitHub datasets", lambda a: csv_url(a, "Date", "Index"), "https://raw.githubusercontent.com/datasets/cpi-us/main/data/cpiai.csv"),
                                           ("BLS API (10 years)", bls_cpi, None),
                                           ("Trading Economics", trading_economics, "historical/country/united%20states/indicator/consumer%20price%20index%20cpi"), ("World Economics (downloaded file)", manual, "worldeconomics_cpi")]),
    "home":     ("US home prices (Case-Shiller)", [("FRED API", fred_api, "CSUSHPINSA"), ("FRED CSV", fred_csv, "CSUSHPINSA"),
                                           ("GitHub datasets", lambda a: csv_url(a, "Date", "National-US"), "https://raw.githubusercontent.com/datasets/house-prices-us/main/data/national-month.csv"),
                                           ("DBnomics (BIS, quarterly)", dbnomics, "BIS/WS_SPP/Q.US.N.628"),
                                           ("Trading Economics", trading_economics, "historical/country/united%20states/indicator/case%20shiller%20home%20price%20index"),
                                           ("Manual file", manual, "home"), ("World Economics (downloaded file)", manual, "worldeconomics_home")]),
    # gold / silver funds and Shariah-compliant miners (metal-vs-miners comparison)
    "aem":      ("Agnico Eagle (AEM)",    [(Y, yahoo, "AEM")]),
    "drd":      ("DRDGOLD (DRD)",         [(Y, yahoo, "DRD")]),
    "gld":      ("Gold fund GLD",         [(Y, yahoo, "GLD")]),
    "iau":      ("Gold fund IAU",         [(Y, yahoo, "IAU")]),
    "slv":      ("Silver fund SLV",       [(Y, yahoo, "SLV")]),
}


def fill_gaps(key, m):
    """months missing in the download are filled from manual\\<key>_fill.csv (Date,Close), e.g. data copied from GuruFocus"""
    f = os.path.join(MANUAL, f"{key}_fill.csv")
    if not os.path.exists(f):
        return m
    x = pd.read_csv(f)
    x["Date"] = x["Date"].astype(str).str[:7]
    add = x[~x["Date"].isin(m.index)].set_index("Date")
    if add.empty:
        return m
    for c in m.columns:
        if c not in add.columns:
            add[c] = add["Close"]
    m = pd.concat([m, add[m.columns]]).sort_index()
    print(f"          + {len(add)} missing months filled from manual\\{key}_fill.csv")
    return m


def save(key, m, d):
    m = fill_gaps(key, m)
    m.to_csv(os.path.join(OUT, f"{key}.csv"))
    if d is not None and len(d):
        d2 = d.copy()
        d2["Date"] = pd.to_datetime(d2["Date"]).dt.strftime("%Y-%m-%d")
        d2.to_csv(os.path.join(OUT, f"{key}_daily.csv"), index=False)


def main():
    only = [a.lower() for a in sys.argv[1:]]          # optional: python download_cycle_data.py psx cpi
    ok, bad = [], []
    for key, (name, sources) in ITEMS.items():
        if only and key not in only:
            continue
        print(f"{key:9} {name}")
        stale = None                                  # an old-only result is kept, but newer sources are still tried
        for label, fn, arg in sources:
            t0 = time.time()
            try:
                m, d = fn(arg)
                months_old = (datetime.now().year * 12 + datetime.now().month) - (int(m.index[-1][:4]) * 12 + int(m.index[-1][5:7]))
                if stale is not None:                   # join the long old history in front of the newer data
                    m = pd.concat([stale[0][stale[0].index < m.index[0]], m])
                if months_old > 6 and not key.endswith("_long"):
                    print(f"          ~ {label}: data ends {m.index[-1]} (old), trying the next source too")
                    stale = (m, d, label)
                    continue
                save(key, m, d)
                msg = f"{label}: OK, {m.index[0]} to {m.index[-1]} ({len(m)} months)"
                print(f"          ✓ {msg}")
                ok.append(f"{key:9} {name:30} {msg}")
                break
            except Exception as e:
                print(f"          ✗ {label}: {str(e)[:110]} ({time.time() - t0:.0f}s)")
        else:
            if stale is not None:
                save(key, stale[0], stale[1])
                ok.append(f"{key:9} {name:30} {stale[2]}: OLD data only, ends {stale[0].index[-1]}")
                continue
            bad.append(f"{key} ({name})")
    print("\nSaved to", OUT)
    print("\n".join(ok))
    if bad:
        print("\nNOT downloaded (every source failed):", "; ".join(bad))
        print("Tip: for any of these you can put a hand-downloaded CSV (Date,Close) into", MANUAL)


if __name__ == "__main__":
    main()
