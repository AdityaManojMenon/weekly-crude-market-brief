import pandas as pd
from pipeline.eia_ingestion import fetch_eia_data
from pipeline.surprise_model import compute_inventory_surprise   
from pipeline.curve_analytics import fetch_curve_data
from pipeline.generate_insights import generate_insights
from pipeline.call_tracker import log_new_call
from pipeline.call_tracker import update_last_call
from charts.generate_charts import plot_inventory_vs_seasonal, plot_futures_curve_snapshot, plot_spread_timeseries

def generate_brief():

    # FETCH INVENTORY DATA
    df = fetch_eia_data()

    # ADD SURPRISE + SIGNAL
    df = compute_inventory_surprise(df)

    # GET LATEST ROW (inventory_row)
    latest = df.iloc[-1]

    # FETCH CURVE DATA
    curve_df = fetch_curve_data()
    if curve_df is not None and not curve_df.empty:
        last_spread = curve_df["spread"].iloc[-1]

    # classification logic
    if last_spread > 2:
        curve_structure = "Extreme Backwardation"
    elif last_spread > 1:
        curve_structure = "Strong Backwardation"
    elif last_spread > 0:
        curve_structure = "Mild Backwardation"
    elif last_spread < -1.5:
        curve_structure = "Extreme Contango"
    elif last_spread < -1:
        curve_structure = "Strong Contango"
    else:
        curve_structure = "Mild Contango"


    inventory_chart = plot_inventory_vs_seasonal(df)

    latest_curve = curve_df.iloc[-1]
    cl1_price = latest_curve["CL1"]
    cl2_price = latest_curve["CL2"]

    curve_chart = plot_futures_curve_snapshot(cl1_price, cl2_price)
    spread_chart = plot_spread_timeseries(curve_df)
        
    # GENERATE INSIGHTS
    insights = generate_insights(latest, curve_structure, last_spread)

    update_last_call()
    entry_price = cl1_price  # front-month price
    log_new_call(
        signal=insights["final_signal"],
        confidence=insights["confidence"],
        trade=insights["trade_idea"],
        entry_price=entry_price
    )

    # PRINT (OR WRITE TO FILE)
    print("\n--- FINAL MARKET VIEW ---")
    print(insights)

    print("\nCharts saved:")
    print(inventory_chart)
    print(curve_chart)
    print(spread_chart)

def main():
    generate_brief()

if __name__ == "__main__":
    main()
