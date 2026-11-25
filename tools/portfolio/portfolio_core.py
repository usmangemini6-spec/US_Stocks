r"""
portfolio_core.py - the private SAlgo portfolio (shared by the PC manager and the daily GitHub job).

Rules (change only here)
  - Start: $100,000 cash. Every Buy puts $5,000 (5%) into a stock; Buy again = add another $5,000.
    Every Sell takes $5,000 out of the stock ("Close" sells all of it).
  - Buy/Add only while the stock passes all 8 Preferred checks (traffic light GREEN).
  - Max 10% of the portfolio in one stock, max 30% in one sector, need $5,000 cash.
  - Automatic close: when a daily close reaches the position's target (the Price Target on the day of
    the last Buy), the whole position is sold at that close.
  - Flags only (you decide): down 20% from average cost; target not reached after 12 months;
    traffic light AMBER (dropped off the list, fails 1-2 checks) or RED (fails 3+ checks or
    Business Analysis SELL, or not in the latest data).
  - Buy zone badge: price at or below the Business Analysis "buy below" price.
  - SAlgo Autopilot: its own $100,000, same rules. On every new monthly data list it first sells its
    RED holdings, then buys one $5,000 unit of each Preferred stock in order of Salman Score, then
    Score TTM, while cash and the limits allow. Target closes work the same way.

Storage (each file has ONE writer, so nothing can overwrite anything else)
  - tools/portfolio/universe.enc : latest Preferred data + monthly Autopilot snapshots. Written only by
    the PC (build_shortlisted.py -> portfolio_manager.refresh), published by DEPLOY_TO_GITHUB.bat.
  - tools/portfolio/trades.enc   : your trades + recent trade requests. Written only by the GitHub
    "Portfolio" workflow (trade.py), from the Buy / Sell buttons on the locked page.
  - portfolio.html               : the page. Built only on GitHub (render in page.py); its data block
    /*PF_START*/ ... /*PF_END*/ is encrypted and decrypted in the browser after the password.
  All encrypted with AES-256-GCM, key from the password with PBKDF2-SHA256.
  The automatic target closes are worked out from the daily closes every time (never stored).
"""
import base64
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", ".."))
LEDGER = os.path.join(HERE, "ledger.enc")            # old single file (before web trading) - migrated
UNIVERSE = os.path.join(HERE, "universe.enc")
TRADES = os.path.join(HERE, "trades.enc")
MAX_REQUESTS = 100
PAGE = os.path.join(SITE, "portfolio.html")
PF_BLOCK = re.compile(r"/\*PF_START\*/window\.PF=(\".*?\");/\*PF_END\*/", re.S)

START_CASH = 100000.0
UNIT = 5000.0
MAX_STOCK_PCT = 10.0
MAX_SECTOR_PCT = 30.0
TOL_PCT = 0.25            # small tolerance so 2 x $5,000 = 10% is still allowed after tiny price moves
LOSS_FLAG_PCT = -20.0
AGE_FLAG_DAYS = 365
RED_FAILS = 3
BENCH = "SPY"
KDF_ITER = 310000

CHECK_NAMES = {1: "SAlgo model", 2: "Salman scores", 3: "Business Analysis", 4: "ThirdParty Valuation",
               5: "Analyst Rating", 6: "Upside", 7: "3-year projection", 8: "Score TTM"}


# ======================================================================= encryption
def _key(password, salt):
    import hashlib
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, KDF_ITER, 32)


def encrypt(obj, password):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, nonce = os.urandom(16), os.urandom(12)
    ct = AESGCM(_key(password, salt)).encrypt(nonce, json.dumps(obj, separators=(",", ":")).encode("utf-8"), None)
    b = lambda x: base64.b64encode(x).decode("ascii")
    return f"v1.{b(salt)}.{b(nonce)}.{b(ct)}"


def decrypt(blob, password):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    v, s, n, c = blob.strip().split(".")
    if v != "v1":
        raise ValueError("unknown format")
    d = base64.b64decode
    return json.loads(AESGCM(_key(password, d(s))).decrypt(d(n), d(c), None).decode("utf-8"))


