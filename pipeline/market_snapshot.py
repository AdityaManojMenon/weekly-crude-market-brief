import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


# ── Ticker definitions ──────────────────────────────────────────────────────
TICKERS = {
    # CL=F (front-month futures) IS the WTI spot price — used by Bloomberg,
    # Reuters, and EIA as the de-facto WTI crude benchmark.
    "WTI_CRUDE":   "CL=F",
    "BRENT":       "BZ=F",
    "NAT_GAS":     "NG=F",
    "RBOB":        "RB=F",
    "HEATING_OIL": "HO=F",
    "DXY":         "DX-Y.NYB",
    "SP500":       "^GSPC",
}

# How many calendar days to pull (must cover >5 trading days for WoW calc)
_LOOKBACK_DAYS = 20


def _nearest_prior_business_day(dt: pd.Timestamp) -> pd.Timestamp:
    """Roll back to the nearest Mon–Fri if dt lands on a weekend."""
    while dt.weekday() >= 5:
        dt -= pd.Timedelta(days=1)
    return dt


def fetch_market_snapshot(target_date=None) -> dict:
    """
    Returns a dict with one entry per tracked asset:

        {
          "WTI": {
            "price":      97.87,
            "wow_change": -5.23,
            "wow_pct":    -5.10,
            "date":       Timestamp("2026-04-09"),
          },
          ...
        }

    WoW is calculated as (price_on_target_date) – (price_5_trading_days_earlier).
    For live mode (target_date=None) the latest available close is used.
    """
    # ── Resolve target date ──────────────────────────────────────────────────
    if target_date is not None:
        as_of = _nearest_prior_business_day(pd.to_datetime(target_date))
    else:
        as_of = _nearest_prior_business_day(pd.Timestamp(datetime.today().date()))

    start = (as_of - pd.Timedelta(days=_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    end   = (as_of + pd.Timedelta(days=1)).strftime("%Y-%m-%d")   # yfinance end is exclusive

    print(f"Fetching market snapshot for {as_of.date()} …")

    result = {}

    for label, ticker in TICKERS.items():
        try:
            raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

            if raw is None or raw.empty:
                print(f"  ✗ {label} ({ticker}): no data")
                result[label] = _empty_row(ticker)
                continue

            close = raw["Close"].squeeze()

            if isinstance(close, pd.DataFrame):
                # Multi-ticker fallback shouldn't happen, but guard anyway
                close = close.iloc[:, 0]

            close = close.dropna()

            if close.empty:
                print(f"  ✗ {label} ({ticker}): empty after dropna")
                result[label] = _empty_row(ticker)
                continue

            # Snap to the as_of date or the most recent available date before it
            close = close[close.index <= as_of]

            if close.empty:
                print(f"  ✗ {label} ({ticker}): no data on or before {as_of.date()}")
                result[label] = _empty_row(ticker)
                continue

            price = float(close.iloc[-1])
            price_date = close.index[-1]

            # Week-over-week: 5 trading days back in the available series
            if len(close) >= 6:
                week_ago_price = float(close.iloc[-6])
            else:
                week_ago_price = float(close.iloc[0])

            wow_change = price - week_ago_price
            wow_pct    = (wow_change / week_ago_price * 100) if week_ago_price != 0 else 0.0

            result[label] = {
                "ticker":     ticker,
                "price":      round(price, 4),
                "wow_change": round(wow_change, 4),
                "wow_pct":    round(wow_pct, 2),
                "date":       price_date,
            }

            print(f"  {label:<14} {price:>9.3f}   WoW {wow_change:+.3f} ({wow_pct:+.2f}%)")

        except Exception as exc:
            print(f"  ✗ {label} ({ticker}): {exc}")
            result[label] = _empty_row(ticker)

    return result


def _empty_row(ticker: str) -> dict:
    return {
        "ticker":     ticker,
        "price":      None,
        "wow_change": None,
        "wow_pct":    None,
        "date":       None,
    }


def snapshot_to_dataframe(snap: dict) -> pd.DataFrame:
    """Convert the snapshot dict to a tidy DataFrame for display or charting."""
    rows = []
    for label, data in snap.items():
        rows.append({
            "Asset":      label,
            "Ticker":     data["ticker"],
            "Price":      data["price"],
            "WoW Chg":    data["wow_change"],
            "WoW %":      data["wow_pct"],
            "Date":       data["date"],
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    snap = fetch_market_snapshot()
    df   = snapshot_to_dataframe(snap)
    print("\n", df.to_string(index=False))
