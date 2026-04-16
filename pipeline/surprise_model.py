import pandas as pd


def _compute_series_seasonal_baseline(
    df: pd.DataFrame,
    change_col: str,
    output_col: str,
) -> pd.DataFrame:
    """
    Compute 5-year seasonal average weekly change by ISO week for a given series.
    """
    work = df.copy()
    cutoff = work["period"].max() - pd.DateOffset(years=5)
    last_5y = work[work["period"] >= cutoff].copy()

    last_5y["week"] = last_5y["period"].dt.isocalendar().week

    seasonal = (
        last_5y.groupby("week")[change_col]
        .mean()
        .reset_index()
        .rename(columns={change_col: output_col})
    )
    return seasonal


def _classify_inventory_signal(x: float) -> str:
    if pd.isna(x):
        return "neutral"
    if x < -1:
        return "bullish"   # bigger draw than expected
    if x > 1:
        return "bearish"   # bigger build than expected
    return "neutral"


def _classify_product_signal(x: float) -> str:
    """
    For gasoline/distillates:
    More negative than expected = stronger draw = bullish demand signal
    More positive than expected = weaker demand / build = bearish
    """
    if pd.isna(x):
        return "neutral"
    if x < -0.5:
        return "bullish"
    if x > 0.5:
        return "bearish"
    return "neutral"


def compute_inventory_surprise(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backward-compatible crude-only surprise model.

    Expects:
    - period
    - value_million_bbl
    - weekly_change
    """
    work = df.copy()

    seasonal = _compute_series_seasonal_baseline(
        work,
        change_col="weekly_change",
        output_col="seasonal_avg",
    )

    work["week"] = work["period"].dt.isocalendar().week
    work = work.merge(seasonal, on="week", how="left")

    work["inventory_surprise"] = work["weekly_change"] - work["seasonal_avg"]
    work["signal"] = work["inventory_surprise"].apply(_classify_inventory_signal)

    return work


def compute_all_surprises(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add seasonal averages, surprises, and signals for:
    - crude
    - gasoline
    - distillates
    - cushing

    Expects columns from fetch_all_eia_series().
    """
    work = df.copy()
    work["week"] = work["period"].dt.isocalendar().week

    series_specs = [
        {
            "change_col": "crude_million_bbl_change",
            "seasonal_col": "crude_seasonal_avg",
            "surprise_col": "crude_surprise",
            "signal_col": "crude_signal",
            "signal_fn": _classify_inventory_signal,
        },
        {
            "change_col": "gasoline_million_bbl_change",
            "seasonal_col": "gasoline_seasonal_avg",
            "surprise_col": "gasoline_surprise",
            "signal_col": "gasoline_signal",
            "signal_fn": _classify_product_signal,
        },
        {
            "change_col": "distillates_million_bbl_change",
            "seasonal_col": "distillates_seasonal_avg",
            "surprise_col": "distillates_surprise",
            "signal_col": "distillates_signal",
            "signal_fn": _classify_product_signal,
        },
        {
            "change_col": "cushing_million_bbl_change",
            "seasonal_col": "cushing_seasonal_avg",
            "surprise_col": "cushing_surprise",
            "signal_col": "cushing_signal",
            "signal_fn": _classify_inventory_signal,
        },
    ]

    for spec in series_specs:
        seasonal = _compute_series_seasonal_baseline(
            work,
            change_col=spec["change_col"],
            output_col=spec["seasonal_col"],
        )
        work = work.merge(seasonal, on="week", how="left")

        work[spec["surprise_col"]] = (
            work[spec["change_col"]] - work[spec["seasonal_col"]]
        )
        work[spec["signal_col"]] = work[spec["surprise_col"]].apply(spec["signal_fn"])

    return work


if __name__ == "__main__":
    from pipeline.eia_ingestion import fetch_all_eia_series

    df = fetch_all_eia_series()
    out = compute_all_surprises(df)
    print(
        out[
            [
                "period",
                "crude_million_bbl_change",
                "crude_surprise",
                "crude_signal",
                "gasoline_million_bbl_change",
                "gasoline_surprise",
                "gasoline_signal",
                "distillates_million_bbl_change",
                "distillates_surprise",
                "distillates_signal",
                "cushing_million_bbl_change",
                "cushing_surprise",
                "cushing_signal",
            ]
        ].tail()
    )