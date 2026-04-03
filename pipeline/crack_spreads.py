import yfinance as yf
import pandas as pd

def fetch_crack_spread():
    cl = yf.download("CL=F", period="6mo")["Close"].squeeze()
    rb = yf.download("RB=F", period="6mo")["Close"].squeeze()
    ho = yf.download("HO=F", period="6mo")["Close"].squeeze()

    df = pd.DataFrame({
        "CL": cl,
        "RB": rb,
        "HO": ho
    }).dropna()

    # 42 gallons in a barrel
    df["RB_barrel"] = df["RB"] * 42 
    df["HO_barrel"] = df["HO"] * 42
    # 3-2-1 crack spread
    df["crack_spread"] = ((2 * df["RB_barrel"]) + df["HO_barrel"] - (3 * df["CL"])) / 3

    return df


if __name__ == "__main__":
    data = fetch_crack_spread()
    print(data)