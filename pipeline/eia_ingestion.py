import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()

# EIA api key and crude oil inventory series
API_KEY = os.getenv("EIA_API_KEY")
SERIES_ID = "PET.WCESTUS1.W"

def fetch_eia_data(cache_path="data/eia_cache/crude_inventory.csv",force_refresh=False):
    """
    Fetching oil data and putting it into dataframe and filtering it to be concise and readable
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    # Check if cache is older than 24 hours (86400 seconds) or if we want to force it
    file_exists = os.path.exists(cache_path)
    is_stale = file_exists and (time.time() - os.path.getmtime(cache_path) > 86400)

    file_exists = os.path.exists(cache_path)
    # Check if the file is older than 24 hours
    is_stale = file_exists and (time.time() - os.path.getmtime(cache_path) > 86400)

    if file_exists and not is_stale and not force_refresh:
        print(f"Loading from cache: {cache_path}")
        df = pd.read_csv(cache_path, parse_dates=["period"])
        return df

    print("Fetching fresh data from EIA API...")
    url = f"https://api.eia.gov/v2/seriesid/{SERIES_ID}?api_key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad status codes
        data = response.json()
        
        if "response" not in data or "data" not in data["response"]:
            raise ValueError("Unexpected API response format. Check your API Key or Series ID.")

        records = data["response"]["data"]
        df = pd.DataFrame(records)
        
        # Data Processing
        df["period"] = pd.to_datetime(df["period"])
        df["value"] = df["value"].astype(float)
        df["value_million_bbl"] = df["value"] / 1000
        
        # Sort to ensure weekly_change is calculated correctly
        df = df.sort_values("period")
        df["weekly_change"] = df["value_million_bbl"].diff()
        
        # Filter columns
        df = df[["period", "value_million_bbl", "weekly_change"]]

        # Save to cache
        df.to_csv(cache_path, index=False)
        return df

    except Exception as e:
        print(f"Error fetching data: {e}")
        if file_exists:
            print("Falling back to stale cache...")
            return pd.read_csv(cache_path, parse_dates=["period"])
        raise

if __name__ == "__main__":
    df = fetch_eia_data()
    print(df.tail())

