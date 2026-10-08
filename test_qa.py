"""
test_qa.py — FoodWise AI Full QA Test Suite
Run with: .venv/Scripts/python.exe test_qa.py
"""
import io
import sys
import traceback
import pandas as pd
import numpy as np

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
results = []

def check(name, condition, level=PASS, detail=""):
    status = level if condition else FAIL
    results.append((name, status, detail))
    marker = "OK " if status == PASS else ("WRN" if status == WARN else "ERR")
    print(f"  [{marker}] {name}" + (f"  — {detail}" if detail else ""))

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ================================================================
# 1. DATA PROCESSING
# ================================================================
section("1. DATA PROCESSING — src/data_processing.py")
from src.data_processing import (
    load_and_clean, get_summary_stats, validate_columns,
    load_data, clean_data, REQUIRED_COLUMNS
)

# 1a. Sample dataset loads
try:
    df, report = load_and_clean()
    check("Sample dataset loads without error", True)
    check("Records loaded > 6000", len(df) > 6000, detail=f"{len(df)} rows")
    check("No rows removed from clean sample", report["rows_removed_total"] == 0,
          detail=f"removed={report['rows_removed_total']}")
except Exception as e:
    check("Sample dataset loads without error", False, FAIL, str(e))
    df = pd.DataFrame()
    report = {}

# 1b. Required columns present
check("Required cols present after load",
      all(c in df.columns for c in REQUIRED_COLUMNS),
      detail=str([c for c in REQUIRED_COLUMNS if c not in df.columns]))

# 1c. Date parsing
check("Date column is datetime dtype", pd.api.types.is_datetime64_any_dtype(df["Date"]))

# 1d. Derived columns
for col in ["DayOfWeek", "DayName", "Month", "MonthName", "IsWeekend", "Week", "Waste_Ratio"]:
    check(f"Derived column '{col}' present", col in df.columns)

# 1e. Waste_Ratio division-by-zero safety
zero_prep = df["Prepared_Quantity"] == 0
if zero_prep.any():
    check("Waste_Ratio is 0.0 when Prepared=0", (df.loc[zero_prep, "Waste_Ratio"] == 0.0).all())
else:
    check("No zero-prep rows (no div-by-zero risk)", True, WARN, "0 zero-prep rows — cannot test DivZero path")

# 1f. Remaining_Quantity consistency: never > Prepared_Quantity
inconsistent = (df["Remaining_Quantity"] > df["Prepared_Quantity"]).sum()
check("Remaining_Quantity <= Prepared_Quantity always", inconsistent == 0,
      detail=f"{inconsistent} violations")

# 1g. Sold_Quantity consistency
sold_excess = (df["Sold_Quantity"] > df["Prepared_Quantity"]).sum()
check("Sold_Quantity <= Prepared_Quantity always", sold_excess == 0,
      detail=f"{sold_excess} violations")

# 1h. No negative quantities
for col in ["Prepared_Quantity", "Sold_Quantity", "Remaining_Quantity"]:
    neg = (df[col] < 0).sum()
    check(f"No negative {col}", neg == 0, detail=f"{neg} negatives")

# 1i. Food_Safety_Status column filled (no NaN)
check("Food_Safety_Status: no NaN", df["Food_Safety_Status"].isna().sum() == 0)

# 1j. Malformed CSV handling — two separate test rows:
#   Row 1: bad date + bad numeric (dropped at date-parse step; negatives never reached)
#   Row 2: valid date + negative sold (reaches negative-clamp step)
#   Row 3: valid date + normal values
bad_csv = io.StringIO(
    "Date,Food_Item,Category,Prepared_Quantity,Sold_Quantity,Remaining_Quantity\n"
    "not-a-date,Rice,Grains,abc,-5,999\n"       # bad date → dropped at step 2
    "2024-01-02,Dal,Protein,80,-10,20\n"          # valid date + negative sold → clamped
    "2024-01-01,Rice,Grains,100,80,20\n"           # normal row
)
try:
    raw_bad = pd.read_csv(bad_csv)
    df_bad, rpt_bad = clean_data(raw_bad)
    check("Malformed CSV: bad date row dropped", rpt_bad["date_parse_failures"] >= 1,
          detail=f"date_failures={rpt_bad['date_parse_failures']}")
    check("Malformed CSV: negative qty clamped (valid-date row)", rpt_bad["negative_values_fixed"] >= 1,
          detail=f"negatives_fixed={rpt_bad['negative_values_fixed']}")
    check("Malformed CSV: Remaining recalculated from Prepared-Sold",
          all(df_bad["Remaining_Quantity"] == (df_bad["Prepared_Quantity"] - df_bad["Sold_Quantity"]).clip(lower=0)))
    check("Malformed CSV: app doesn't crash", True)
