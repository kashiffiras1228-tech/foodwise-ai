"""
Quick targeted checks for the 3 flagged issues.
"""
import io
import sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

from src.data_processing import clean_data

print("=== Test A: Negative value counter with valid date ===")
# All rows have valid dates — negative should be counted
raw_neg = pd.DataFrame({
    "Date": ["2024-01-01", "2024-01-02"],
    "Food_Item": ["Rice", "Dal"],
    "Category": ["Grains", "Protein"],
    "Prepared_Quantity": [100, 80],
    "Sold_Quantity": [-5, 60],  # row 0 has negative
    "Remaining_Quantity": [20, 20],
})
df_neg, rpt_neg = clean_data(raw_neg)
print(f"  negatives_fixed={rpt_neg['negative_values_fixed']}")
print(f"  Sold row 0 after clean: {df_neg['Sold_Quantity'].iloc[0]}")
print(f"  PASS" if rpt_neg["negative_values_fixed"] >= 1 else "  FAIL - counter not incremented")

print()
print("=== Test B: All-bad-dates CSV ===")
bad_csv = pd.DataFrame({
    "Date": ["not-a-date"],
    "Food_Item": ["Rice"],
    "Category": ["Grains"],
    "Prepared_Quantity": [100],
    "Sold_Quantity": [80],
    "Remaining_Quantity": [20],
})
try:
    df_bad, rpt_bad = clean_data(bad_csv)
    print(f"  No exception raised. Rows after clean: {len(df_bad)}")
    print(f"  date_failures={rpt_bad['date_parse_failures']}")
    print(f"  PASS - handled gracefully, no crash")
except Exception as e:
    print(f"  EXCEPTION: {type(e).__name__}: {e}")

print()
print("=== Test C: Zero Prepared_Quantity after negative clamp ===")
zero_prep = pd.DataFrame({
    "Date": ["2024-01-01"],
    "Food_Item": ["Rice"],
    "Category": ["Grains"],
    "Prepared_Quantity": [-10],  # clamped to 0
    "Sold_Quantity": [0],
    "Remaining_Quantity": [0],
})
try:
    df_zp, rpt_zp = clean_data(zero_prep)
    print(f"  No exception. Rows: {len(df_zp)}")
    if len(df_zp) > 0:
        print(f"  Prepared={df_zp['Prepared_Quantity'].iloc[0]}")
        print(f"  Waste_Ratio={df_zp['Waste_Ratio'].iloc[0]}")
        print(f"  PASS - no div-by-zero" if df_zp['Waste_Ratio'].iloc[0] == 0.0 else "  FAIL - non-zero waste ratio for zero prepared")
except Exception as e:
    print(f"  EXCEPTION: {type(e).__name__}: {e}")

print()
print("=== Test D: Original test script false failure ===")
print("  The 'negative qty clamped' test in test_qa.py used a CSV where")
print("  the ONLY row with a negative value (-5 sold) ALSO had an invalid")
print("  date ('not-a-date'), so that row was dropped in step 2 (date parse)") 
print("  BEFORE reaching step 6 (negative clamping).")
print("  This is CORRECT behaviour — bad-date rows are dropped first.")
print("  Counter = 0 is correct for that specific input.")
print("  VERDICT: False failure in test. Application logic is correct.")

print()
print("=== Test E: Date parsing UserWarning ===")
print("  Stderr showed: UserWarning from pd.to_datetime without format=...")
print("  This is a pandas 2.x deprecation advisory, not an error.")
print("  Fix: specify format='mixed' or format='ISO8601' for flexibility.")
