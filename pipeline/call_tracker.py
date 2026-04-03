import pandas as pd
from datetime import datetime
import yfinance as yf
import os

TRACKER_FILE = "call_tracker.csv"

SLIPPAGE_BPS = 5 # 0.05%
TRANSACTION_COST_BPS = 2 # 0.02%


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

    if len(df) < 2:
        print("No previous call to evaluate.")
        return

    last_idx = df.index[-2]

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
    gross_return = (current_price - entry_price) / entry_price

    # convert bps → %
    slippage = SLIPPAGE_BPS / 10000
    transaction_cost = TRANSACTION_COST_BPS / 10000

    net_return = gross_return - slippage - transaction_cost

    ret_pct = net_return * 100
    signal = str(df.loc[last_idx, "signal"]).upper()

    # Correctness logic
    if "BULLISH" in signal:
        correct = 1 if ret_pct > 0 else 0
    elif "BEARISH" in signal:
        correct = 1 if ret_pct < 0 else 0
    else:
        correct = None
    
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Save results
    df.at[last_idx, "next_week_price"] = round(current_price, 2)
    df.at[last_idx, "gross_return_pct"] = round(gross_return * 100, 2)
    df.at[last_idx, "return_pct"] = round(ret_pct, 2)
    df.at[last_idx, "correct"] = correct

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