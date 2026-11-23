r"""
salgo_cycle.py - SAlgo Cycle Forecast engine (our own model).

Idea (same building blocks Larry Williams uses, but every block is tested before it is used):
  * Calendar patterns  : seasonal, presidential (4-yr), decennial (10-yr), 20-yr, 60-yr
  * Fixed-length cycles: the market's price stacked every P months (e.g. 24, 42, 54, 84, 108)
  * Each pattern is DE-TRENDED (the market's normal drift is removed), so it can say
    "weaker than normal" or "down", not only "up".
  * WALK-FORWARD BACKTEST: a forecast for year Y is built only from data up to Dec of Y-1.
    Every rise/fall wave it predicts is scored against what really happened (vs normal drift).
  * A pattern is USED only if it beats a coin toss with enough cases (hit >= 55%, n >= 30,
    binomial p <= 0.10). The combined forecast weights the passed patterns by their edge and
    is itself backtested the same way (it only knows records from earlier years).
Cycles give TIMING (when to expect highs and lows), not size.
"""
import math
import numpy as np

MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


# ---------------------------------------------------------------- helpers
def ym_add(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) + k
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return f"{y:04d}-{m:02d}"


def binom_p(h, n):
    """one-sided p-value: chance of >= h hits out of n by coin toss."""
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(h, n + 1)) / 2 ** n


KEYS = {
    "seasonal":     ("Within-year (seasonal)",     lambda Y, M: M),
    "presidential": ("Presidential 4-year",        lambda Y, M: ((Y - 1953) % 4, M)),
    "decennial":    ("Decennial (year digit)",     lambda Y, M: (Y % 10, M)),
    "y20":          ("20-year (decade + term)",    lambda Y, M: (Y % 20, M)),
    "y60":          ("60-year",                    lambda Y, M: (Y % 60, M)),
}


def fold_key(P):
    return lambda Y, M: ((Y - 1900) * 12 + M - 1) % P


def all_components(fixed=(24, 42, 54, 84, 108, 120)):
    c = dict(KEYS)
    for P in fixed:
        c[f"c{P}"] = (f"{P}-month cycle" + (f" ({P // 12} yr)" if P % 12 == 0 else ""), fold_key(P))
    return c


# ---------------------------------------------------------------- pattern path
class Series:
    def __init__(self, dates, values, log=True):
        self.d = list(dates)
        v = np.asarray(values, float)
        self.y = np.log(v) if log else v
        self.log = log
        self.idx = {d: i for i, d in enumerate(self.d)}

    def chg(self, i, j):
        return self.y[j] - self.y[i]


def pattern_path(S, upto, key, H, min_rep=3):
    """average de-trended monthly change for each slot, from data up to index `upto` (inclusive);
    returns the cumulative path for the next H months and the number of past repeats per month."""
    ch = np.diff(S.y[:upto + 1])
    if len(ch) < 24:
        return None, None
    drift = ch.mean()
    acc = {}
    for k in range(len(ch)):
        Y, M = int(S.d[k + 1][:4]), int(S.d[k + 1][5:7])
        acc.setdefault(key(Y, M), []).append(ch[k] - drift)
    out, reps = [], []
    ym = S.d[upto]
    for h in range(1, H + 1):
        t = ym_add(ym, h)
        v = acc.get(key(int(t[:4]), int(t[5:7])), [])
        reps.append(len(v))
        out.append(float(np.mean(v)) if len(v) >= min_rep else 0.0)
    return np.cumsum(out), reps


def waves(path, min_len=2):
    """rise/fall waves of a path that starts at 0: [(start_month, end_month, +1/-1)]"""
    p = np.concatenate([[0.0], path])
    seg, a = [], 0
    for i in range(1, len(p) - 1):
        if (p[i] - p[i - 1]) * (p[i + 1] - p[i]) < 0 and i - a >= min_len:
            seg.append((a, i, int(np.sign(p[i] - p[a]))))
            a = i
    if len(p) - 1 - a >= 1:
        seg.append((a, len(p) - 1, int(np.sign(p[-1] - p[a]))))
    return [s for s in seg if s[2] != 0]