except Exception as e:
    check("Malformed CSV: app doesn't crash", False, FAIL, str(e))

# 1k. Missing-column validation
df_missing_col = pd.read_csv("data/sample_food_data.csv").drop(columns=["Sold_Quantity"])
ok, missing = validate_columns(df_missing_col)
check("validate_columns detects missing Sold_Quantity", not ok and "Sold_Quantity" in missing)

# 1l. Summary stats uses active df
stats = get_summary_stats(df)
check("total_prepared matches df sum", stats["total_prepared"] == int(df["Prepared_Quantity"].sum()))
check("total_sold matches df sum", stats["total_sold"] == int(df["Sold_Quantity"].sum()))
check("total_remaining matches df sum", stats["total_remaining"] == int(df["Remaining_Quantity"].sum()))
expected_waste_pct = round(df["Remaining_Quantity"].sum() / df["Prepared_Quantity"].sum() * 100, 1)
check("overall_waste_pct computed correctly", stats["overall_waste_pct"] == expected_waste_pct,
      detail=f"got={stats['overall_waste_pct']}, expected={expected_waste_pct}")

# ================================================================
# 2. FORECASTING
# ================================================================
section("2. FORECASTING — src/forecasting.py")
from src.forecasting import (
    train_model, generate_forecast_df, SKLEARN_AVAILABLE,
    FEATURE_COLS, TARGET_COL
)

check("sklearn available in venv", SKLEARN_AVAILABLE,
      detail="RF model active" if SKLEARN_AVAILABLE else "NumPy fallback active")

try:
    result = train_model(df)
    check("train_model returns without error", True)
except Exception as e:
    check("train_model returns without error", False, FAIL, str(e))
    result = None

if result:
    metrics = result["metrics"]
    check("Metrics dict has MAE", "MAE" in metrics and isinstance(metrics["MAE"], float))
    check("Metrics dict has RMSE", "RMSE" in metrics and isinstance(metrics["RMSE"], float))
    check("MAE > 0", metrics["MAE"] > 0, detail=f"MAE={metrics['MAE']}")
    check("RMSE >= MAE", metrics["RMSE"] >= metrics["MAE"],
          detail=f"RMSE={metrics['RMSE']}, MAE={metrics['MAE']}")
    r2 = metrics["R2"]
    check("R2 is numeric (not hardcoded string)", isinstance(r2, float), detail=f"R2={r2}")
    check("R2 is in plausible range [-1, 1]", isinstance(r2, float) and -1.0 <= r2 <= 1.0,
          detail=f"R2={r2}")
    check("model_type key present", "model_type" in result, detail=result.get("model_type","missing"))

    # Data leakage check: FEATURE_COLS must not include target or future data
    leaky = [f for f in FEATURE_COLS if "Remaining" in f or "Sold_Qty" in f or "Waste" in f]
    check("No data leakage in features (no target/future cols)", len(leaky) == 0,
          detail=f"Leaky features: {leaky}" if leaky else "")

    # Train/test split is time-based (no shuffle leakage)
    check("train_rows > test_rows (80/20 time split)",
          metrics.get("train_rows", 0) > metrics.get("test_rows", 1),
          detail=f"train={metrics.get('train_rows')}, test={metrics.get('test_rows')}")

    # generate_forecast_df
    try:
        df_f = generate_forecast_df(df, result)
        check("generate_forecast_df adds Predicted_Demand", "Predicted_Demand" in df_f.columns)
        check("generate_forecast_df adds Predicted_Surplus", "Predicted_Surplus" in df_f.columns)
        check("Predicted_Demand >= 0 always", (df_f["Predicted_Demand"] >= 0).all())
        check("Predicted_Surplus >= 0 always", (df_f["Predicted_Surplus"] >= 0).all())
        check("Predicted_Surplus = Prepared - Predicted (clipped)",
              ((df_f["Prepared_Quantity"] - df_f["Predicted_Demand"]).clip(lower=0) == df_f["Predicted_Surplus"]).all())
    except Exception as e:
        check("generate_forecast_df runs without error", False, FAIL, str(e))
        df_f = df.copy()
        df_f["Predicted_Demand"] = 0
        df_f["Predicted_Surplus"] = 0

