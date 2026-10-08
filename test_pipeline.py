"""
Quick pipeline validation script.
Run: python test_pipeline.py
"""
import sys

print("1. Loading and cleaning data...")
from src.data_processing import load_and_clean, get_summary_stats
df, report = load_and_clean()
print(f"   Loaded {len(df)} rows.")
print(f"   Report: {report}")

print("2. Summary stats...")
stats = get_summary_stats(df)
print(f"   {stats}")

print("3. Training demand model...")
from src.forecasting import train_model, generate_forecast_df
result = train_model(df)
print(f"   Enough data: {result['enough_data']}")
print(f"   Metrics: {result['metrics']}")

print("4. Generating forecasts...")
df_f = generate_forecast_df(df, result)
print(f"   Added columns: {[c for c in df_f.columns if c not in df.columns]}")

print("5. Risk scoring...")
from src.waste_risk import calculate_risk, get_risk_summary
df_r = calculate_risk(df_f)
risk_sum = get_risk_summary(df_r)
print(f"   Low={risk_sum['low_count']}  Medium={risk_sum['medium_count']}  High={risk_sum['high_count']}")

print("6. Action recommendations...")
from src.recommendations import generate_recommendations, get_action_summary
df_rec = generate_recommendations(df_r)
act_sum = get_action_summary(df_rec)
print(f"   Action counts: {act_sum['action_counts']}")

print("7. Redistribution matching...")
from src.redistribution import load_recipients, match_recipients, get_redistribution_summary
recipients = load_recipients()
matches = match_recipients(df_rec, recipients)
red_sum = get_redistribution_summary(matches)
print(f"   Redistribution summary: {red_sum}")

print()
print("=" * 40)
print("ALL PIPELINE STEPS PASSED")
print("=" * 40)
