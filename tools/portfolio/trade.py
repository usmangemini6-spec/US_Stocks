"""
trade.py - run by the GitHub "Portfolio" workflow when the locked page sends a Buy / Sell / Close.

The request arrives encrypted (workflow input "request", passed in the REQUEST environment variable)
and is decrypted with the PORTFOLIO_PASSWORD repository secret, so the public Actions log never shows
what was traded. Rules are checked again here (portfolio_core.apply_request); the result is stored
with the request id so the page can show "Done" or the reason it was not done.
Prints nothing about the trade itself. Exit code is always 0.
"""
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import portfolio_core as pc  # noqa: E402


def main():
    pw, blob = os.environ.get("PORTFOLIO_PASSWORD", ""), os.environ.get("REQUEST", "").strip()
    if not pw:
        print("PORTFOLIO_PASSWORD secret not set.")
        return 0
    ledger = pc.load_ledger(pw)
    old = pc.read_page_state(pw) or {}
    req = None
    if blob:
        try:
            req = pc.decrypt(blob, pw)
        except Exception:
            print("Request could not be read (wrong password on the page?) - ignored.")
    extra = [str(req.get("t", "")).upper()] if isinstance(req, dict) else []
    px = pc.fetch_prices(ledger, cache=old.get("px"), log=lambda *a: None, extra=extra)
    if isinstance(req, dict):
        ok, _msg = pc.apply_request(ledger, req, px, date.today().isoformat())
        pc.save_trades(ledger, pw)
        print("Request processed:", "done" if ok else "not done (reason shown on the page)")
        if ok:
            px = pc.fetch_prices(ledger, cache=px, log=lambda *a: None)
    state = pc.build_state(ledger, px)
    state["px"] = px
    pc.write_page_state(state, pw)
    print("Portfolio page rebuilt.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Portfolio: not updated ({type(e).__name__})")
        sys.exit(0)