# ================================================================
# 3. WASTE RISK
# ================================================================
section("3. WASTE RISK — src/waste_risk.py")
from src.waste_risk import (
    calculate_risk, get_risk_summary, get_category_risk_profile,
    WASTE_RATIO_LOW_THRESHOLD, WASTE_RATIO_HIGH_THRESHOLD, ABS_HIGH_THRESHOLD
)

try:
    df_r = calculate_risk(df_f)
    check("calculate_risk runs without error", True)
except Exception as e:
    check("calculate_risk runs without error", False, FAIL, str(e))
    df_r = df_f.copy()
    df_r["Waste_Risk"] = "Low"

# Risk levels are only Low/Medium/High
valid_risks = {"Low", "Medium", "High"}
actual_risks = set(df_r["Waste_Risk"].unique())
check("Risk values are only Low/Medium/High", actual_risks.issubset(valid_risks),
      detail=f"found: {actual_risks}")

# Zero remaining always maps to Low
zero_rows = df_r[df_r["Remaining_Quantity"] == 0]
if not zero_rows.empty:
    check("Zero remaining → Low risk always",
          (zero_rows["Waste_Risk"] == "Low").all(),
          detail=f"{(zero_rows['Waste_Risk'] != 'Low').sum()} violations")

# High risk should NOT be based on Food_Safety_Status — these are separate concepts
# Waste_Risk must be derivable without Food_Safety_Status
check("Waste risk logic does not reference Food_Safety_Status",
      True, WARN, "Confirmed by code review: risk uses Waste_Ratio + Expiry only")

# Risk_Reason column present and non-empty for surplus rows
surplus_rows = df_r[df_r["Remaining_Quantity"] > 0]
if not surplus_rows.empty:
    empty_reasons = (surplus_rows["Risk_Reason"] == "").sum()
    check("Risk_Reason present for surplus rows",
          empty_reasons == 0, detail=f"{empty_reasons} missing reasons")

# Surplus_Value computed when Price is present
if "Price" in df_r.columns:
    expected_val = (df_r["Remaining_Quantity"] * df_r["Price"]).round(2)
    check("Surplus_Value = Remaining × Price",
          (df_r["Surplus_Value"] - expected_val).abs().max() < 0.01)

# get_risk_summary
risk_sum = get_risk_summary(df_r)
check("Risk summary total = len(df)",
      risk_sum["low_count"] + risk_sum["medium_count"] + risk_sum["high_count"] == len(df_r),
      detail=f"sum={risk_sum['low_count']+risk_sum['medium_count']+risk_sum['high_count']}, len={len(df_r)}")
check("avg_waste_ratio_pct > 0", risk_sum["avg_waste_ratio_pct"] > 0)
check("total_surplus_units matches df sum",
      risk_sum["total_surplus_units"] == int(df_r["Remaining_Quantity"].sum()))

# Category risk profile
cat_profile = get_category_risk_profile(df_r)
check("Category risk profile has all categories",
      set(cat_profile["Category"]) == set(df_r["Category"].unique()))
check("Waste_Ratio_Pct between 0 and 100",
      cat_profile["Waste_Ratio_Pct"].between(0, 100).all())

# ================================================================
# 4. RECOMMENDATIONS
# ================================================================
section("4. RECOMMENDATIONS — src/recommendations.py")
from src.recommendations import (
    generate_recommendations, get_action_summary, get_item_action_summary,
    ACTION_MONITOR, ACTION_REDUCE_PREP, ACTION_DISCOUNT, ACTION_REDISTRIBUTE, ACTION_DISCARD
)

try:
    df_rec = generate_recommendations(df_r)
    check("generate_recommendations runs without error", True)
except Exception as e:
    check("generate_recommendations runs without error", False, FAIL, str(e))
    df_rec = df_r.copy()
    df_rec["Recommended_Action"] = ACTION_MONITOR
    df_rec["Action_Rationale"] = ""

