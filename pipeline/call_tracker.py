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
        print("Last call already updated.")
        return

    call_date = pd.to_datetime(df.loc[last_idx, "date"])
    today = pd.Timestamp.today()

    if (today - call_date).days < 5:
        print("Too early to evaluate call.")
        return

    # Fetch price
    try:
        wti = yf.Ticker("CL=F")
        hist = wti.history(period="1d")

        if hist.empty:
            print("No price data available.")
            return

        current_price = float(hist["Close"].iloc[-1])

    except Exception as e:
        print(f"Error fetching price: {e}")
        return

    entry_price = float(df.loc[last_idx, "entry_price"])


    # Compute return
    ret_pct = ((current_price - entry_price) / entry_price) * 100
    signal = str(df.loc[last_idx, "signal"]).upper()

    # Correctness logic
    if "BULLISH" in signal:
        correct = 1 if ret_pct > 0 else 0
    elif "BEARISH" in signal:
        correct = 1 if ret_pct < 0 else 0
    else:
        correct = None

    # Save results
    df.at[last_idx, "next_week_price"] = round(current_price, 2)
    df.at[last_idx, "return_pct"] = round(ret_pct, 2)
    df.at[last_idx, "correct"] = correct

    # enforce numeric
    df["entry_price"] = pd.to_numeric(df["entry_price"], errors="coerce")
    df["next_week_price"] = pd.to_numeric(df["next_week_price"], errors="coerce")
    df["return_pct"] = pd.to_numeric(df["return_pct"], errors="coerce")
    df["correct"] = pd.to_numeric(df["correct"], errors="coerce")

    df.to_csv(TRACKER_FILE, index=False)

    print(f"Updated last call → Return: {ret_pct:.2f}% | Correct: {correct}")

def main():
    update_last_call()

if __name__ == "__main__":
    main()