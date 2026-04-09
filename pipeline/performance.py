import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

TRACKER_FILE = "call_tracker.csv"

def load_data():
    df = pd.read_csv(TRACKER_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["return_pct"])
    return df

def compute_win_rate(df):
    win = df["correct"].dropna()
    win_rate = win.mean() * 100 if len(win) > 0 else 0
    print(f"Win Rate: {win_rate:.2f}%")
    return win_rate

# CUMULATIVE PnL
def compute_cumulative_returns(df):
    df = df.copy()

    # convert % → decimal
    df["ret_decimal"] = df["return_pct"] / 100

    # cumulative return
    starting_capital = 10000
    # Calculate the growth factor first
    df["cumulative"] = (1 + df["ret_decimal"]).cumprod()
    #Scaling capital
    df["wealth_growth"] = starting_capital * df["cumulative"]
    
    if len(df) >= 1:
        baseline = pd.DataFrame({
            "date": [df["date"].iloc[0] - pd.Timedelta(days=7)],
            "wealth_growth": [starting_capital]
        })

        df = pd.concat([baseline, df], ignore_index=True)
    
    # sort to ensure correct plotting order
    df = df.sort_values("date")

    return df

# SHARPE RATIO
def compute_sharpe(df):
    returns = df["return_pct"].dropna() / 100
    if len(returns) < 2:
        print("Not enough data for Sharpe")
        return None
    # Annualized Sharpe Ratio for weekly data
    sharpe_annualized = (returns.mean() / returns.std()) * (52 ** 0.5)
    print(f"Sharpe Ratio: {sharpe_annualized:.2f}")
    return sharpe_annualized

def compute_drawdown(df):
    df = df.copy()
    df["peak"] = df["wealth_growth"].cummax()
    df["drawdown"] = (df["wealth_growth"] - df["peak"]) / df["peak"]

    max_dd = df["drawdown"].min()
    print(f"Max Drawdown: {max_dd * 100:.2f}%")

    return df, max_dd

def compute_cagr(df):
    start = df["date"].iloc[0]
    end = df["date"].iloc[-1]

    years = (end - start).days / 365
    final = df["wealth_growth"].iloc[-1]
    initial = df["wealth_growth"].iloc[0]

    if years > 0:
        cagr = (final / initial) ** (1 / years) - 1
        print(f"CAGR: {cagr * 100:.2f}%")

def main():
    df = load_data()

    wr = compute_win_rate(df)
    cr = compute_cagr(df)
    df_results = compute_cumulative_returns(df)
    sr = compute_sharpe(df_results)
    df_results, max_dd = compute_drawdown(df_results)


    print(f"Final Account Value: ${df_results['wealth_growth'].iloc[-1]:.2f}")
    print(f"Total Trades: {len(df)}")

if __name__ == "__main__":
    main()