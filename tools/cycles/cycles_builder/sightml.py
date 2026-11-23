"""HTML for the cycle signals: signal now, actual-vs-forecast chart, signal table, tested cycles."""
import json, html
SIG = json.load(open("work/sig.json", encoding="utf-8"))
MK = SIG["markets"]
MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
COL = {"Strong buy": "#15803d", "Buy": "#4d7c0f", "Hold": "#6b7280", "Caution": "#c2410c", "Sell": "#b91c1c", "No signal": "#9ca3af"}
ICON = {"Strong buy": "🟢", "Buy": "🟢", "Hold": "⚪", "Caution": "🟠", "Sell": "🔴"}


def mlab(ym, short=False):
    return f"{MON[int(ym[5:7]) - 1]} {ym[2:4] if short else ym[:4]}"


def per(a, b):
    if a == b:
        return mlab(a)
    return f"{MON[int(a[5:7]) - 1]}{' ' + a[:4] if a[:4] != b[:4] else ''} – {mlab(b)}"


def fmt(v, r):
    if not r["log"]:
        return f"{v:.2f}%"
    return f"{v:,.0f}" if v >= 1000 else f"{v:,.2f}"


def badge(s):
    return f'<span class="sg" style="background:{COL[s]}">{s}</span>'


CSS = """<style>
.sg{display:inline-block;color:#fff;font-weight:700;font-size:13px;border-radius:999px;padding:2px 10px;white-space:nowrap}
.now{display:flex;gap:12px;align-items:center;flex-wrap:wrap;background:#fdf8f1;border:1px solid #e7dcc8;border-radius:10px;padding:12px 16px;margin:8px 0 14px;font-size:16px}
.now .sg{font-size:15px;padding:4px 14px}.none{background:#f8f8f6}
.vt{font-size:17px;text-align:center}.vt.up{color:#15803d}.vt.dn{color:#b91c1c}.vt.fl{color:#9ca3af}
.cy svg{width:100%;height:auto;display:block}.cy{margin:6px 0 4px}
.howto{background:#fff;border:1px solid #e7dcc8;border-radius:12px;padding:14px 18px;margin:10px 0}
.howto table{margin-top:6px}.facts{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 10px}.facts div{flex:1;min-width:170px;padding:10px 14px}.facts span{display:block;font-size:12px;color:#6b7280}.facts b{font-size:20px}.legend{font-size:13px;color:#6b7280}
td.rule{font-size:13px;color:#374151}
</style>"""

HOWTO = """<div class="howto"><b>How to read the signals</b>
<p class="small" style="margin:4px 0 6px">Each market uses only the cycles that passed our backtest for that market (each forecast built from earlier data only, then checked against what happened). The more of them agree, the stronger the signal. Cycles give <b>timing and odds, not guarantees or price targets</b>.</p>
<div class="scroll"><table><thead><tr><th>Signal</th><th>When</th><th>What it suggests</th></tr></thead><tbody>
<tr><td>""" + badge("Strong buy") + """</td><td>All tested cycles point up, plus a year rule or a strong past record (75%+)</td><td>Buy or add</td></tr>
<tr><td>""" + badge("Buy") + """</td><td>Most cycles up and the period rose in 65%+ of past years</td><td>Buy dips</td></tr>
<tr><td>""" + badge("Hold") + """</td><td>Cycles disagree, or the record is close to normal</td><td>Keep, no new action</td></tr>
<tr><td>""" + badge("Caution") + """</td><td>Most cycles point down, but the record is not strong enough to sell</td><td>Don't add; protect profits</td></tr>
<tr><td>""" + badge("Sell") + """</td><td>All cycles down and the period fell in 65%+ of past years</td><td>Reduce or sell</td></tr>
</tbody></table></div></div>"""


