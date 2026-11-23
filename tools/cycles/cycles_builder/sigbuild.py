"""Builds work/sig.json: for every market, the tested cycles, the combined forecast line
(made from data up to December of last year), buy/sell signal windows and their records."""
import json, datetime, numpy as np
import salgo_cycle as sc
from cdata import have, series, merged, yoy, daily_last

NOW = datetime.date.today()
CUR = f"{NOW.year}-{NOW.month:02d}"            # running month (not complete)
ORIGIN = f"{NOW.year - 1}-12"                  # forecast made from data up to here
END = f"{NOW.year + 1}-12"                     # forecast horizon
US = {"sp", "nasdaq", "dji"}
MARKETS = [  # key, name, unit, loader, log scale, daily key
    ("sp", "S&P 500", "index", lambda: merged("sp_long", "sp", "1871-01"), True, "sp"),
    ("nasdaq", "NASDAQ Composite", "index", lambda: series("nasdaq"), True, "nasdaq"),
    ("dji", "Dow Jones", "index", lambda: series("dji"), True, "dji"),
    ("tasi", "Saudi TASI", "index", lambda: series("tasi"), True, "tasi"),
    ("psx", "Pakistan KSE-100", "index", lambda: series("psx"), True, "psx"),
    ("gold", "Gold", "$/oz", lambda: merged("gold_long", "gold", "1971-08"), True, "gold"),
    ("silver", "Silver", "$/oz", lambda: series("silver"), True, "silver"),
    ("oil", "Crude oil (WTI)", "$/barrel", lambda: merged("wti_fred", "oil"), True, "oil"),
    ("home", "US home prices", "index", lambda: series("home", "1975-01"), True, None),
    ("cpi", "US inflation", "% a year", lambda: yoy(series("cpi")), False, None),
    ("us10y", "US 10-year yield", "%", lambda: series("us10y"), False, "us10y"),
    ("fedfunds", "Fed funds rate", "%", lambda: series("fedfunds"), False, None),
]
NEEDS = {"sp": "sp", "nasdaq": "nasdaq", "dji": "dji", "tasi": "tasi", "psx": "psx", "gold": "gold", "silver": "silver",
         "oil": "oil", "home": "home", "cpi": "cpi", "us10y": "us10y", "fedfunds": "fedfunds"}
COMPS = sc.all_components(fixed=(24, 42, 54, 84, 108))


def votes(S, i, used, a, b, H):
    out = {}
    for k in used:
        p, _ = sc.pattern_path(S, i, COMPS[k][1], H)
        p = np.concatenate([[0.0], p])
        ch = p[b] - p[a]
        out[k] = 1 if ch > 1e-3 else (-1 if ch < -1e-3 else 0)
    return out


def analog_record(S, used, a_ym, b_ym, first):
    """how often the market rose from month-end a_ym to month-end b_ym in comparable past years"""
    yb = int(b_ym[:4]); span = (int(b_ym[:4]) - int(a_ym[:4]))
    years = [y for y in range(first, NOW.year) if ("presidential" not in used or (y - yb) % 4 == 0)]
    up = tot = 0
    for y in years:
        a = f"{y - span}{a_ym[4:]}"; b = f"{y}{b_ym[4:]}"
        if a in S.idx and b in S.idx and S.idx[b] < len(S.d):
            up += int(S.y[S.idx[b]] > S.y[S.idx[a]]); tot += 1
    return up, tot, ("same year of the presidential term" if "presidential" in used else "all years")


def year_rule(key, a_ym, b_ym):
    if key not in US:
        return None
    ya, yb, mb = int(a_ym[:4]), int(b_ym[:4]), int(b_ym[5:7])
    if ya % 4 == 2 and int(a_ym[5:7]) >= 10:
        return "4-year low: the 12 months after a midterm-year October rose 19 of 19 times since 1950"
    if yb % 4 == 3 and mb <= 7:
        return "Pre-election year Jan–Jul: rose 19 of 19 times since 1950"
    return None


def signal(v, rec, rule):
    ups = sum(1 for x in v.values() if x > 0); dns = sum(1 for x in v.values() if x < 0); n = len(v)
    up_rate = rec[0] / rec[1] if rec[1] else .5
    if n and ups == n and (rule or up_rate >= .75):
        return "Strong buy"
    if ups > n / 2 and up_rate >= .65:
        return "Buy"
    if n and dns == n and (1 - up_rate) >= .65:
        return "Sell"
    if dns > n / 2:
        return "Hold" if rule else "Caution"
    return "Hold"


def months_up(S, years=30):
    """for each calendar month: % of the last `years` years in which the price (or level) rose"""
    out = []
    for m in range(1, 13):
        up = tot = 0
        for y in range(NOW.year - years, NOW.year):
            a, c = f"{y if m > 1 else y - 1}-{(m - 1 or 12):02d}", f"{y}-{m:02d}"
            if a in S.idx and c in S.idx:
                up += int(S.y[S.idx[c]] > S.y[S.idx[a]]); tot += 1
        out.append(round(up / tot * 100) if tot else None)
    return out


