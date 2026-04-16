import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("EIA_API_KEY")

SERIES_MAP = {
    "crude": {
        "series_id": "PET.WCESTUS1.W",
        "cache_path": "data/eia_cache/crude_inventory.csv",
        "value_col": "crude_million_bbl",
    },
    "gasoline": {
        "series_id": "PET.WGTSTUS1.W",
        "cache_path": "data/eia_cache/gasoline_inventory.csv",
        "value_col": "gasoline_million_bbl",
    },
    "distillates": {
        "series_id": "PET.WDISTUS1.W",
        "cache_path": "data/eia_cache/distillates_inventory.csv",
        "value_col": "distillates_million_bbl",
    },
    "cushing": {
        "series_id": "PET.W_EPC0_SAX_YCUOK_MBBL.W",
        "cache_path": "data/eia_cache/cushing_inventory.csv",
        "value_col": "cushing_million_bbl",
    },
    "refinery_util": {
        "series_id": "PET.WPULEUS3.W",
        "cache_path": "data/eia_cache/refinery_util.csv",
        "value_col": "refinery_util_pct",
    },
    "production": {
        # Weekly US field production of crude oil (thousand barrels per day)
        "series_id": "PET.WCRFPUS2.W",
        "cache_path": "data/eia_cache/production.csv",
        "value_col": "production_mmbbl_d",
    },
}

CACHE_MAX_AGE_SECONDS = 86400


def _fetch_single_series(
    series_id: str,
    cache_path: str,
    value_col: str,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Fetch one EIA weekly series, cache it locally, and return:
    period | <value_col> | <value_col>_change
    """
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    file_exists = os.path.exists(cache_path)
    is_stale = file_exists and (
        time.time() - os.path.getmtime(cache_path) > CACHE_MAX_AGE_SECONDS
    )

    if file_exists and not is_stale and not force_refresh:
        print(f"Loading from cache: {cache_path}")
        return pd.read_csv(cache_path, parse_dates=["period"])

    print(f"Fetching fresh data from EIA API: {series_id}")
    url = f"https://api.eia.gov/v2/seriesid/{series_id}?api_key={API_KEY}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "response" not in data or "data" not in data["response"]:
            raise ValueError(
                f"Unexpected API response format for series {series_id}. "
                "Check your API key or series id."
            )

        records = data["response"]["data"]
        df = pd.DataFrame(records)

        if df.empty:
            raise ValueError(f"No data returned for series {series_id}")

        df["period"] = pd.to_datetime(df["period"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.sort_values("period")

        if "util" in value_col:
            # refinery utilization already in %
            df[value_col] = df["value"].astype(float)
        elif "production" in value_col:
            # EIA reports kbbl/d → convert to MMbbl/d
            df[value_col] = df["value"].astype(float) / 1000.0
        else:
            # inventory series → convert to million barrels
            df[value_col] = df["value"] / 1000.0
        change_col = f"{value_col}_change"
        df[change_col] = df[value_col].diff()

        df = df[["period", value_col, change_col]]
        df.to_csv(cache_path, index=False)
        return df

    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        if file_exists:
            print(f"Falling back to stale cache: {cache_path}")
            return pd.read_csv(cache_path, parse_dates=["period"])
        raise


def fetch_eia_data(
    cache_path: str = "data/eia_cache/crude_inventory.csv",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Backward-compatible crude-only fetch.
    Returns:
    period | value_million_bbl | weekly_change
    """
    crude_cfg = SERIES_MAP["crude"]
    df = _fetch_single_series(
        series_id=crude_cfg["series_id"],
        cache_path=cache_path,
        value_col=crude_cfg["value_col"],
        force_refresh=force_refresh,
    ).copy()

    return df.rename(
        columns={
            crude_cfg["value_col"]: "value_million_bbl",
            f"{crude_cfg['value_col']}_change": "weekly_change",
        }
    )


def fetch_all_eia_series(force_refresh: bool = False) -> pd.DataFrame:
    """
    Fetch and merge crude, gasoline, distillates, and Cushing weekly series.

    Returns columns:
    - period
    - crude_million_bbl
    - crude_million_bbl_change
    - gasoline_million_bbl
    - gasoline_million_bbl_change
    - distillates_million_bbl
    - distillates_million_bbl_change
    - cushing_million_bbl
    - cushing_million_bbl_change
    - refinery_change
    """
    dfs = []

    for cfg in SERIES_MAP.values():
        df = _fetch_single_series(
            series_id=cfg["series_id"],
            cache_path=cfg["cache_path"],
            value_col=cfg["value_col"],
            force_refresh=force_refresh,
        )
        dfs.append(df)

    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on="period", how="outer")

    merged = merged.sort_values("period").reset_index(drop=True)
    return merged


if __name__ == "__main__":
    df = fetch_all_eia_series()
    print(df.tail())