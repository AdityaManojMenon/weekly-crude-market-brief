import matplotlib.pyplot as plt
import os
from datetime import datetime

def plot_inventory_vs_seasonal(df):
    plt.style.use('fivethirtyeight') # Gives it a clean, professional look
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)
    
    df = df.copy()
    df["year"] = df["period"].dt.year
    df["week"] = df["period"].dt.isocalendar().week

    current_year = df["year"].max()
    hist = df[(df["year"] < current_year) & (df["year"] >= current_year - 5)]

    # Calculate band
    band = hist.groupby("week")["value_million_bbl"].agg(["min", "max", "mean"]).reset_index()
    current = df[df["year"] == current_year].copy()
    current["week"] = current["period"].dt.isocalendar().week

    fig, ax = plt.subplots(figsize=(12, 7))

    # 1. Plot the 5Y Range (The "Cloud")
    ax.fill_between(band["week"], band["min"], band["max"], 
                    color = 'gray', alpha=0.15, label="5-Year Range (Min-Max)")
    
    # 2. Plot the 5Y Average (The "Anchor")
    ax.plot(band["week"], band["mean"], color = 'gray', linestyle='--', 
            linewidth=1, alpha=0.6, label="5-Year Average")

    # 3. Plot Current Year (The "Signal")
    ax.plot(current["week"], current["value_million_bbl"], 
            color="red", linewidth=3, label=f"{current_year} Inventory")

    # Formatting
    ax.set_title(f"US Crude Inventory: {current_year} vs. 5-Year Seasonality", fontsize = 16, pad = 20)
    ax.set_xlabel("Week of Year", fontsize=12)
    ax.set_ylabel("Million Barrels (mbbl)", fontsize=12)
    ax.legend(facecolor = 'white', frameon = True, loc = 'upper right')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = f"{folder}/inventory_vs_5yr_band.png"
    plt.savefig(path, dpi=300) 
    plt.close()
    return path

# FUTURES CURVE SNAPSHOT
def plot_futures_curve_snapshot(cl1_price, cl2_price):
    plt.style.use('ggplot')
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)

    months = ["Front Month (CL1)", "Next Month (CL2)"]
    prices = [cl1_price, cl2_price]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Plot lined as dots
    ax.plot(months, prices, marker = 'o', markersize=10, color = "blue", linewidth=3)
    # Add price labels above dots
    for i, price in enumerate(prices):
        ax.annotate(f"${price:.2f}", (months[i], prices[i]), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold')
    
    # Shade area under the curve
    ax.fill_between(months, prices, min(prices)-1, color = "blue", alpha = 0.1)
    state = "Backwardation" if cl1_price > cl2_price else "Contango"
    ax.set_title(f"WTI Futures Curve: {state}", fontsize = 14, color = "black")
    ax.set_ylabel("Price per Barrel ($)")
    ax.set_ylim(min(prices)-2, max(prices)+2)

    plt.tight_layout()
    path = f"{folder}/futures_curve.png"
    plt.savefig(path, dpi=300)
    plt.close()
    return path

# SPREAD TIME SERIES
def plot_spread_timeseries(curve_df):
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the spread
    ax.plot(curve_df.index, curve_df["spread"], color='green', linewidth=2, label="CL1–CL2 Spread")
    # Add a zero line
    ax.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)

    ax.set_title("WTI Prompt Spread (CL1–CL2)", fontsize=14, loc='left')
    ax.set_ylabel("Spread ($)")
    ax.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    path = f"{folder}/spread_timeseries.png"
    plt.savefig(path, dpi=300)
    plt.close()
    return path
