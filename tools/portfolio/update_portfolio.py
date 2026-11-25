"""
update_portfolio.py - run every weekday by the GitHub workflow (.github/workflows/daily_prices.yml),
right after update_prices.py.

Also run by the "Portfolio" workflow when the PC publishes new data (tools/portfolio/universe.enc).
Reads the encrypted data + trades with the PORTFOLIO_PASSWORD repository secret, downloads the daily
closes (Yahoo first, Stooq if Yahoo fails), applies the automatic target closes for you and the SAlgo
Autopilot, and rebuilds portfolio.html (current menu + encrypted figures). It never changes the
data or trades files. Prints totals only as "updated", never the figures (the Actions log is public).

Exit code is always 0 (a portfolio problem must not stop the daily prices job); problems are printed.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import portfolio_core as pc  # noqa: E402


def main():
    pw = os.environ.get("PORTFOLIO_PASSWORD", "")
    if not pw:
        print("Portfolio: PORTFOLIO_PASSWORD secret not set - skipped.")
        return 0
    if not any(os.path.exists(f) for f in (pc.UNIVERSE, pc.TRADES, pc.LEDGER)):
        print("Portfolio: nothing published yet - skipped.")
        return 0
    try:
        ledger = pc.load_ledger(pw)
    except Exception:
        print("Portfolio: the PORTFOLIO_PASSWORD secret does not match the password used on the PC - skipped.")
        return 0
    old = pc.read_page_state(pw) or {}
    px = pc.fetch_prices(ledger, cache=old.get("px"), log=lambda *a: None)
    state = pc.build_state(ledger, px)
    state["px"] = px
    pc.write_page_state(state, pw)
    print(f"Portfolio updated to {state['as_of']}.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Portfolio: not updated ({type(e).__name__})")
        sys.exit(0)
