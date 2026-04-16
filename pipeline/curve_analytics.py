import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_active_month_codes():
    """Returns front and second WTI futures contracts"""
    codes = ['F','G','H','J','K','M','N','Q','U','V','X','Z']

    now = datetime.now()

    # roll logic
    if now.day > 20:
        now += timedelta(days=20)

    m1 = now.month % 12
    m2 = (now.month + 1) % 12

    y1 = str(now.year)[-2:]
    y2 = str(now.year + 1 if m2 == 0 else now.year)[-2:]

    return f"CL{codes[m1]}{y1}.NYM", f"CL{codes[m2]}{y2}.NYM"


def fetch_curve_data():
    print("Fetching WTI curve data (CL1, CL2)...")

    # -------------------------------
    # STEP 1: Try Yahoo generic tickers
    # -------------------------------
    try:
        cl1 = yf.download("CL=F", period="6mo", progress=False)
        cl2 = yf.download("CL2=F", period="6mo", progress=False)

        if cl2 is None or cl2.empty:
            raise Exception("CL2 failed")

        print("Using Yahoo generic tickers (CL=F, CL2=F)")

    except:
        print("CL2=F failed → fallback to manual contracts")

        t1, t2 = get_active_month_codes()
        print(f"Using contracts: {t1}, {t2}")

        cl1 = yf.download(t1, period="6mo", progress=False)
        cl2 = yf.download(t2, period="6mo", progress=False)

    # -------------------------------
    # STEP 2: VALIDATION
    # -------------------------------
    if cl1 is None or cl2 is None or cl1.empty or cl2.empty:
        raise ValueError("Curve data unavailable (both methods failed)")

    # -------------------------------
    # STEP 3: ALIGN INDEXES (CRITICAL FIX)
    # -------------------------------
    cl1_close = cl1["Close"].squeeze()
    cl2_close = cl2["Close"].squeeze()

    df = pd.concat([
        cl1_close.rename("CL1"),
        cl2_close.rename("CL2")
    ], axis=1).dropna()

    # -------------------------------
    # STEP 4: CORRECT SPREAD DEFINITION
    # BACKWARDATION = POSITIVE
    # -------------------------------
    df["spread"] = df["CL1"] - df["CL2"]

    # -------------------------------
    # STEP 5: MOMENTUM
    # -------------------------------
    df["spread_change"] = df["spread"].diff()

    # -------------------------------
    # STEP 6: Z-SCORE (ROBUST)
    # -------------------------------
    window = min(20, len(df))

    df["spread_mean"] = df["spread"].rolling(window, min_periods=10).mean()
    df["spread_std"] = df["spread"].rolling(window, min_periods=10).std()

    df["spread_zscore"] = (
        (df["spread"] - df["spread_mean"]) / df["spread_std"]
    ).fillna(0)

    df["spread_magnitude"] = df["spread"].abs()

    return df