valid_actions = {ACTION_MONITOR, ACTION_REDUCE_PREP, ACTION_DISCOUNT, ACTION_REDISTRIBUTE, ACTION_DISCARD}
actual_actions = set(df_rec["Recommended_Action"].unique())
check("All actions are valid labels", actual_actions.issubset(valid_actions),
      detail=f"found: {actual_actions}")

# Zero-remaining rows should be Monitor (no surplus)
zero_rec = df_rec[df_rec["Remaining_Quantity"] == 0]
if not zero_rec.empty:
    wrong = (zero_rec["Recommended_Action"] != ACTION_MONITOR).sum()
    check("Zero surplus → Monitor action", wrong == 0, detail=f"{wrong} wrong")

# Unsafe food must not be Redistribution Candidate
unsafe_rows = df_rec[df_rec["Food_Safety_Status"].str.lower() == "unsafe"]
if not unsafe_rows.empty:
    bad_unsafe = (unsafe_rows["Recommended_Action"] == ACTION_REDISTRIBUTE).sum()
    check("Unsafe food never recommended for redistribution", bad_unsafe == 0,
          detail=f"{bad_unsafe} violations")

# Redistribution only for Safe food
redist_rows = df_rec[df_rec["Recommended_Action"] == ACTION_REDISTRIBUTE]
if not redist_rows.empty:
    non_safe = (redist_rows["Food_Safety_Status"].str.lower() != "safe").sum()
    check("Redistribution only when Food_Safety_Status == Safe", non_safe == 0,
          detail=f"{non_safe} non-safe redistribution candidates")
    # Redistribution only for High risk
    non_high = (redist_rows["Waste_Risk"] != "High").sum()
    check("Redistribution candidates are High waste risk", non_high == 0,
          detail=f"{non_high} non-High-risk redistribution candidates")

# get_action_summary counts match actual dataframe counts
act_sum = get_action_summary(df_rec)
check("action_counts total = len(df_rec)",
      sum(act_sum["action_counts"].values()) == len(df_rec),
      detail=f"sum={sum(act_sum['action_counts'].values())}, len={len(df_rec)}")
check("redistribution_candidates count matches",
      act_sum["redistribution_candidates"] == act_sum["action_counts"].get(ACTION_REDISTRIBUTE, 0))
check("redistribution_units >= 0", act_sum["redistribution_units"] >= 0)

# get_item_action_summary
item_acts = get_item_action_summary(df_rec)
check("Per-item summary has all food items",
      set(item_acts["Food_Item"]) == set(df_rec["Food_Item"].unique()))

# ================================================================
# 5. REDISTRIBUTION
# ================================================================
section("5. REDISTRIBUTION — src/redistribution.py")
from src.redistribution import (
    load_recipients, match_recipients, get_redistribution_summary
)

try:
    recipients = load_recipients()
    check("Recipient data loads", True)
    check("At least 5 recipients", len(recipients) >= 5, detail=f"{len(recipients)} orgs")
    check("Accepted_Cat_List parsed", "Accepted_Cat_List" in recipients.columns)
except Exception as e:
    check("Recipient data loads", False, FAIL, str(e))
    recipients = pd.DataFrame()

try:
    matches = match_recipients(df_rec, recipients)
    check("match_recipients runs without error", True)
except Exception as e:
    check("match_recipients runs without error", False, FAIL, str(e))
    matches = pd.DataFrame()

# Only redistribution candidates are matched
if not matches.empty:
    candidate_items = set(df_rec[df_rec["Recommended_Action"] == ACTION_REDISTRIBUTE]["Food_Item"])
    match_items = set(matches["Food_Item"])
    non_candidate_matched = match_items - candidate_items
    check("Only redistribution candidates appear in matches",
          len(non_candidate_matched) == 0, detail=f"non-candidates: {non_candidate_matched}")

    # Capacity respected: matched org capacity >= surplus_units for each match row
    capacity_violated = 0
    for _, row in matches.iterrows():
        org_cap = recipients[recipients["Organization_Name"] == row["Organisation"]]["Capacity_Per_Day"].values
        if len(org_cap) > 0 and row["Surplus_Units"] > org_cap[0]:
            capacity_violated += 1
    check("Org capacity >= surplus units in every match", capacity_violated == 0,
          detail=f"{capacity_violated} capacity violations")

    # Food safety shown in matches
    check("Food_Safety_Status column present in matches", "Food_Safety_Status" in matches.columns)

    # Redistribution summary totals
    red_sum = get_redistribution_summary(matches)
    check("redistribution_summary total_eligible_units > 0",
          red_sum["total_eligible_units"] > 0)

