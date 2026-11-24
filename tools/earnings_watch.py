r"""
earnings_watch.py - runs daily on GitHub (workflow earnings_watch.yml).

1. Reads ba_dates.json (written by the PC on every deploy): for each Screener stock, the date of its
   business analysis and whether it is a full written analysis.
2. Reads the US earnings calendar (Nasdaq) for the last 10 days.
3. A stock is "pending" when it reported after the date of its analysis.
4. Writes earnings_pending.json (the PC daily task reads it) and keeps one GitHub issue
   "Earnings to update" open while anything is pending: new stocks are added as a comment, so
   GitHub emails you. The issue is closed when everything is updated.
"""
import json, os, sys, time, urllib.request, urllib.error
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = date.today()
LOOKBACK = 10
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}
norm = lambda s: s.strip().upper().replace(".", "-").replace("/", "-")


def get_json(url, headers, data=None, method=None):
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read()
        return json.loads(b) if b else {}


def calendar(day):
    for attempt in range(3):
        try:
            j = get_json(f"https://api.nasdaq.com/api/calendar/earnings?date={day.isoformat()}", UA)
            rows = ((j.get("data") or {}).get("rows")) or []
            return [(norm(r["symbol"]), r.get("time", "")) for r in rows if r.get("symbol")]
        except Exception as e:  # noqa: BLE001
            print(f"  {day}: try {attempt + 1} failed: {e}")
            time.sleep(5)
    return None


def main():
    f = os.path.join(ROOT, "ba_dates.json")
    if not os.path.exists(f):
        print("ba_dates.json not found yet: run DEPLOY_TO_GITHUB.bat once on the PC.")
        return
    ba = json.load(open(f, encoding="utf-8"))
    ba = {norm(k): v for k, v in ba.items()}
    pending, failed = {}, []
    for k in range(LOOKBACK, 0, -1):                      # reports up to yesterday (US results are out by now)
        d = TODAY - timedelta(days=k)
        if d.weekday() >= 5:
            continue
        rows = calendar(d)
        if rows is None:
            failed.append(d.isoformat())
            continue
        for sym, tm in rows:
            a = str(ba.get(sym, [""])[0])[:10]
            # analysed before the report day; or on the same day before a pre-market report (Riyadh morning run)
            if sym in ba and (a < d.isoformat() or (a == d.isoformat() and "pre-market" in tm)):
                pending[sym] = dict(ticker=sym, reported=d.isoformat(), analysed=str(ba[sym][0])[:10], full=bool(ba[sym][1]))
    out = dict(checked=TODAY.isoformat(), failed_days=failed,
               auto=sorted((p for p in pending.values() if not p["full"]), key=lambda p: (p["reported"], p["ticker"])),
               full=sorted((p for p in pending.values() if p["full"]), key=lambda p: (p["reported"], p["ticker"])))
    with open(os.path.join(ROOT, "earnings_pending.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"Pending: {len(out['auto'])} automatic, {len(out['full'])} full analyses; calendar failed for {failed or 'no days'}")
    issue(out)


def issue(out):
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("No GitHub token: issue not updated (local run).")
        return
    H = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "earnings-watch"}
    api = f"https://api.github.com/repos/{repo}"
    label = "earnings-pending"
    found = get_json(f"{api}/issues?state=open&labels={label}&per_page=5", H)
    cur = found[0] if found else None
    tick = [p["ticker"] for p in out["auto"] + out["full"]]
    if not tick:
        if cur:
            get_json(f"{api}/issues/{cur['number']}/comments", H, json.dumps({"body": "All recent earnings are updated. Closing."}).encode(), "POST")
            get_json(f"{api}/issues/{cur['number']}", H, json.dumps({"state": "closed"}).encode(), "PATCH")
            print("Issue closed.")
        return
    line = lambda p: f"| {p['ticker']} | {p['reported']} | {p['analysed']} |"
    body = ("Stocks that reported earnings after their business analysis. Updated daily by the earnings watch.\n\n"
            f"**Automatic analysis ({len(out['auto'])})** - your PC's daily task updates these when the PC is on "
            "(or run RUN_BA_RECENT_EARNINGS.bat):\n\n| Ticker | Reported | Analysis date |\n|---|---|---|\n"
            + "\n".join(line(p) for p in out["auto"]) +
            f"\n\n**Full written analysis ({len(out['full'])})** - ask Claude: `/business-analysis "
            + " ".join(p["ticker"] for p in out["full"]) + "`\n\n| Ticker | Reported | Analysis date |\n|---|---|---|\n"
            + "\n".join(line(p) for p in out["full"]) + f"\n\nChecked {out['checked']}."
            + (f" Calendar could not be read for: {', '.join(out['failed_days'])}." if out["failed_days"] else ""))
    if not cur:
        get_json(f"{api}/issues", H, json.dumps({"title": "Earnings to update", "body": body, "labels": [label]}).encode(), "POST")
        print("Issue opened (GitHub emails you).")
        return
    old = cur.get("body") or ""
    new = [t for t in tick if f"| {t} |" not in old]
    get_json(f"{api}/issues/{cur['number']}", H, json.dumps({"body": body}).encode(), "PATCH")
    if new:
        get_json(f"{api}/issues/{cur['number']}/comments", H, json.dumps({"body": "New earnings to update: " + ", ".join(new)}).encode(), "POST")
        print("Issue updated; comment added for new stocks (GitHub emails you).")
    else:
        print("Issue updated (no new stocks).")


if __name__ == "__main__":
    main()
