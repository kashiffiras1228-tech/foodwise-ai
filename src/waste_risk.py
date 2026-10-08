"""
src/waste_risk.py
-----------------
Calculates surplus quantity and assigns a waste-risk level to each record.

Risk classification is rule-based and transparent so it can be explained
easily during a student presentation.

Risk levels:
    Low     – small remaining quantity and/or long expiry window
    Medium  – moderate remaining quantity or moderate expiry risk
    High    – large remaining quantity and/or very short expiry window
"""

import pandas as pd
import numpy as np


# ------------------------------------------------------------------
# Thresholds — adjust these if you have domain-specific knowledge.
# These are expressed as fractions of Prepared_Quantity (waste ratio).
# ------------------------------------------------------------------
WASTE_RATIO_LOW_THRESHOLD = 0.10     # <= 10 %  remaining → Low
WASTE_RATIO_HIGH_THRESHOLD = 0.30    # >= 30 %  remaining → High (otherwise Medium)

# Absolute quantity thresholds (used in conjunction with ratio)
ABS_HIGH_THRESHOLD = 20              # remaining >= 20 units → at least Medium

# Short expiry: if Expiry_Hours <= this, risk is elevated
SHORT_EXPIRY_HOURS = 6


def calculate_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'Waste_Risk' column (Low / Medium / High) and supporting
    columns to the dataframe.

    Parameters
    ----------
    df : cleaned DataFrame from data_processing.clean_data()

    Returns
    -------
    DataFrame with extra columns:
        Waste_Risk          – str: Low / Medium / High
        Risk_Reason         – str: human-readable explanation
        Surplus_Value       – float: Remaining_Quantity * Price (if Price present)
    """
    df = df.copy()

    # Waste ratio already computed in data_processing; recalculate if absent
    if "Waste_Ratio" not in df.columns:
        df["Waste_Ratio"] = np.where(
            df["Prepared_Quantity"] > 0,
            df["Remaining_Quantity"] / df["Prepared_Quantity"],
            0.0,
        )

    has_expiry = "Expiry_Hours" in df.columns
    has_price = "Price" in df.columns

    risk_list = []
    reason_list = []

    for _, row in df.iterrows():
        remaining = row["Remaining_Quantity"]
        ratio = row["Waste_Ratio"]
        expiry = row.get("Expiry_Hours", np.nan) if has_expiry else np.nan

        reasons = []

        # --- Determine base risk from waste ratio ---
        if ratio <= WASTE_RATIO_LOW_THRESHOLD and remaining < ABS_HIGH_THRESHOLD:
            base_risk = "Low"
            reasons.append(f"{ratio*100:.0f}% remaining (low)")
        elif ratio >= WASTE_RATIO_HIGH_THRESHOLD or remaining >= ABS_HIGH_THRESHOLD:
            base_risk = "High"
            reasons.append(f"{ratio*100:.0f}% remaining ({remaining:.0f} units)")
        else:
            base_risk = "Medium"
            reasons.append(f"{ratio*100:.0f}% remaining")

        # --- Escalate risk if expiry is very short ---
        if not np.isnan(expiry) and expiry <= SHORT_EXPIRY_HOURS and remaining > 5:
            if base_risk == "Low":
                base_risk = "Medium"
            elif base_risk == "Medium":
                base_risk = "High"
            reasons.append(f"short expiry ({expiry:.0f}h)")

        # --- Zero remaining always Low ---
        if remaining == 0:
            base_risk = "Low"
            reasons = ["no surplus"]

        risk_list.append(base_risk)
        reason_list.append("; ".join(reasons) if reasons else "")

    df["Waste_Risk"] = risk_list
    df["Risk_Reason"] = reason_list

    # Surplus monetary value (if Price is available)
    if has_price:
        df["Surplus_Value"] = (df["Remaining_Quantity"] * df["Price"]).round(2)
    else:
        df["Surplus_Value"] = np.nan

    return df


def get_risk_summary(df: pd.DataFrame) -> dict:
    """
    Aggregate risk-level counts and key metrics.
    """
    if "Waste_Risk" not in df.columns:
        df = calculate_risk(df)

    counts = df["Waste_Risk"].value_counts().to_dict()

    high_risk_items = (
        df[df["Waste_Risk"] == "High"]
        .groupby("Food_Item")
        .agg(
            Avg_Remaining=("Remaining_Quantity", "mean"),
            Avg_Waste_Ratio=("Waste_Ratio", "mean"),
            Occurrences=("Waste_Risk", "count"),
        )
        .sort_values("Avg_Remaining", ascending=False)
        .reset_index()
    )

    return {
        "low_count": counts.get("Low", 0),
        "medium_count": counts.get("Medium", 0),
        "high_count": counts.get("High", 0),
        "high_risk_items": high_risk_items,
        "total_surplus_units": int(df["Remaining_Quantity"].sum()),
        "avg_waste_ratio_pct": round(df["Waste_Ratio"].mean() * 100, 1),
    }


def get_category_risk_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-category summary of waste risk metrics.
    """
    if "Waste_Risk" not in df.columns:
        df = calculate_risk(df)

    profile = (
        df.groupby("Category")
        .agg(
            Total_Prepared=("Prepared_Quantity", "sum"),
            Total_Sold=("Sold_Quantity", "sum"),
            Total_Remaining=("Remaining_Quantity", "sum"),
            Avg_Waste_Ratio=("Waste_Ratio", "mean"),
            High_Risk_Records=("Waste_Risk", lambda x: (x == "High").sum()),
        )
        .reset_index()
    )
    profile["Waste_Ratio_Pct"] = (profile["Avg_Waste_Ratio"] * 100).round(1)
    return profile.sort_values("Total_Remaining", ascending=False)