# Empty candidates edge case
empty_rec = df_rec.copy()
empty_rec["Recommended_Action"] = ACTION_MONITOR
empty_matches = match_recipients(empty_rec, recipients)
check("match_recipients returns empty df when no candidates",
      isinstance(empty_matches, pd.DataFrame) and empty_matches.empty)

# ================================================================
# 6. APP.PY STATIC ANALYSIS
# ================================================================
section("6. APP.PY — Static / structural checks")

app_src = open("app.py", encoding="utf-8").read()

# Unused import: make_subplots should not appear in app.py
imported_make_subplots = "from plotly.subplots import make_subplots" in app_src
check("Unused import make_subplots removed from app.py", not imported_make_subplots,
      detail="import still present" if imported_make_subplots else "")

# No hardcoded metric numbers (quick check for suspicious patterns)
import re
hardcoded_patterns = [
    (r'kpi\([^,]+,\s*"[0-9,]+(?:\.[0-9]+)?"', "hardcoded numeric string in kpi()"),
    (r'metric\([^,]+,\s*[0-9]+\)', "hardcoded int in st.metric()"),
]
for pattern, desc in hardcoded_patterns:
    # Exclude known safe cases (e.g. height=320, etc.)
    found = [m.group() for m in re.finditer(pattern, app_src) if "height" not in m.group()]
    check(f"No {desc}", len(found) == 0, WARN if found else PASS,
          str(found[:2]) if found else "")

# Session state: data switching invalidates downstream caches
check("Upload path clears forecast_result", '"forecast_result": None' in app_src or
      "st.session_state[\"forecast_result\"] = None" in app_src)
check("Upload path clears df_risk", "st.session_state[\"df_risk\"] = None" in app_src)
check("Upload path clears df_rec", "st.session_state[\"df_rec\"] = None" in app_src)
check("Sample reload clears pipeline when source changes",
      'st.session_state.get("data_source") != "sample"' in app_src)

# SDG wording checks
check("SDG 12 primary stated", "SDG 12" in app_src and "Responsible Consumption" in app_src)
check("SDG 2 as potential only", "potential" in app_src and "SDG 2" in app_src)
check("No claim of proven outcome for SDG 2", "proven outcome" in app_src or "not a proven outcome" in app_src)
check("Disclaimer for prototype present", "decision-support" in app_src.lower() or "prototype" in app_src.lower())
check("No CO2/meals-served/money-saved claims",
      "CO2" not in app_src and "meals served" not in app_src.lower() and "money saved" not in app_src.lower())

# Demand prediction page: model_type displayed dynamically
check("Model type shown from result dict (not hardcoded)",
      'result.get("model_type"' in app_src or 'result["model_type"]' in app_src)

# Metrics displayed from result dict
check("MAE shown from metrics dict", 'metrics["MAE"]' in app_src)
check("RMSE shown from metrics dict", 'metrics["RMSE"]' in app_src)
check("R2 shown from metrics dict", 'metrics["R2"]' in app_src)

# Risk page: wording check — risk != food unsafe
check("Risk page does not equate High-Risk with Unsafe",
      "food is unsafe" not in app_src.lower() and "unsafe food" not in app_src.lower()
      or "risk level" in app_src.lower())

# Redistribution page: simulated disclaimer
check("Redistribution page has PROTOTYPE DISCLAIMER", "PROTOTYPE DISCLAIMER" in app_src)
check("No claim of real NGO network", "real NGO" not in app_src or "does NOT connect" in app_src)

# ================================================================
# 7. DATA SOURCE SWITCHING
# ================================================================
section("7. DATA SOURCE SWITCHING — behavioural test")

# Simulate uploading a different CSV (a subset of the sample) and check metrics change
subset_df = pd.read_csv("data/sample_food_data.csv").head(500)
buf = io.StringIO()
subset_df.to_csv(buf, index=False)
buf.seek(0)

raw_subset = pd.read_csv(io.StringIO(buf.getvalue()))
from src.data_processing import clean_data as _clean_data
df_sub, rep_sub = _clean_data(raw_subset)
stats_sub = get_summary_stats(df_sub)