def new_ledger():
    return {"version": 2, "created": date.today().isoformat(), "trades": [], "requests": [], "universe": {}, "snapshots": []}


def _read(path, password):
    with open(path, encoding="ascii") as f:
        return decrypt(f.read(), password)


def _write(path, obj, password):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="ascii") as f:
        f.write(encrypt(obj, password))
    os.replace(tmp, path)


def load_ledger(password):
    """Both files merged into one dict (falls back to the old single ledger.enc)."""
    led = new_ledger()
    if not os.path.exists(UNIVERSE) and not os.path.exists(TRADES) and os.path.exists(LEDGER):
        old = _read(LEDGER, password)
        led.update({k: old.get(k, led[k]) for k in ("trades", "universe", "snapshots")})
        return led
    if os.path.exists(UNIVERSE):
        u = _read(UNIVERSE, password)
        led["universe"], led["snapshots"] = u.get("universe") or {}, u.get("snapshots") or []
    if os.path.exists(TRADES):
        t = _read(TRADES, password)
        led["trades"], led["requests"] = t.get("trades") or [], t.get("requests") or []
    return led


def save_universe(ledger, password):          # PC only
    _write(UNIVERSE, {"universe": ledger["universe"], "snapshots": ledger["snapshots"]}, password)


def save_trades(ledger, password):            # GitHub trade job only (and one-time migration / password change)
    ledger["requests"] = ledger.get("requests", [])[-MAX_REQUESTS:]
    _write(TRADES, {"trades": ledger["trades"], "requests": ledger["requests"]}, password)


def read_page_state(password):
    """Last published state (used as a price cache)."""
    try:
        m = PF_BLOCK.search(open(PAGE, encoding="utf-8").read())
        return decrypt(json.loads(m.group(1)), password) if m else None
    except Exception:
        return None


def write_page_state(state, password):
    """Build the whole portfolio.html (current menu + encrypted data). Runs on GitHub."""
    import page
    block = "/*PF_START*/window.PF=" + json.dumps(encrypt(state, password)) + ";/*PF_END*/"
    html = page.page_html(os.environ.get("GITHUB_REPOSITORY") or page.DEFAULT_REPO)
    if not PF_BLOCK.search(html):
        raise ValueError("page template has no data block")
    html = PF_BLOCK.sub(lambda m: block, html)
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(html)


# ======================================================================= helpers
def num(v):
    try:
        f = float(str(v).replace(",", "").replace("$", "").strip())
        return f if f == f else None
    except Exception:
        return None


def parse_buy_below(text, ref_price):
    """First number in the Business Analysis 'buy below' text; ignored when it is clearly not a
    price for this stock (more than 3x away from the analysis price)."""
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)", str(text or ""))
    v = num(m.group(1)) if m else None
    if not v or not ref_price or not (ref_price / 3 <= v <= ref_price * 3):
        return None
    return round(v, 2)


def light_of(u):
    """GREEN / AMBER / RED for a stock in the latest data (u = universe entry or None)."""
    if not u:
        return "RED"
    if (u.get("ba") or "").upper() == "SELL" or len(u.get("fails") or []) >= RED_FAILS:
        return "RED"
    return "GREEN" if not u.get("fails") else "AMBER"