def chart(r):
    act = [a for a in r["actual"]]
    months = sorted(set([d for d, _ in act] + r.get("months", [])))
    if not months:
        return ""
    x0 = months[0]
    idx = {m: i for i, m in enumerate(months)}
    W, L, R = 1000, 64, 20
    T1, H1, T2, H2 = 22, 190, 268, 130
    n = len(months)
    X = lambda i: L + (W - L - R) * i / max(n - 1, 1)
    vals = [v for _, v in act] + ([r["live"]["value"]] if r.get("live") else [])
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * .08 or 1
    lo, hi = lo - pad, hi + pad
    Y1 = lambda v: T1 + H1 * (1 - (v - lo) / (hi - lo))
    g = [f'<svg viewBox="0 0 {W} {T2 + H2 + 40}" role="img" aria-label="{html.escape(r["name"])}: actual price and cycle forecast">']
    g.append(f'<text x="{L}" y="14" font-size="13" font-weight="600" fill="#1f2937">Actual {html.escape(r["name"])}</text>')
    for k in range(3):
        v = lo + (hi - lo) * (k + .5) / 3
        g.append(f'<line x1="{L}" x2="{W - R}" y1="{Y1(v):.1f}" y2="{Y1(v):.1f}" stroke="#eee7da"/><text x="{L - 6}" y="{Y1(v) + 4:.1f}" font-size="11" text-anchor="end" fill="#6b7280">{fmt(v, r)}</text>')
    path = r.get("path")
    if path:
        info = r.get("info") or not r.get("reliable")
        ttl = (f"Cycle pattern, for information only: NOT reliable (made from data up to {mlab(SIG['origin'])})" if info
               else f"Cycle forecast (made from data up to {mlab(SIG['origin'])})")
        g.append(f'<text x="{L}" y="{T2 - 8}" font-size="13" font-weight="600" fill="{"#9ca3af" if info else "#1f2937"}">{ttl}</text>')
        for a, b, s in r["waves"]:
            xa, xb = X(idx.get(a, 0)), X(idx[b])
            fill = ("#f3f4f6" if s > 0 else "#fafafa") if info else ("#e3f1e5" if s > 0 else "#fbe5e3")
            g.append(f'<rect x="{xa:.1f}" y="{T2}" width="{xb - xa:.1f}" height="{H2}" fill="{fill}"/>')
        plo, phi = min(path + [0]), max(path + [0])
        Y2 = lambda v: T2 + 8 + (H2 - 16) * (1 - (v - plo) / ((phi - plo) or 1))
        pts = [(X(idx[r["months"][0]]) - (X(1) - X(0)), Y2(0))] + [(X(idx[m]), Y2(v)) for m, v in zip(r["months"], path)]
        if SIG["origin"] in idx:
            pts[0] = (X(idx[SIG["origin"]]), Y2(0))
        g.append(f'<polyline fill="none" stroke="{"#9ca3af" if info else "#a8650a"}" stroke-width="2.4"{" stroke-dasharray=\'6 5\'" if info else ""} points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + '"/>')
        lastx, row = -999, 0
        for a, b, s in r["waves"][:-1]:
            xb = X(idx[b])
            c = "#9ca3af" if info else ("#b91c1c" if s > 0 else "#15803d")
            row = (row + 1) % 2 if xb - lastx < 90 else 0
            lastx = xb
            g.append(f'<line x1="{xb:.1f}" x2="{xb:.1f}" y1="{T1}" y2="{T2 + H2 + 4 + row * 15}" stroke="{c}" stroke-dasharray="4 4" stroke-width="1.3"/>'
                     f'<text x="{xb:.1f}" y="{T2 + H2 + 16 + row * 15}" font-size="12" font-weight="600" text-anchor="middle" fill="{c}">{"High" if s > 0 else "Low"} {mlab(b, True)}</text>')
    pa = [(X(idx[d]), Y1(v)) for d, v in act]
    g.append('<polyline fill="none" stroke="#1f5f2a" stroke-width="2.4" points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pa) + '"/>')
    fcdir = {}
    if path:
        for a, b, s in r["waves"]:
            for m in r["months"]:
                if a < m <= b:
                    fcdir[m] = "rising" if s > 0 else "falling"
    for (d, v), (x, y) in zip(act, pa):
        tip = f"{mlab(d)} · Actual: {fmt(v, r)}" + (f" · Forecast: {fcdir[d]}" if d in fcdir else "")
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="transparent"><title>{tip}</title></circle>')
    last = act[-1][0]
    xt = X(idx[last])
    g.append(f'<line x1="{xt:.1f}" x2="{xt:.1f}" y1="{T1}" y2="{T2 + H2}" stroke="#374151" stroke-width="1"/><text x="{xt + 5:.1f}" y="{T1 + 10}" font-size="12" font-weight="600" fill="#374151">Today</text>')
    if r.get("live"):
        lv = r["live"]
        g.append(f'<circle cx="{xt:.1f}" cy="{Y1(lv["value"]):.1f}" r="5" fill="#dc2626"/><text x="{xt + 8:.1f}" y="{Y1(lv["value"]) + 4:.1f}" font-size="12" font-weight="600" fill="#dc2626">{fmt(lv["value"], r)} ({lv["date"][8:]}/{lv["date"][5:7]})</text>')
    for m in months:
        if m[5:7] == "01":
            g.append(f'<text x="{X(idx[m]):.1f}" y="{T1 + H1 + 16}" font-size="11" text-anchor="middle" fill="#6b7280">{m[:4]}</text>')
    g.append("</svg>")
    return '<div class="cy">' + "".join(g) + "</div>"


def facts(r):
    act = r["actual"]
    if not act:
        return ""
    last = r["live"]["value"] if r.get("live") else act[-1][1]
    when = r["live"]["date"] if r.get("live") else act[-1][0]
    m = dict(act)
    yago = m.get(f"{int(act[-1][0][:4]) - 1}{act[-1][0][4:]}")
    hi = max(v for _, v in act)
    if r["log"]:
        ch = f"{(last / yago - 1) * 100:+.1f}%" if yago else "—"
        dh = f"{(last / hi - 1) * 100:+.1f}%"
    else:
        ch = f"{last - yago:+.2f} pts" if yago is not None else "—"
        dh = f"{last - hi:+.2f} pts"
    cell = lambda a, b: f'<div><span>{a}</span><b>{b}</b></div>'
    return ('<div class="facts">' + cell(f"Latest ({when[8:10] + '/' if len(when) > 7 else ''}{when[5:7]}/{when[:4]})", fmt(last, r))
            + cell("Change over 12 months", ch) + cell("From the high of the chart period", dh) + '</div>')


def month_table(r):
    mu = r.get("months_up") or []
    if not any(x is not None for x in mu):
        return ""
    cells = "".join(f'<td class="n" style="background:{"#e3f1e5" if (x or 0) >= 60 else "#fbe5e3" if x is not None and x <= 40 else "#fff"}">{x if x is not None else "—"}%</td>' for x in mu)
    return (f'<div class="scroll"><table><thead><tr><th>Month</th>' + "".join(f'<th class="n">{m}</th>' for m in MON) + '</tr></thead>'
            f'<tbody><tr><td>Rose in</td>{cells}</tr></tbody></table></div>'
            '<p class="small">How often the price (or level) rose in each calendar month over the last 30 years. Green 60%+, red 40% or less. A history fact, not a forecast.</p>')


def tested_table(r):
    rows = [t for t in r["tested"] if t["ok"]] + [t for t in r["tested"] if not t["ok"]][:3]
    body = "".join(f'<tr><td>{html.escape(t["name"])}</td><td class="n">{t["hit"]}%</td><td class="n">{t["hit90"] if t["hit90"] is not None else "—"}{"%" if t["hit90"] is not None else ""}</td><td class="n">{t["n"]}</td>'
                   f'<td>{"✅ Used" if t["ok"] else "Not used (no edge)"}</td></tr>' for t in rows)
    since = r["tested"][0]["since"] if r["tested"] else ""
    cr = r["comp_record"]
    comb = (f'Combined forecast, tested year by year: <b>{cr[0]}% of rises and falls right</b> ({cr[1]} waves, {cr[2]} years).' if cr[0] is not None
            else "Combined forecast: not enough history to test it yet.")
    return (f'<details><summary><b>Which cycles count here</b> (how often each called rises and falls right; a coin toss is 50%)</summary>'
            f'<div class="scroll"><table><thead><tr><th>Cycle</th><th class="n">Right since {since}</th><th class="n">Since 1990</th><th class="n">Waves tested</th><th>Status</th></tr></thead><tbody>{body}</tbody></table></div>'
            f'<p class="small">{comb}</p></details>')


def section(key, title=None):
    r = MK.get(key)
    if not r:
        return ""
    name = title or r["name"]
    out = [f'<section class="band mk" id="sig-{key}"><div class="wrap"><h2>{html.escape(name)}</h2>']
    out.append(facts(r))
    if r.get("gap"):
        out.append(f'<div class="now none">{badge("No signal")}<span><b>Data gap</b>: the monthly data stops at {mlab(r["last_full"])}, so the cycles cannot be tested. '
                   f'Add the missing history as cycles_data\\manual\\{key}.csv (e.g. downloaded from investing.com).</span></div></div></section>')
        return "".join(out)
    sn = r.get("signal_now")
    if sn:
        out.append(f'<div class="now">{badge(sn["signal"])}<span><b>{per(sn["frm"], sn["to"])}</b>: {sum(1 for v in sn["votes"].values() if v > 0)} of {len(sn["votes"])} cycles up; '
                   f'rose in {sn["rec"][0]} of {sn["rec"][1]} comparable years.</span></div>')
    else:
        cr = r["comp_record"]
        why = ("none of its cycles passed our backtest" if not r["used"] else
               f"its cycles tested together called only {cr[0]}% of rises and falls right" if cr[0] is not None else
               "there is not enough history to verify its cycles")
        out.append(f'<div class="now none">{badge("No signal")}<span><b>No reliable cycle signal</b>: {why}. The grey line below is shown for information only; we give no buy or sell signal.</span></div>')
        if r.get("path"):
            out.append(chart(r))
            out.append('<p class="legend">Top: actual price (month-end; red dot = latest close). Bottom (grey): the strongest cycle pattern we found, which did NOT pass our backtest.</p>')
    if r.get("path") and r.get("reliable"):
        out.append(chart(r))
        out.append('<p class="legend">Top: actual price (month-end; red dot = latest close). Bottom: our cycle forecast; green = rise expected, red = fall expected. '
                   'Left of "Today" is a real test: the forecast was made before those months happened.</p>')
        ck = r.get("checked") or []
        if ck:
            ok = sum(1 for c in ck if c["ok"])
            items = "; ".join(f'{per(c["frm"], c["to"])} forecast {"rise" if c["fc"] > 0 else "fall"}, actual {c["act"]:+.1f}{"%" if r["log"] else " pts"} {"✅" if c["ok"] else "❌"}' for c in ck)
            out.append(f'<p class="small"><b>Forecast check this year: {ok} of {len(ck)} right.</b> {items}.</p>')
        heads = "".join(f'<th style="text-align:center">{html.escape(MKN(k))}</th>' for k in r["used"])
        rows = []
        for w in r["windows"]:
            vt = "".join(f'<td class="vt {"up" if w["votes"][k] > 0 else "dn" if w["votes"][k] < 0 else "fl"}">{"▲" if w["votes"][k] > 0 else "▼" if w["votes"][k] < 0 else "–"}</td>' for k in r["used"])
            rows.append(f'<tr><td><b>{per(w["frm"], w["to"])}</b></td>{vt}<td class="rule">{html.escape(w["rule"]) if w["rule"] else "—"}</td>'
                        f'<td class="n">Up {w["rec"][0]} of {w["rec"][1]}</td><td>{badge(w["signal"])}</td></tr>')
        basis = r["windows"][0]["basis"] if r["windows"] else ""
        out.append(f'<div class="scroll"><table><thead><tr><th>Period</th>{heads}<th>Year rule</th><th class="n">Past record*</th><th>Signal</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
                   f'<p class="small">*How often the price rose in the same period of past years ({basis}). ▲ cycle points up, ▼ down, – flat.</p>')
    out.append(month_table(r))
    out.append(tested_table(r))
    out.append("</div></section>")
    return "".join(out)


def MKN(k):
    return {"presidential": "Presidential", "seasonal": "Within-year", "decennial": "Decennial", "y20": "20-year"}.get(k, f"{k[1:]}-month")


def summary():
    rows = []
    for k, page in (("sp", "us-stocks.html"), ("nasdaq", "us-stocks.html"), ("dji", "us-stocks.html"), ("tasi", "tasi.html"), ("psx", "psx.html"),
                    ("gold", "gold.html"), ("silver", "silver.html"), ("oil", "oil.html"), ("home", "real-estate.html"),
                    ("cpi", "rates.html"), ("us10y", "rates.html"), ("fedfunds", "rates.html")):
        r = MK.get(k)
        if not r:
            continue
        sn = r.get("signal_now")
        last = r["live"]["value"] if r.get("live") else r["actual"][-1][1]
        nxt = r["windows"][1] if sn and len(r["windows"]) > 1 else None
        rows.append(f'<tr><td><a href="{page}#sig-{k}">{html.escape(r["name"])}</a></td><td class="n">{fmt(last, r)}</td>'
                    f'<td>{badge(sn["signal"]) + " " + per(sn["frm"], sn["to"]) if sn else "No reliable signal"}</td>'
                    f'<td>{badge(nxt["signal"]) + " " + per(nxt["frm"], nxt["to"]) if nxt else "—"}</td>'
                    f'<td>{", ".join(MKN(x) for x in r["used"]) if sn else "—"}</td></tr>')
    return ('<div class="scroll"><table><thead><tr><th>Market</th><th class="n">Latest</th><th>Signal now</th><th>Next</th><th>Cycles that count</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def miners_html():
    """10-year chart of halal gold miners vs gold and silver, plus how much the miners move per 1% move in the metal."""
    from cdata import have, series
    keys = [("gld", "Gold (GLD)", "#374151"), ("slv", "Silver (SLV)", "#0b5fa5"), ("aem", "AEM", "#1f5f2a"), ("drd", "DRD", "#a8650a")]
    data = {}
    for k, n, c in keys:
        if have(k):
            data[k] = dict(series(k))
    if "gld" not in data or len(data) < 3:
        return ""
    end = max(max(v) for v in data.values())
    start = f"{int(end[:4]) - 10}{end[4:]}"
    months = sorted(m for m in data["gld"] if m >= start)
    W, L, R, T, H = 1000, 56, 120, 16, 260
    norm = {k: [(m, data[k][m] / data[k][months[0]] * 100) for m in months if m in data[k] and months[0] in data[k]] for k in data}
    allv = [v for s in norm.values() for _, v in s]
    import math
    lo, hi = math.log(min(allv)), math.log(max(allv))
    X = lambda i: L + (W - L - R) * i / (len(months) - 1)
    Y = lambda v: T + H * (1 - (math.log(v) - lo) / (hi - lo))
    idx = {m: i for i, m in enumerate(months)}
    g = [f'<svg viewBox="0 0 {W} {T + H + 30}" role="img" aria-label="Gold miners vs gold and silver, 10 years">']
    for v in (50, 100, 200, 400, 800):
        if min(allv) <= v <= max(allv):
            g.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#eee7da"/><text x="{L - 6}" y="{Y(v) + 4:.1f}" font-size="11" text-anchor="end" fill="#6b7280">{v}</text>')
    for m in months:
        if m[5:7] == "01" and int(m[:4]) % 2 == 0:
            g.append(f'<text x="{X(idx[m]):.1f}" y="{T + H + 16}" font-size="11" text-anchor="middle" fill="#6b7280">{m[:4]}</text>')
    lab = []
    for k, n, c in keys:
        if k not in norm or not norm[k]:
            continue
        pts = " ".join(f"{X(idx[m]):.1f},{Y(v):.1f}" for m, v in norm[k])
        g.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.2" points="{pts}"><title>{n}</title></polyline>')
        lab.append([Y(norm[k][-1][1]), n, c, norm[k][-1][1]])
    lab.sort()
    for i in range(1, len(lab)):
        lab[i][0] = max(lab[i][0], lab[i - 1][0] + 15)
    for y, n, c, v in lab:
        g.append(f'<text x="{W - R + 6}" y="{y + 4:.1f}" font-size="12" font-weight="600" fill="{c}">{n} {v:,.0f}</text>')
    g.append("</svg>")
    # sensitivity: average miner move per 1% move in the metal (monthly, 10 years)
    def beta(a, b):
        ra = [data[a][months[i]] / data[a][months[i - 1]] - 1 for i in range(1, len(months)) if months[i] in data[a] and months[i - 1] in data[a] and months[i] in data[b] and months[i - 1] in data[b]]
        rb = [data[b][months[i]] / data[b][months[i - 1]] - 1 for i in range(1, len(months)) if months[i] in data[a] and months[i - 1] in data[a] and months[i] in data[b] and months[i - 1] in data[b]]
        if len(ra) < 24:
            return None
        mb, ma = sum(rb) / len(rb), sum(ra) / len(ra)
        cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)); var = sum((y - mb) ** 2 for y in rb)
        return cov / var if var else None
    rows = []
    for k, n in (("aem", "AEM"), ("drd", "DRD")):
        if k in data:
            bg = beta(k, "gld"); bs = beta(k, "slv") if "slv" in data else None
            tot = norm[k][-1][1] / 100 - 1 if norm.get(k) else None
            rows.append(f'<tr><td><b>{n}</b></td><td class="n">{bg:.1f}%</td><td class="n">{bs:.1f}%</td><td class="n">{tot * 100:+.0f}%</td></tr>' if bg and bs and tot is not None else "")
    tg = norm["gld"][-1][1] - 100
    ts = norm["slv"][-1][1] - 100 if norm.get("slv") else None
    table = ('<div class="scroll"><table><thead><tr><th>Miner</th><th class="n">Move per 1% move in gold</th><th class="n">Move per 1% move in silver</th><th class="n">Change over 10 years</th></tr></thead><tbody>'
             + "".join(rows) + f'<tr><td>Gold (GLD)</td><td class="n">—</td><td class="n">—</td><td class="n">{tg:+.0f}%</td></tr>'
             + (f'<tr><td>Silver (SLV)</td><td class="n">—</td><td class="n">—</td><td class="n">{ts:+.0f}%</td></tr>' if ts is not None else "") + '</tbody></table></div>')
    return ('<h3 style="margin-top:22px">Miners vs metal: last 10 years</h3><div class="cy">' + "".join(g) + '</div>'
            f'<p class="legend">All lines start at 100 on {mlab(months[0])} (log scale), monthly closes to {mlab(months[-1])}.</p>' + table +
            '<p class="small">Measured from monthly moves over 10 years: a miner that moves about 2% for each 1% move in gold gains more in rallies and loses more in falls.</p>')
