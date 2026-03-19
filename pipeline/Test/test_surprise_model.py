from pipeline.eia_ingestion import fetch_eia_data
from pipeline.surprise_model import compute_inventory_surprise

df = fetch_eia_data()
df = compute_inventory_surprise(df)

latest = df.iloc[-1]

print(df)
print("\n=====================\n")

print("Latest Week:")
print(f"Inventory: {latest['value_million_bbl']:.1f} mb")
print(f"Weekly Change: {latest['weekly_change']:.2f} mb")
print(f"Seasonal Avg: {latest['seasonal_avg']:.2f} mb")
print(f"Surprise: {latest['inventory_surprise']:.2f} mb")
print(f"Signal: {latest['signal']}")