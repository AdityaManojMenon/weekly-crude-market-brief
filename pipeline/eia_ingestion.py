import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# EIA api key and crude oil inventory series
API_KEY = os.getenv("EIA_API_KEY")
SERIES_ID = "PET.WCESTUS1.W"

def fetch_eia_data(cache_path="data/eia_cache/crude_inventory.csv"):
    #caching to avoid hitting api every run
    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path, parse_dates=["period"])
        return df
    
    url = f"https://api.eia.gov/v2/seriesid/{SERIES_ID}?api_key={API_KEY}"

    response = requests.get(url)
    data = response.json()
    records = data["response"]["data"]
    df = pd.DataFrame(records)
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = df["value"].astype(float)
    df["value_million_bbl"] = df["value"] / 1000
    df = df.sort_values("period")
    #track changes that can be plotted
    df["weekly_change"] = df["value_million_bbl"].diff()
    df = df[["period", "value_million_bbl", "weekly_change"]]

    df.to_csv(cache_path, index=False)
    return df

if __name__ == "__main__":
    df = fetch_eia_data()
    print(df.tail())

