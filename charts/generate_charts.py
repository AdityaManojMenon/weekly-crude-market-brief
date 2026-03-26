import matplotlib.pyplot as plt
import os
from datetime import datetime

def plot_inventory_vs_seasonal(df):
    """
    Plots current year inventory vs 5Y min-max band
    """
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)
    
    df = df.copy()
    df["year"] = df["period"].dt.year
    df["week"] = df["period"].dt.isocalendar().week


    current_year = df["year"].max()

    #last 5 years excluding current
    hist = df[df["year"] < current_year]
    hist = df[df["year"] >= current_year - 5]

    band = hist.groupby("week")["value_million_bbl"].agg(["min","max"]).reset_index()
    current = df[df["year"] == current_year]
    band = band[band["week"] <= current["week"].max()]

    # merge current with week
    current = current.copy()
    current["week"] = current["period"].dt.isocalendar().week

    plt.figure(figsize=(12,6))

    # plot band
    plt.fill_between(
        band["week"],
        band["min"],
        band["max"],
        alpha=0.2,
        label="5Y Range"
    )

    # plot current year
    plt.plot(
        current["week"],
        current["value_million_bbl"],
        label=f"{current_year} Inventory",
        linewidth=2
    )

    plt.title("US Crude Inventory vs 5-Year Range")
    plt.xlabel("Week of Year")
    plt.ylabel("Million Barrels")
    plt.legend()

    path = f"{folder}/inventory_vs_5yr_band.png"
    plt.savefig(path)
    plt.close()

    return path

# FUTURES CURVE SNAPSHOT
def plot_futures_curve_snapshot(cl1_price, cl2_price):
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)

    months = ["CL1", "CL2"]
    prices = [cl1_price, cl2_price]

    plt.figure(figsize=(8,5))
    plt.plot(months, prices, marker='o')

    plt.title("WTI Futures Curve (Front vs Next Month)")
    plt.ylabel("Price ($)")

    path = f"{folder}/futures_curve.png"
    plt.savefig(path)
    plt.close()

    return path

# SPREAD TIME SERIES
def plot_spread_timeseries(curve_df):
    date_str = datetime.today().strftime("%Y-%m-%d")
    folder = f"charts/{date_str}"
    os.makedirs(folder, exist_ok=True)

    plt.figure(figsize=(10,5))

    plt.plot(curve_df.index, curve_df["spread"], label="CL1–CL2 Spread")
    plt.axhline(0, linestyle="--")

    plt.title("WTI CL1–CL2 Spread (6-Month Trend)")
    plt.ylabel("Spread ($)")
    plt.legend()

    path = f"{folder}/spread_timeseries.png"
    plt.savefig(path)
    plt.close()

    return path
