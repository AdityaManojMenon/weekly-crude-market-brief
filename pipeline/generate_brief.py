import pandas as pd
from pipeline.expectations import get_expectations
from pipeline.eia_ingestion import fetch_all_eia_series
from pipeline.surprise_model import compute_all_surprises   
from pipeline.curve_analytics import fetch_curve_data
from pipeline.generate_insights import generate_insights
from pipeline.call_tracker import log_new_call
from pipeline.call_tracker import update_last_call
from pipeline.crack_spreads import fetch_crack_spread
from pipeline.regime_model import detect_regime_with_momentum
from pipeline.performance import load_data, compute_win_rate, compute_sharpe, compute_cumulative_returns, compute_cagr, compute_drawdown
from pipeline.market_snapshot import fetch_market_snapshot
from charts.generate_charts import plot_inventory_vs_seasonal, plot_futures_curve_snapshot, plot_spread_timeseries, plot_crack_spread,plot_pnl_drawdown, plot_product_snapshot, plot_market_snapshot


def generate_brief(target_date=None):
    """
    Generates a full crude market brief.
    If target_date is provided (YYYY-MM-DD), runs historical snapshot.
    """

    event_override = "CEASEFIRE"

    # FETCH & PREP DATA
    df = fetch_all_eia_series()
    df = compute_all_surprises(df)

    df["period"] = pd.to_datetime(df["period"])

    # Rename crude columns for compatibility
    df = df.rename(columns={
        "crude_million_bbl": "value_million_bbl",
        "crude_million_bbl_change": "weekly_change",
        "crude_seasonal_avg": "seasonal_avg",
        "crude_surprise": "inventory_surprise",
        "crude_signal": "signal",
    })


    # FILTER BY DATE
    if target_date:
        target_date = pd.to_datetime(target_date)
        df_filtered = df[df["period"] <= target_date].copy()
        if df_filtered.empty:
            raise ValueError(f"No inventory data available for {target_date}")
        latest = df_filtered.iloc[-1]
    else:
        df_filtered = df.copy()
        latest = df.iloc[-1]

    #REFINERY METRICS
    refinery_util = latest["refinery_util_pct"]
    refinery_change = (
        df_filtered["refinery_util_pct"].iloc[-1]
        - df_filtered["refinery_util_pct"].iloc[-2]
    )

    #PRODUCTION (MMbbl/d) — EIA weekly estimate
    try:
        production_mmbbl_d = float(latest["production_mmbbl_d"])
        production_wow = float(latest["production_mmbbl_d_change"])
    except (KeyError, TypeError):
        production_mmbbl_d = None
        production_wow = None


    #EXPECTATIONS
    EXPECTATIONS = get_expectations()

    crude_exp_surprise = latest["weekly_change"] - EXPECTATIONS["crude"]
    gasoline_exp_surprise = latest["gasoline_million_bbl_change"] - EXPECTATIONS["gasoline"]
    distillate_exp_surprise = latest["distillates_million_bbl_change"] - EXPECTATIONS["distillates"]
    cushing_exp_surprise = latest["cushing_million_bbl_change"] - EXPECTATIONS["cushing"]

    #CURVE DATA
    curve_df = fetch_curve_data()
    if curve_df is None or curve_df.empty:
        raise ValueError("Curve data unavailable")

    curve_df = curve_df.copy()

    if target_date:
        target_date = pd.to_datetime(target_date)
        curve_df = curve_df.loc[:target_date]
        curve_df = curve_df.sort_index()

    last_spread = curve_df["spread"].iloc[-1]

    print("Using spread date:", curve_df.index[-1])
    print("Spread value:", last_spread)

    # Momentum
    spread_change = (
        curve_df["spread"].iloc[-1]
        - curve_df["spread"].iloc[-2]
    )

    # Z-score + magnitude
    spread_magnitude = curve_df["spread_magnitude"].iloc[-1]
    spread_zscore = curve_df["spread_zscore"].iloc[-1]

    regime, _, caution_flag, reversal_flag = detect_regime_with_momentum(curve_df)

    # Structure classification — spread = CL1 - CL2, positive = backwardation, negative = contango
    if last_spread > 10:
        curve_structure = "Extreme Backwardation"
    elif last_spread > 5:
        curve_structure = "Strong Backwardation"
    elif last_spread > 2:
        curve_structure = "Moderate Backwardation"
    elif last_spread > 0:
        curve_structure = "Mild Backwardation"
    elif last_spread < -10:
        curve_structure = "Extreme Contango"
    elif last_spread < -5:
        curve_structure = "Strong Contango"
    elif last_spread < -2:
        curve_structure = "Moderate Contango"
    else:
        curve_structure = "Mild Contango"

 
    #CRACK SPREAD
    crack_df = fetch_crack_spread()
    if crack_df is None or crack_df.empty:
        raise ValueError("Crack spread data unavailable")

    if target_date:
        crack_df = crack_df[crack_df.index <= target_date]
        if len(crack_df) < 2:
            raise ValueError("Not enough crack data")

    latest_crack = crack_df["crack_spread"].iloc[-1]

    crack_change = (
        crack_df["crack_spread"].iloc[-1]
        - crack_df["crack_spread"].iloc[-2]
    )

    #CHARTS
    inventory_chart = plot_inventory_vs_seasonal(df_filtered, target_date)

    latest_curve = curve_df.iloc[-1]
    cl1_price = latest_curve["CL1"]
    cl2_price = latest_curve["CL2"]

    curve_chart = plot_futures_curve_snapshot(cl1_price, cl2_price, target_date)
    spread_chart = plot_spread_timeseries(curve_df, report_date=target_date)

    crack_chart = plot_crack_spread(crack_df, target_date)
    product_chart = plot_product_snapshot(df_filtered, target_date)

    #MARKET SNAPSHOT (prices + WoW for all assets not already in brief)
    try:
        market_snap = fetch_market_snapshot(target_date)
        market_snap_chart = plot_market_snapshot(market_snap, report_date=target_date)
    except Exception as e:
        print(f"Market snapshot skipped: {e}")
        market_snap = {}
        market_snap_chart = None

    #INSIGHTS
    insights = generate_insights(
        latest,
        curve_structure,
        last_spread,
        latest_crack,
        crack_change,
        refinery_util,
        refinery_change,
        crude_exp_surprise,
        gasoline_exp_surprise,
        distillate_exp_surprise,
        cushing_exp_surprise,
        spread_magnitude,
        spread_zscore,
        EXPECTATIONS,
        regime,
        spread_change,
        caution_flag,
        reversal_flag,
        event_override,
    )

    #TRACKER
    if not target_date:
        update_last_call()

        log_new_call(
            signal=insights["final_signal"],
            confidence=insights["confidence"],
            trade=insights["trade_idea"],
            entry_price=cl1_price,
        )

    #PERFORMANCE
    try:
        performance_df = load_data()
        win_rate = compute_win_rate(performance_df)
        performance_df = compute_cumulative_returns(performance_df)
        performance_df, max_dd = compute_drawdown(performance_df)
        sharpe = compute_sharpe(performance_df)
        cagr = compute_cagr(performance_df)

        pnl_chart = plot_pnl_drawdown(
            performance_df, win_rate, sharpe, max_dd,target_date
        )
    except Exception as e:
        print(f"Performance skipped: {e}")
        pnl_chart = None
        cagr = None

    #OUTPUT
    print("\n--- FINAL MARKET VIEW ---")
    print(insights)

    print(f"\nRegime: {regime} | Spread Change: {spread_change:.2f}")

    if production_mmbbl_d is not None:
        wow_str = f"{production_wow:+.3f} MMbbl/d WoW" if production_wow is not None else ""
        print(f"Production: {production_mmbbl_d:.1f} MMbbl/d  {wow_str}")

    if cagr is not None:
        print(f"CAGR: {cagr:.2%}")

    # Attach snapshot and production to insights so callers can use them
    insights["market_snapshot"]    = market_snap
    insights["production_mmbbl_d"] = production_mmbbl_d
    insights["production_wow"]     = production_wow

    print("\nCharts saved:")
    print(inventory_chart)
    print(curve_chart)
    print(spread_chart)
    print(crack_chart)
    print(product_chart)

    if market_snap_chart:
        print(market_snap_chart)

    if pnl_chart:
        print(pnl_chart)


def main():
    #CURRENT
    generate_brief()
    print("=================\n")
    generate_brief("2026-04-09")
    print("=================\n")
    generate_brief("2026-04-02")
    print("=================\n")
    generate_brief("2026-03-26")


if __name__ == "__main__":
    main()