"""
src/data_processing.py
----------------------
Handles loading, validating and cleaning the food-waste dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ------------------------------------------------------------------
# Required columns and their expected dtypes (post-conversion)
# ------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "Date",
    "Food_Item",
    "Category",
    "Prepared_Quantity",
    "Sold_Quantity",
    "Remaining_Quantity",
]

OPTIONAL_COLUMNS = [
    "Expiry_Hours",
    "Food_Safety_Status",
    "Price",
]

NUMERIC_COLUMNS = [
    "Prepared_Quantity",
    "Sold_Quantity",
    "Remaining_Quantity",
    "Expiry_Hours",
    "Price",
]

DEFAULT_SAMPLE_PATH = Path(__file__).parent.parent / "data" / "sample_food_data.csv"


def load_data(source) -> pd.DataFrame:
    """
    Load data from a file path (str/Path) or a Streamlit UploadedFile object.
    Returns a raw DataFrame before cleaning.
    """
    if isinstance(source, (str, Path)):
        df = pd.read_csv(source)
    else:
        # Streamlit UploadedFile – rewind to start before reading
        source.seek(0)
        df = pd.read_csv(source)
    return df


def validate_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Check that all required columns are present (case-insensitive match).
    Returns (ok: bool, missing_columns: list).
    """
    df_cols_lower = [c.lower() for c in df.columns]
    missing = [
        col for col in REQUIRED_COLUMNS
        if col.lower() not in df_cols_lower
    ]
    return (len(missing) == 0), missing


def _coerce_numeric(series: pd.Series) -> pd.Series:
    """Convert a column to numeric, replacing non-parseable values with NaN."""
    return pd.to_numeric(series, errors="coerce")


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean and normalise the raw DataFrame.

    Returns
    -------
    cleaned_df : pd.DataFrame
        Cleaned data, ready for analysis.
    quality_report : dict
        Summary of data-quality actions taken.
    """
    report = {
        "original_rows": len(df),
        "duplicate_rows_removed": 0,
        "rows_with_missing_required": 0,
        "negative_values_fixed": 0,
        "inconsistent_remaining_fixed": 0,
        "date_parse_failures": 0,
    }

    df = df.copy()

    # ---- 1. Standardise column names (strip whitespace) ----------------
    df.columns = [c.strip() for c in df.columns]

    # ---- 2. Parse dates ------------------------------------------------
    # format="mixed" allows ISO8601 and common date strings without a noisy
    # pandas UserWarning about inferred formats (pandas 2.x advisory).
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", format="mixed")
    bad_dates = df["Date"].isna().sum()
    report["date_parse_failures"] = int(bad_dates)
    df = df.dropna(subset=["Date"])  # rows with unparseable dates are dropped

    # ---- 3. Convert numeric columns ------------------------------------
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = _coerce_numeric(df[col])

    # ---- 4. Drop rows where required numeric columns are all missing ---
    required_numeric = ["Prepared_Quantity", "Sold_Quantity", "Remaining_Quantity"]
    before = len(df)
    df = df.dropna(subset=[c for c in required_numeric if c in df.columns])
    report["rows_with_missing_required"] = before - len(df)

    # ---- 5. Remove exact duplicate rows --------------------------------
    before = len(df)
    df = df.drop_duplicates()
    report["duplicate_rows_removed"] = before - len(df)

    # ---- 6. Fix negative quantities (clamp to 0) -----------------------
    for col in ["Prepared_Quantity", "Sold_Quantity", "Remaining_Quantity"]:
        if col in df.columns:
            negatives = (df[col] < 0).sum()
            report["negative_values_fixed"] += int(negatives)
            df[col] = df[col].clip(lower=0)

    # ---- 7. Ensure Sold_Quantity <= Prepared_Quantity ------------------
    if "Sold_Quantity" in df.columns and "Prepared_Quantity" in df.columns:
        excess = (df["Sold_Quantity"] > df["Prepared_Quantity"]).sum()
        report["inconsistent_remaining_fixed"] += int(excess)
        df["Sold_Quantity"] = df[["Sold_Quantity", "Prepared_Quantity"]].min(axis=1)

    # ---- 8. Recalculate Remaining_Quantity for consistency -------------
    #  We trust Prepared and Sold as ground truth; re-derive Remaining.
    if "Prepared_Quantity" in df.columns and "Sold_Quantity" in df.columns:
        df["Remaining_Quantity"] = (
            df["Prepared_Quantity"] - df["Sold_Quantity"]
        ).clip(lower=0)

    # ---- 9. Fill optional columns with sensible defaults ---------------
    if "Expiry_Hours" in df.columns:
        # Fill missing expiry with median expiry of that food category
        df["Expiry_Hours"] = df.groupby("Category")["Expiry_Hours"].transform(
            lambda x: x.fillna(x.median())
        )
        df["Expiry_Hours"] = df["Expiry_Hours"].fillna(12)  # global fallback

    if "Food_Safety_Status" not in df.columns:
        df["Food_Safety_Status"] = "Unknown"
    else:
        df["Food_Safety_Status"] = df["Food_Safety_Status"].fillna("Unknown")

    if "Price" in df.columns:
        df["Price"] = df["Price"].fillna(df["Price"].median())

    # ---- 10. Derived date features (useful for ML & EDA) ---------------
    df["DayOfWeek"] = df["Date"].dt.dayofweek          # 0=Mon, 6=Sun
    df["DayName"] = df["Date"].dt.day_name()
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.month_name()
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6]).astype(int)
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)

    # ---- 11. Waste ratio (fraction of prepared that was not sold) ------
    df["Waste_Ratio"] = np.where(
        df["Prepared_Quantity"] > 0,
        df["Remaining_Quantity"] / df["Prepared_Quantity"],
        0.0,
    )

    report["final_rows"] = len(df)
    report["rows_removed_total"] = report["original_rows"] - report["final_rows"]

    df = df.sort_values("Date").reset_index(drop=True)
    return df, report


def load_and_clean(source=None) -> tuple[pd.DataFrame, dict]:
    """
    Convenience wrapper: load + validate + clean in one call.
    Falls back to the bundled sample data if source is None.
    """
    if source is None:
        source = DEFAULT_SAMPLE_PATH

    raw = load_data(source)
    ok, missing = validate_columns(raw)
    if not ok:
        raise ValueError(
            f"Uploaded file is missing required columns: {missing}. "
            f"Required: {REQUIRED_COLUMNS}"
        )

    cleaned, report = clean_data(raw)
    return cleaned, report


def get_summary_stats(df: pd.DataFrame) -> dict:
    """
    Compute high-level summary statistics for the dashboard.
    """
    total_prepared = df["Prepared_Quantity"].sum()
    total_sold = df["Sold_Quantity"].sum()
    total_remaining = df["Remaining_Quantity"].sum()
    waste_pct = (total_remaining / total_prepared * 100) if total_prepared > 0 else 0.0

    return {
        "total_records": len(df),
        "unique_items": df["Food_Item"].nunique(),
        "unique_categories": df["Category"].nunique(),
        "date_range_start": df["Date"].min().strftime("%d %b %Y"),
        "date_range_end": df["Date"].max().strftime("%d %b %Y"),
        "total_prepared": int(total_prepared),
        "total_sold": int(total_sold),
        "total_remaining": int(total_remaining),
        "overall_waste_pct": round(waste_pct, 1),
    }
