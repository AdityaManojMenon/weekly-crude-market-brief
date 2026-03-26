import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_active_month_codes():
    """Returns the current and next month codes for WTI Crude."""
    # Standard Futures Month Codes
    codes = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']
    now = datetime.now()
    
    # Crude usually rolls around the 20th. 
    # Today is March 26, the 'Front' month is likely May (K) 
    # because the April (J) contract is heading into delivery/expiry.
    if now.day > 20:
        now += timedelta(days=20)
    
    # We want the next two available months
    m1_idx = (now.month) % 12 
    m2_idx = (now.month + 1) % 12
    
    year1 = now.year
    year2 = year1 + 1 if m2_idx == 0 else year1

    y1_str = str(year1)[-2:] 
    y2_str = str(year2)[-2:]
    
    # Ticker format: CL + Code + Year + .NYM
    # Example: CLK26.NYM
    return f"CL{codes[m1_idx]}{y1_str}.NYM", f"CL{codes[m2_idx]}{y2_str}.NYM"

def fetch_curve_data():
    t1, t2 = get_active_month_codes()
    print(f"Attempting to fetch: {t1} and {t2}")

    # Explicitly fetch the specific monthly contracts
    cl1 = yf.download(t1, period="3mo")
    cl2 = yf.download(t2, period="3mo")

    if cl1 is not None and cl2 is not None and not cl1.empty and not cl2.empty:
        df = pd.DataFrame({
            "CL1": cl1["Close"].squeeze(),
            "CL2": cl2["Close"].squeeze()
        }).dropna()
        df["spread"] = df["CL1"] - df["CL2"]
        return df

    return None

def main():
    df = fetch_curve_data()
    if df is not None:
        print("\n--- Crude Oil Term Structure (Spread) ---")
        print(df.tail())

        last_spread = df["spread"].iloc[-1]
        if last_spread > 2:
            structure = "Extreme Backwardation"
        elif last_spread > 1:
            structure = "Strong Backwardation"
        elif last_spread > 0:
            structure = "Mild Backwardation"
        elif last_spread < -1.5:
            structure = "Extreme Contango"
        elif last_spread < -1:
            structure = "Strong Contango"
        else:
            structure = "Mild Contango"

        print(structure, last_spread)
        print(f"\nCurrent Market State: {structure} (${last_spread:.2f})")

if __name__ == "__main__":
    main()
