"""Data access for the Cycles pages: monthly series from scripts\\cycles_data\\ (made by download_cycle_data.py)."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(os.path.dirname(HERE), "cycles_data") + os.sep


def have(key):
    f = CD + key + ".csv"
    return os.path.exists(f) and os.path.getsize(f) > 200


def series(key, start="1800-01"):
    """[(YYYY-MM, close), ...] from cycles_data\\<key>.csv"""
    out = []
    for r in csv.DictReader(open(CD + key + ".csv", encoding="utf-8")):
        try:
            v = float(r["Close"])
        except (TypeError, ValueError):
            continue
        d = r["Date"][:7]
        if v > 0 and d >= start:
            out.append((d, v))
    return out


def merged(long_key, short_key, start="1800-01"):
    """long history (e.g. monthly averages since 1871) extended with the newer months of the short series"""
    s = series(short_key, start) if have(short_key) else []
    if not have(long_key):
        return s
    l = series(long_key, start)
    if not s:
        return l
    first = s[0][0]                       # month-end closes win where both exist
    return [x for x in l if x[0] < first] + s


def yoy(sr):
    m = dict(sr)
    return [(d, (v / m[str(int(d[:4]) - 1) + d[4:]] - 1) * 100) for d, v in sr if str(int(d[:4]) - 1) + d[4:] in m]


def daily_last(key):
    """(date, last close, record close, record date) from <key>_daily.csv, or None"""
    f = CD + key + "_daily.csv"
    if not os.path.exists(f):
        return None
    best, last = None, None
    for r in csv.DictReader(open(f, encoding="utf-8")):
        try:
            v = float(r["Close"])
        except (TypeError, ValueError):
            continue
        last = (r["Date"][:10], v)
        if best is None or v >= best[1]:
            best = (r["Date"][:10], v)
    return last and (last[0], last[1], best[1], best[0])