def normal_drift(S, i, years=10):
    k = years * 12
    if i < k:
        k = i
    return (S.y[i] - S.y[i - k]) / k if k > 0 else 0.0


# ---------------------------------------------------------------- backtest
def backtest(S, comps, start=1950, H=12, origin_month="12"):
    """walk-forward. Returns per component: list of (origin_year, hits, waves) and Dec/1-month tests."""
    res = {k: [] for k in comps}
    for i, d in enumerate(S.d):
        if d[5:7] != origin_month or int(d[:4]) < start - 1 or i + H >= len(S.d):
            continue
        dr = normal_drift(S, i)
        for k, (_, key) in comps.items():
            p, _ = pattern_path(S, i, key, H)
            if p is None:
                continue
            h = n = 0
            for a, b, s in waves(p):
                act = S.chg(i + a, i + b) - dr * (b - a)
                h += int(np.sign(act) == s)
                n += 1
            res[k].append((int(d[:4]) + 1, h, n))
    return res


def score(rows, since=None):
    rows = [r for r in rows if since is None or r[0] >= since]
    h = sum(r[1] for r in rows)
    n = sum(r[2] for r in rows)
    return dict(hit=h / n if n else None, n=n, p=binom_p(h, n), years=len(rows))


def passes(s, min_hit=.55, min_n=30, max_p=.10):
    return s["hit"] is not None and s["hit"] >= min_hit and s["n"] >= min_n and s["p"] <= max_p


def composite_path(S, upto, comps, skill, H):
    """weighted average of the passed patterns (weight = edge over 50%), each scaled to unit size."""
    num, den, used = None, 0.0, []
    for k, (_, key) in comps.items():
        s = skill.get(k)
        if not s or not passes(s):
            continue
        p, _ = pattern_path(S, upto, key, H)
        if p is None:
            continue
        sd = np.std(np.diff(np.concatenate([[0], p]))) or 1e-9
        w = s["hit"] - .5
        num = w * p / sd if num is None else num + w * p / sd
        den += w
        used.append(k)
    if not den:
        return None, []
    return num / den, used


def backtest_composite(S, comps, rows, start=1975, H=12):
    """the combined forecast for year Y only uses pattern records from years before Y."""
    out = []
    for i, d in enumerate(S.d):
        if d[5:7] != "12" or int(d[:4]) < start - 1 or i + H >= len(S.d):
            continue
        Y = int(d[:4]) + 1
        skill = {k: score([r for r in rows[k] if r[0] < Y]) for k in comps}
        p, used = composite_path(S, i, comps, skill, H)
        if p is None:
            continue
        dr = normal_drift(S, i)
        h = n = 0
        for a, b, s in waves(p):
            act = S.chg(i + a, i + b) - dr * (b - a)
            h += int(np.sign(act) == s)
            n += 1
        yr = S.chg(i, i + 12) - dr * 12
        out.append((Y, h, n, int(np.sign(p[-1]) == np.sign(yr)), used))
    return out


# ---------------------------------------------------------------- analog (sweet-spot) counts
def analog_years(key, target_year, first, last):
    return [y for y in range(first, last + 1) if key(y, 1) == key(target_year, 1)]


def window_count(S, years, m_from, m_to, detrend=False):
    """in how many analog years did the market rise from month-end m_from to month-end m_to?"""
    up = tot = 0
    for y in years:
        a = f"{y if m_from > 0 else y - 1}-{(m_from or 12):02d}"
        b = f"{y}-{m_to:02d}"
        if a in S.idx and b in S.idx:
            i, j = S.idx[a], S.idx[b]
            c = S.chg(i, j) - (normal_drift(S, i) * (j - i) if detrend else 0)
            up += int(c > 0)
            tot += 1
    return up, tot
