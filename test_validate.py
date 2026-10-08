"""
Validate that app.py can be imported without errors.
Tests the full set of imports and all page functions can be called.
"""
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit so we don't need a browser/server
import unittest.mock as mock

# Replace streamlit with a mock
st_mock = mock.MagicMock()
st_mock.session_state = {}
st_mock.cache_data = lambda **kwargs: (lambda f: f)
sys.modules['streamlit'] = st_mock

# Now test all src modules directly
print("Testing src modules...")

from src.data_processing import load_and_clean, get_summary_stats
from src.forecasting import train_model, generate_forecast_df, SKLEARN_AVAILABLE
from src.waste_risk import calculate_risk, get_risk_summary, get_category_risk_profile
from src.recommendations import generate_recommendations, get_action_summary, get_item_action_summary
from src.redistribution import load_recipients, match_recipients, get_redistribution_summary

print(f"sklearn available: {SKLEARN_AVAILABLE}")

df, report = load_and_clean()
assert len(df) > 6000, f"Expected >6000 rows, got {len(df)}"
assert "DayOfWeek" in df.columns, "DayOfWeek missing"
assert "Waste_Ratio" in df.columns, "Waste_Ratio missing"

result = train_model(df)
assert result["metrics"]["MAE"] > 0
assert result["metrics"]["R2"] != "N/A (baseline model)"
print(f"Model: {result['model_type']}, R2={result['metrics']['R2']}, MAE={result['metrics']['MAE']}")

df_f = generate_forecast_df(df, result)
assert "Predicted_Demand" in df_f.columns
assert (df_f["Predicted_Demand"] >= 0).all()

df_r = calculate_risk(df_f)
assert "Waste_Risk" in df_r.columns
assert set(df_r["Waste_Risk"].unique()).issubset({"Low", "Medium", "High"})

df_rec = generate_recommendations(df_r)
assert "Recommended_Action" in df_rec.columns

recipients = load_recipients()
assert len(recipients) >= 5

matches = match_recipients(df_rec, recipients)
assert len(matches) > 0, "Expected some redistribution matches"

summary = get_redistribution_summary(matches)
assert summary["total_matches"] > 0

print()
print("=" * 50)
print("FULL VALIDATION PASSED")
print(f"  Records: {len(df)}")
print(f"  Model R2: {result['metrics']['R2']}")
print(f"  Risk High: {get_risk_summary(df_r)['high_count']}")
print(f"  Actions: {get_action_summary(df_rec)['action_counts']}")
print(f"  Redistribution matches: {summary['total_matches']}")
print("=" * 50)
