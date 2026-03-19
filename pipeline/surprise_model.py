import pandas as pd

def compute_seasonal_baseline(df):
    """
    Computes 5-year seasonal average weekly change by week of year
    """
    df = df.copy()

    # 5 years cutoff
    cutoff = df["period"].max() - pd.DateOffset(years=5)
    
    last_5y = df[df["period"] >= cutoff].copy()

    # Create the seasonal bucket
    last_5y["week"] = last_5y["period"].dt.isocalendar().week

    seasonal_avg = (
        last_5y.groupby("week")["weekly_change"]
        .mean()
        .reset_index()
        .rename(columns={"weekly_change": "seasonal_avg"})
    )

    return seasonal_avg

def compute_inventory_surprise(df):
    """
    Adds seasonal baseline + surprise + signal
    """

    df = df.copy()
    
    seasonal = compute_seasonal_baseline(df)

    #merge seasonal average
    df["week"] = df["period"].dt.isocalendar().week
    df = df.merge(seasonal, on = "week", how = "left")

    #compute surprise
    df["inventory_surprise"] = df["weekly_change"] - df["seasonal_avg"]

    # classify signal
    def classify_signal(x):
        if pd.isna(x):
            return "neutral"
        elif x < -1:
            return "bullish"   # bigger draw than expected
        elif x > 1:
            return "bearish"   # bigger build than expected
        else:
            return "neutral"
        
    df["signal"] = df["inventory_surprise"].apply(classify_signal)

    return df