def to_iso(d):
    for fmt in ("%Y-%m-%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(str(d), fmt).date().isoformat()
        except Exception:
            pass
    return date.today().isoformat()


# ======================================================================= snapshots (from the PC data)
def update_universe(ledger, rows, ba, data_date):
    """rows = build_shortlisted.evaluate() output for ALL stocks. Refreshes the latest-data view and
    adds an Autopilot snapshot the first time a data date is seen (snapshots never change later)."""
    iso = to_iso(data_date)
    stocks = {}
    for r in rows:
        b = ba.get(r["t"]) or {}
        stocks[r["t"]] = {
            "name": r["company"], "sector": r["sector"] or "Other",
            "fails": [i + 1 for i, ok in enumerate(r["checks"]) if not ok],
            "ba": str(b.get("rating") or "").upper(), "price": r["price"], "pt": r["pt"],
            "upside": r["upside"], "salman": r["salman"], "ttm": r["ttm"], "uo": r["uo"],
            "buy_below": parse_buy_below(b.get("buy_below"), num(b.get("price")) or r["price"]),
        }
    ledger["universe"] = {"date": iso, "updated": datetime.now().isoformat(timespec="seconds"), "stocks": stocks}
    if not any(s["date"] == iso for s in ledger["snapshots"]):
        pref = [(t, s) for t, s in stocks.items() if not s["fails"] and s["price"] and s["pt"]]
        pref.sort(key=lambda x: (-(x[1]["salman"] or 0), -(x[1]["ttm"] or 0), x[0]))
        ever = {t for snap in ledger["snapshots"] for t in snap["ranked"]} | {t for t, _ in pref}
        ledger["snapshots"].append({
            "date": iso,
            "ranked": [t for t, _ in pref],
            "info": {t: {"sector": s["sector"], "price": s["price"], "pt": s["pt"]} for t, s in pref},
            "red": sorted(t for t in ever if light_of(stocks.get(t)) == "RED"),
        })
        ledger["snapshots"].sort(key=lambda s: s["date"])
    return ledger


# ======================================================================= simulation
class Book:
    def __init__(self, name):
        self.name, self.cash, self.pos, self.closed, self.log, self.hist = name, START_CASH, {}, [], [], []

    def value_of(self, px, d, fallback=None):
        return sum(p["shares"] * price_on(px, t, d, p["avg"]) for t, p in self.pos.items())

    def total(self, px, d):
        return self.cash + self.value_of(px, d)

    def sector_value(self, px, d, sector):
        return sum(p["shares"] * price_on(px, t, d, p["avg"]) for t, p in self.pos.items() if p["sector"] == sector)

    def buy(self, t, d, price, target, sector, src="you"):
        p = self.pos.setdefault(t, {"shares": 0.0, "cost": 0.0, "avg": price, "first": d, "sector": sector, "target": target})
        sh = UNIT / price
        p["shares"] += sh
        p["cost"] += UNIT
        p["avg"] = p["cost"] / p["shares"]
        p["last"] = d
        p["target"] = target or p.get("target")
        p["sector"] = sector or p["sector"]
        self.cash -= UNIT
        self.log.append({"date": d, "t": t, "side": "BUY", "price": round(price, 2), "amount": UNIT, "by": src})

    def sell(self, t, d, price, amount=None, reason="Sold", src="you"):
        p = self.pos.get(t)
        if not p:
            return
        sh = p["shares"] if amount is None else min(p["shares"], amount / price)
        if p["shares"] - sh < 1e-9 or (p["shares"] - sh) * price < UNIT / 2:   # less than half a unit left: sell it all
            sh = p["shares"]
        proceeds = sh * price
        cost = sh * p["avg"]
        self.cash += proceeds
        p["shares"] -= sh
        p["cost"] -= cost
        self.log.append({"date": d, "t": t, "side": "SELL", "price": round(price, 2), "amount": round(proceeds, 2),
                         "by": src, "reason": reason})
        self.closed.append({"date": d, "t": t, "reason": reason, "price": round(price, 2), "proceeds": round(proceeds, 2),
                            "pl": round(proceeds - cost, 2), "pl_pct": round((price / p["avg"] - 1) * 100, 2),
                            "full": p["shares"] <= 1e-9, "by": src})
        if p["shares"] <= 1e-9:
            del self.pos[t]


def price_on(px, t, d, fallback=None):
    """Latest close on or before d."""
    h = px.get(t) or {}
    best = None
    for k in h:
        if k <= d and (best is None or k > best):
            best = k
    return h[best] if best else fallback


def check_buy(book, px, d, t, u, price):
    """Reason a Buy is not allowed, or None. u = latest-data entry of the stock."""
    if light_of(u) != "GREEN":
        return "Not on the Preferred list now (fails: " + ", ".join(CHECK_NAMES[i] for i in (u or {}).get("fails", [])) + ")" if u else "Not in the latest data"
    if book.cash < UNIT - 0.01:
        return f"Not enough cash (${book.cash:,.0f}, need ${UNIT:,.0f})"
    total = book.total(px, d)
    p = book.pos.get(t)
    pos_after = (p["shares"] * price_on(px, t, d, p["avg"]) if p else 0) + UNIT
    if pos_after / total * 100 > MAX_STOCK_PCT + TOL_PCT:
        return f"Would be {pos_after / total * 100:.1f}% in {t} (max {MAX_STOCK_PCT:.0f}%)"
    sec = (u or {}).get("sector") or "Other"
    sec_after = book.sector_value(px, d, sec) + UNIT
    if sec_after / total * 100 > MAX_SECTOR_PCT + TOL_PCT:
        return f"Would be {sec_after / total * 100:.1f}% in {sec} (max {MAX_SECTOR_PCT:.0f}%)"
    return None


def simulate(ledger, px, today=None):
    """Replays your trades and the Autopilot day by day. Returns (you, auto, days)."""
    today = today or date.today().isoformat()
    you, auto = Book("you"), Book("auto")
    trades = sorted(ledger["trades"], key=lambda x: (x["date"], x.get("seq", 0)))
    snaps = ledger["snapshots"]
    starts = [x["date"] for x in trades] + [s["date"] for s in snaps]
    if not starts:
        return you, auto, []
    start = min(starts)
    days = {d for h in px.values() for d in h if start <= d <= today} | {d for d in starts if d <= today}
    days = sorted(days)
    ti = si = 0
    for d in days:
        trading = (px.get(BENCH) or {}).get(d) is not None
        # 1) automatic target closes at today's close (positions bought before today)
        for book in (you, auto):
            for t, p in list(book.pos.items()):
                c = (px.get(t) or {}).get(d)
                if c and p.get("target") and p.get("last", d) < d and c >= p["target"]:
                    book.sell(t, d, c, None, "Target reached", "auto-close")
        # 2) your trades of the day
        while ti < len(trades) and trades[ti]["date"] <= d:
            x = trades[ti]
            if x["side"] == "BUY":
                you.buy(x["t"], x["date"], x["price"], x.get("target"), x.get("sector"))
            else:
                you.sell(x["t"], x["date"], x["price"], None if x.get("all") else UNIT,
                         "Closed by you" if x.get("all") else "Sold by you")
            ti += 1
        # 3) Autopilot on a new data list
        while si < len(snaps) and snaps[si]["date"] <= d:
            s = snaps[si]
            for t in list(auto.pos):
                if t in s["red"]:
                    auto.sell(t, d, price_on(px, t, d, auto.pos[t]["avg"]), None, "Dropped (red)", "autopilot")
            for t in s["ranked"]:
                inf = s["info"][t]
                u = {"fails": [], "sector": inf["sector"], "ba": ""}
                price = price_on(px, t, d, None) or inf["price"]
                if check_buy(auto, px, d, t, u, price) is None:
                    auto.buy(t, d, price, inf["pt"], inf["sector"], "autopilot")
            si += 1
        for book in (you, auto):
            book.hist.append([d, round(book.total(px, d), 2)])
    return you, auto, days


def needed_tickers(ledger, you=None, auto=None):
    ts = {x["t"] for x in ledger["trades"]}
    for b in (you, auto):
        if b:
            ts |= set(b.pos) | {c["t"] for c in b.closed}
    return ts


# ======================================================================= page state
def book_view(book, px, d, uni, days_hist):
    total = book.total(px, d)
    rows = []
    for t, p in sorted(book.pos.items()):
        u = uni.get(t)
        last = price_on(px, t, d, p["avg"])
        val = p["shares"] * last
        pl_pct = (last / p["avg"] - 1) * 100
        age = (date.fromisoformat(d) - date.fromisoformat(p["first"])).days
        flags = []
        if pl_pct <= LOSS_FLAG_PCT:
            flags.append(f"Down {pl_pct:.0f}% from cost")
        if age >= AGE_FLAG_DAYS:
            flags.append("Target not reached after 12 months")
        bb = (u or {}).get("buy_below")
        rows.append({
            "t": t, "name": (u or {}).get("name", ""), "sector": p["sector"], "light": light_of(u),
            "fails": [CHECK_NAMES[i] for i in (u or {}).get("fails", [])], "ba": (u or {}).get("ba", ""),
            "shares": round(p["shares"], 4), "avg": round(p["avg"], 2), "last": round(last, 2),
            "cost": round(p["cost"], 2), "value": round(val, 2), "weight": round(val / total * 100, 2),
            "pl": round(val - p["cost"], 2), "pl_pct": round(pl_pct, 2), "target": p.get("target"),
            "to_target": round((p["target"] / last - 1) * 100, 2) if p.get("target") else None,
            "first": p["first"], "lastbuy": p.get("last"), "flags": flags,
            "buyzone": bool(bb and last <= bb), "buy_below": bb,
        })
    sectors = {}
    for r in rows:
        sectors[r["sector"]] = round(sectors.get(r["sector"], 0) + r["weight"], 2)
    realized = round(sum(c["pl"] for c in book.closed), 2)
    return {"total": round(total, 2), "cash": round(book.cash, 2), "ret_pct": round((total / START_CASH - 1) * 100, 2),
            "invested_pct": round((total - book.cash) / total * 100, 2) if total else 0, "realized": realized,
            "unrealized": round(sum(r["pl"] for r in rows), 2), "holdings": rows, "sectors": sectors,
            "closed": list(reversed(book.closed)), "log": list(reversed(book.log)), "hist": book.hist}


def build_state(ledger, px, today=None):
    today = today or date.today().isoformat()
    you, auto, days = simulate(ledger, px, today)
    last = days[-1] if days else today
    uni = (ledger.get("universe") or {}).get("stocks") or {}
    bench = []
    if days and px.get(BENCH):
        b0 = price_on(px, BENCH, days[0])
        if b0:
            bench = [[d, round(START_CASH * price_on(px, BENCH, d, b0) / b0, 2)] for d in days]
    eligible = []
    for t, u in uni.items():
        if light_of(u) == "GREEN":
            last_px = price_on(px, t, last, u["price"])
            eligible.append({"t": t, "name": u["name"], "sector": u["sector"], "price": round(last_px or 0, 2),
                             "pt": u["pt"], "upside": u["upside"], "salman": u["salman"], "ttm": u["ttm"],
                             "buyzone": bool(u.get("buy_below") and last_px and last_px <= u["buy_below"]),
                             "buy_below": u.get("buy_below"),
                             "why_not": check_buy(you, px, last, t, u, last_px or u["price"])})
    eligible.sort(key=lambda e: (-(e["salman"] or 0), -(e["ttm"] or 0)))
    return {
        "generated": datetime.now().isoformat(timespec="minutes"), "as_of": last,
        "data_date": (ledger.get("universe") or {}).get("date"),
        "rules": {"start": START_CASH, "unit": UNIT, "max_stock": MAX_STOCK_PCT, "max_sector": MAX_SECTOR_PCT,
                  "loss_flag": LOSS_FLAG_PCT, "age_days": AGE_FLAG_DAYS},
        "you": book_view(you, px, last, uni, days), "auto": book_view(auto, px, last, uni, days),
        "bench": bench, "eligible": eligible,
        "autopilot_start": ledger["snapshots"][0]["date"] if ledger["snapshots"] else None,
        "requests": ledger.get("requests", [])[-20:],
    }


# ======================================================================= prices
def fetch_prices(ledger, cache=None, fetcher=None, today=None, log=print, extra=()):
    """Daily closes for every ticker the two portfolios need, plus SPY. Rebuilt from the first
    trade / snapshot date every time (missed days fill themselves). fetcher(ticker, start) -> {date: close}."""
    if fetcher is None:
        sys.path.insert(0, os.path.dirname(HERE))
        from update_prices import fetch as _f
        fetcher = lambda t, s: _f(t, s)[0]
    starts = [x["date"] for x in ledger["trades"]] + [s["date"] for s in ledger["snapshots"]] + [today or date.today().isoformat()]
    start = (date.fromisoformat(min(starts)) - timedelta(days=10)).isoformat()
    px = {}
    cache = cache or {}
    got = set()
    for _ in range(4):                     # Autopilot holdings depend on prices: repeat until stable
        you, auto, _d = simulate(ledger, px, today)
        need = (needed_tickers(ledger, you, auto) | {BENCH} | set(extra)) - got
        if not need:
            break
        for t in sorted(need):
            s = None
            try:
                s = fetcher(t, start)
            except Exception as e:
                log(f"  {t}: price download failed ({e})")
            if not s and cache.get(t):
                s = cache[t]
                log(f"  {t}: using the previous prices")
            if s:
                px[t] = s
            got.add(t)
    return px


# ======================================================================= a trade (GitHub job)
def latest_close(px, t, today):
    h = px.get(t) or {}
    ds = [d for d in h if d <= today]
    return (h[max(ds)], max(ds)) if ds else (None, None)


def apply_request(ledger, req, px, today=None, now_ms=None):
    """Validates one decrypted trade request from the page and adds it to ledger["trades"].
    Returns (ok, message). Always records the request id so the page can show the result."""
    import time
    today = today or date.today().isoformat()
    now_ms = now_ms or int(time.time() * 1000)
    rid = str(req.get("id") or "")[:64]
    if not re.fullmatch(r"[A-Za-z0-9-]{8,64}", rid):
        return False, "Bad request id."
    if any(r["id"] == rid for r in ledger.get("requests", [])):
        return False, "Already processed."

    def done(ok, msg):
        ledger.setdefault("requests", []).append({"id": rid, "ok": ok, "msg": msg, "at": datetime.utcnow().isoformat(timespec="seconds") + "Z"})
        return ok, msg

    ts = int(req.get("ts") or 0)
    if not (now_ms - 2 * 3600 * 1000 <= ts <= now_ms + 10 * 60 * 1000):
        return done(False, "Request too old - press the button again.")
    t = str(req.get("t") or "").upper()
    act = req.get("act")
    if not re.fullmatch(r"[A-Z0-9.\-]{1,10}", t) or act not in ("BUY", "SELL", "CLOSE"):
        return done(False, "Bad stock or action.")
    price = num(req.get("price"))
    if price is None or price <= 0:
        price, pdate = latest_close(px, t, today)
        if price is None:
            u = (ledger.get("universe") or {}).get("stocks", {}).get(t) or {}
            price = u.get("price")
        if not price:
            return done(False, f"No price found for {t} - type the price and try again.")
    you, _a, _d = simulate(ledger, px, today)
    u = (ledger.get("universe") or {}).get("stocks", {}).get(t)
    seq = len(ledger["trades"])
    if act == "BUY":
        why = check_buy(you, px, today, t, u, price)
        if why:
            return done(False, why)
        ledger["trades"].append({"date": today, "seq": seq, "t": t, "side": "BUY", "price": round(price, 4),
                                 "target": u.get("pt"), "sector": u.get("sector"), "req": rid})
        return done(True, f"Bought ${UNIT:,.0f} of {t} at ${price:,.2f}")
    if t not in you.pos:
        return done(False, f"You do not hold {t}.")
    ledger["trades"].append({"date": today, "seq": seq, "t": t, "side": "SELL", "price": round(price, 4),
                             "all": act == "CLOSE", "req": rid})
    return done(True, (f"Closed {t}" if act == "CLOSE" else f"Sold ${UNIT:,.0f} of {t}") + f" at ${price:,.2f}")
