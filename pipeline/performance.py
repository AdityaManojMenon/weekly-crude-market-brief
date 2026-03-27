import pandas as pd
import matplotlib.pyplot as plt

TRACKER_FILE = "call_tracker.csv"

def load_data():
    df = pd.read_csv(TRACKER_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["return_pct"])
    return df

def compute_win_rate(df):
    win = df["correct"].map({"yes": 1, "no": 0, "neutral": 0})
    win_rate = win.mean() * 100
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

    return df

# SHARPE RATIO
def compute_sharpe(df):
    returns = df["return_pct"] / 100
    if len(returns) < 2:
        print("Not enough data for Sharpe")
        return None
    # Annualized Sharpe Ratio for weekly data
    sharpe_annualized = (returns.mean() / returns.std()) * (52 ** 0.5)
    print(f"Sharpe Ratio: {sharpe_annualized:.2f}")
    return sharpe_annualized


# PLOT PnL CURVE
def plot_pnl(df):
    plt.style.use('ggplot')
    plt.figure(figsize=(12, 6))

    plt.plot(df["date"], df["wealth_growth"], marker='o')
    plt.axhline(y=10000, color='black', linestyle='--', alpha=0.5)

    plt.title("Portfolio Growth: $10,000 Starting Capital (WTI Strategy)")
    plt.ylabel("Account Balance ($)")
    plt.xlabel("Trade Date")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("charts/pnl_curve.png")
    plt.close()
    print("Saved PnL chart → charts/pnl_curve.png")

def main():
    df = load_data()

    wr = compute_win_rate(df)
    df_results = compute_cumulative_returns(df)
    sr = compute_sharpe(df_results)
    
    plot_pnl(df_results)
    print(f"Final Account Value: ${df_results['wealth_growth'].iloc[-1]:.2f}")

if __name__ == "__main__":
    main()