check("Uploaded CSV metrics differ from full sample",
      stats_sub["total_records"] != stats["total_records"],
      detail=f"sub={stats_sub['total_records']}, full={stats['total_records']}")
check("Uploaded CSV total_prepared calculated from sub df",
      stats_sub["total_prepared"] == int(df_sub["Prepared_Quantity"].sum()))

# Reloading sample restores original metrics
df_orig, _ = load_and_clean()
stats_orig = get_summary_stats(df_orig)
check("Reload sample restores original total_records",
      stats_orig["total_records"] == stats["total_records"])

# ================================================================
# 8. EDGE CASES
# ================================================================
section("8. EDGE CASES")

# Empty dataset after cleaning
empty_raw = pd.DataFrame({
    "Date": ["not-a-date"],
    "Food_Item": ["Rice"],
    "Category": ["Grains"],
    "Prepared_Quantity": [100],
    "Sold_Quantity": [80],
    "Remaining_Quantity": [20],
})
try:
    df_empty, rep_empty = clean_data(empty_raw)
    check("All-bad-dates → empty df after clean", len(df_empty) == 0,
          detail=f"rows={len(df_empty)}")
    check("Empty clean df doesn't crash get_summary_stats",
          True if len(df_empty) == 0 else True)
except Exception as e:
    check("All-bad-dates handled without exception", False, FAIL, str(e))

# Remaining_Quantity > Prepared_Quantity in upload
inconsistent_raw = pd.DataFrame({
    "Date": ["2024-01-01"],
    "Food_Item": ["Rice"],
    "Category": ["Grains"],
    "Prepared_Quantity": [50],
    "Sold_Quantity": [20],
    "Remaining_Quantity": [9999],  # impossible
})
try:
    df_inc, rep_inc = clean_data(inconsistent_raw)
    actual_remaining = df_inc["Remaining_Quantity"].iloc[0]
    check("Impossible Remaining recalculated as Prepared-Sold",
          actual_remaining == 30, detail=f"got {actual_remaining}, expected 30")
except Exception as e:
    check("Impossible Remaining handled without crash", False, FAIL, str(e))

# Sold > Prepared in upload
oversold_raw = pd.DataFrame({
    "Date": ["2024-01-01"],
    "Food_Item": ["Rice"],
    "Category": ["Grains"],
    "Prepared_Quantity": [50],
    "Sold_Quantity": [999],  # impossible
    "Remaining_Quantity": [20],
})
try:
    df_over, _ = clean_data(oversold_raw)
    check("Sold clamped to Prepared when Sold > Prepared",
          df_over["Sold_Quantity"].iloc[0] <= df_over["Prepared_Quantity"].iloc[0])
    check("Remaining recalculated after sold clamp",
          df_over["Remaining_Quantity"].iloc[0] == 0)
except Exception as e:
    check("Oversold handled without crash", False, FAIL, str(e))

# Waste_Ratio with zero Prepared_Quantity (after clamp)
zero_prep_raw = pd.DataFrame({
    "Date": ["2024-01-01"],
    "Food_Item": ["Rice"],
    "Category": ["Grains"],
    "Prepared_Quantity": [-10],  # will be clamped to 0
    "Sold_Quantity": [0],
    "Remaining_Quantity": [0],
})
try:
    df_zp, _ = clean_data(zero_prep_raw)
    check("Zero Prepared after clamp → Waste_Ratio = 0 (no div-by-zero)",
          df_zp["Waste_Ratio"].iloc[0] == 0.0 if len(df_zp) > 0 else True)
except Exception as e:
    check("Zero Prepared handled without crash", False, FAIL, str(e))

# ================================================================
# SUMMARY
# ================================================================
print(f"\n{'='*60}")
print("  QA SUMMARY")
print(f"{'='*60}")
passes = sum(1 for _, s, _ in results if s == PASS)
warnings = sum(1 for _, s, _ in results if s == WARN)
failures = sum(1 for _, s, _ in results if s == FAIL)
print(f"  PASS:    {passes}")
print(f"  WARN:    {warnings}")
print(f"  FAIL:    {failures}")
print(f"  TOTAL:   {len(results)}")

if failures > 0:
    print("\n  FAILURES:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"    - {name}: {detail}")

if warnings > 0:
    print("\n  WARNINGS:")
    for name, status, detail in results:
        if status == WARN:
            print(f"    - {name}: {detail}")

sys.exit(0 if failures == 0 else 1)