def build(key, name, unit, loader, lg, dkey):
    if not have(NEEDS[key]):
        return None
    sr = loader()
    sr = [x for x in sr if x[1] > 0 or not lg]
    full = [x for x in sr if x[0] < CUR]
    if len(full) < 180:
        return None
    S = sc.Series([d for d, _ in full], [v for _, v in full], log=lg)
    first = int(S.d[0][:4])
    start = max(1950, first + 12)
    rows = sc.backtest(S, COMPS, start=start)
    tested = []
    for k, (label, _) in COMPS.items():
        s = sc.score(rows[k])
        if s["hit"] is None:
            continue
        s90 = sc.score(rows[k], 1990)
        tested.append(dict(k=k, name=label, hit=round(s["hit"] * 100), n=s["n"], since=start,
                           hit90=round(s90["hit"] * 100) if s90["hit"] else None, ok=sc.passes(s)))
    tested.sort(key=lambda t: (-t["ok"], -t["hit"]))
    # walk-forward record of the combined forecast
    comp = sc.backtest_composite(S, COMPS, rows, start=start + 15)
    ch, cn = sum(r[1] for r in comp), sum(r[2] for r in comp)
    # forecast made at ORIGIN using only records from years before this year
    if ORIGIN not in S.idx:                          # gap in the data around last December
        return dict(key=key, name=name, unit=unit, log=lg, tested=[], used=[], used_names=[], comp_record=(None, 0, 0),
                    gap=True, last_full=S.d[-1], actual=[x for x in sr if x[0] >= f"{NOW.year - 1}-01"], months_up=months_up(S))
    oi = S.idx[ORIGIN]
    skill = {k: sc.score([r for r in rows[k] if r[0] <= NOW.year - 1]) for k in COMPS}
    H = (int(END[:4]) - int(ORIGIN[:4])) * 12 + int(END[5:7]) - int(ORIGIN[5:7])
    path, used = sc.composite_path(S, oi, COMPS, skill, H)
    info = False
    if path is None:                                  # nothing passed: build the line from the two best-tested
        best = [t["k"] for t in tested[:2]]          # cycles, shown only as "for information, not reliable"
        forced = {k: dict(hit=max(skill[k]["hit"] or .51, .56), n=99, p=0) for k in best}
        path, _ = sc.composite_path(S, oi, {k: COMPS[k] for k in best}, forced, H)
        info = True
    months = [sc.ym_add(ORIGIN, h) for h in range(1, H + 1)]
    res = dict(key=key, name=name, unit=unit, log=lg, tested=tested, used=used,
               used_names=[COMPS[k][0] for k in used],
               comp_record=(round(ch / cn * 100) if cn else None, cn, len(comp)), months_up=months_up(S))
    # actual line: from Jan of the year before ORIGIN's year
    a0 = f"{ORIGIN[:4]}-01"
    res["actual"] = [(d, v) for d, v in sr if d >= a0]
    dl = daily_last(dkey) if dkey else None
    if dl:
        res["live"] = dict(date=dl[0], value=dl[1])
    if path is None:
        res["signal_now"] = None
        return res
    res["info"] = info
    res["months"] = months
    res["path"] = [round(float(x), 4) for x in path]
    wv = []
    for a, bb, s in sc.waves(np.array(path)):          # join neighbouring waves in the same direction
        if wv and wv[-1][2] == s:
            wv[-1] = (wv[-1][0], bb, s)
        else:
            wv.append((a, bb, s))
    res["waves"] = [(months[a - 1] if a else ORIGIN, months[b - 1], s) for a, b, s in wv]
    # score the waves that are already over (forecast vs actual)
    done = []
    for a, b, s in wv:
        fa = months[a - 1] if a else ORIGIN; fb = months[b - 1]
        if fb < CUR and fa in S.idx and fb in S.idx:
            act = S.y[S.idx[fb]] - S.y[S.idx[fa]]
            done.append(dict(frm=fa, to=fb, fc=s, ok=bool(np.sign(act) == s), act=round(float(act * (100 if lg else 1)), 1)))
    res["checked"] = done
    # signal windows: waves that end after the last complete month
    last = S.d[-1]
    wins = []
    for a, b, s in wv:
        fa = months[a - 1] if a else ORIGIN; fb = months[b - 1]
        if fb <= last:
            continue
        fa_eff = max(fa, last)
        ai = months.index(fa_eff) + 1 if fa_eff in months else 0
        v = votes(S, oi, used, ai, b, H)
        rec = analog_record(S, used, fa_eff, fb, max(start, 1950) if key in US else start - 12)
        rule = year_rule(key, fa_eff, fb)
        wins.append(dict(frm=sc.ym_add(fa_eff, 1), to=fb, dir=s, votes=v, rec=rec[:2], basis=rec[2],
                         rule=rule, signal=signal(v, rec, rule)))
    merged_w = []
    for w in wins:                                   # join neighbours with the same signal
        if merged_w and merged_w[-1]["signal"] == w["signal"] and merged_w[-1]["rule"] == w["rule"]:
            p = merged_w[-1]
            p["to"] = w["to"]; p["votes"] = {k: (p["votes"][k] if p["votes"][k] == w["votes"][k] else 0) for k in p["votes"]}
            p["rec"] = analog_record(S, used, sc.ym_add(p["frm"], -1), p["to"], max(start, 1950) if key in US else start - 12)[:2]
        else:
            merged_w.append(w)
    wins = merged_w
    cr = res["comp_record"]
    res["reliable"] = bool(not info and cr[0] is not None and cr[1] >= 30 and cr[0] >= 55)
    res["windows"] = wins
    res["signal_now"] = wins[0] if wins and res["reliable"] else None
    return res


def main():
    out = {}
    for m in MARKETS:
        try:
            r = build(*m)
        except Exception as e:  # noqa: BLE001
            print("  ", m[0], "skipped:", e)
            r = None
        if r:
            out[m[0]] = r
            sn = r.get("signal_now")
            print(f"  {m[1]:22} cycles used: {', '.join(r['used_names']) or 'none'}" + (f" | now: {sn['signal']}" if sn else " | no reliable signal") + f" | combined record {r['comp_record']}")
    json.dump(dict(built=str(NOW), origin=ORIGIN, end=END, markets=out), open("work/sig.json", "w"), indent=0)


if __name__ == "__main__":
    main()
