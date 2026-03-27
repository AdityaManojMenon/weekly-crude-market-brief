import pandas as pd
from datetime import datetime
import yfinance as yf
import os

TRACKER_FILE = "call_tracker.csv"


def log_new_call(signal, confidence, trade, entry_price):
    date_str = datetime.today().strftime("%Y-%m-%d")

    new_row = {
        "date": date_str,
        "signal": signal,
        "confidence": confidence,
        "trade": trade,
        "entry_price": entry_price,
        "next_week_price": None,
        "return_pct": None,
        "correct": None
    }

    if os.path.exists(TRACKER_FILE):
        df = pd.read_csv(TRACKER_FILE)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_csv(TRACKER_FILE, index=False)

    print(f"Logged new call for {date_str}")


def update_last_call():
    if not os.path.exists(TRACKER_FILE):
        return

    df = pd.read_csv(TRACKER_FILE)

    if df.empty:
        return

    last_idx = df.index[-1]

    # skip if already updated
    if pd.notna(df.loc[last_idx, "next_week_price"]):
        return

    # get current WTI price
    wti = yf.download("CL=F", period="1d")
    current_price = float(wti["Close"].iloc[-1])

    entry_price = df.loc[last_idx, "entry_price"]

    # calculate return
    ret = (current_price - entry_price) / entry_price * 100

    signal = df.loc[last_idx, "signal"]

    # determine correctness
    if signal in ["BULLISH", "STRONG BULLISH"]:
        correct = "yes" if ret > 0 else "no"
    elif signal in ["BEARISH", "STRONG BEARISH"]:
        correct = "yes" if ret < 0 else "no"
    else:
        correct = "neutral"

    df.loc[last_idx, "next_week_price"] = current_price
    df.loc[last_idx, "return_pct"] = round(ret, 2)
    df.loc[last_idx, "correct"] = correct

    df.to_csv(TRACKER_FILE, index=False)

    print("Updated last call")