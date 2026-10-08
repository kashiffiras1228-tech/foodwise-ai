"""
src/recommendations.py
-----------------------
Generates action recommendations for food items based on:
  - Current waste-risk level
  - Surplus quantity
  - Expiry window
  - Food safety status
  - Predicted demand vs prepared quantity

Possible recommendations:
    Monitor             – low risk, no immediate action needed
    Reduce Preparation  – consistently over-preparing
    Controlled Discount – sell before expiry; surplus is moderate
    Redistribution Candidate – safe, significant surplus, suitable for sharing
    Discard (Unsafe)    – food-safety status indicates unsafe

Note: This system does NOT automatically declare food safe for donation.
It only flags *candidates* for redistribution based on available data.
"""

import pandas as pd
import numpy as np


# ------------------------------------------------------------------
# Action labels (keep consistent so downstream code can filter on them)
# ------------------------------------------------------------------
ACTION_MONITOR = "Monitor"
ACTION_REDUCE_PREP = "Reduce Preparation"
ACTION_DISCOUNT = "Controlled Discount"
ACTION_REDISTRIBUTE = "Redistribution Candidate"
ACTION_DISCARD = "Discard (Unsafe)"


def _single_recommendation(row: pd.Series) -> tuple[str, str]:
    """
    Determine action and rationale for one record.

    Returns (action: str, rationale: str).
    """
    risk = row.get("Waste_Risk", "Low")
    remaining = row.get("Remaining_Quantity", 0)
    expiry = row.get("Expiry_Hours", np.nan)
    safety = str(row.get("Food_Safety_Status", "Unknown")).strip()
    predicted_demand = row.get("Predicted_Demand", np.nan)
    prepared = row.get("Prepared_Quantity", 0)

    # --- 1. No surplus → Monitor ---
    if remaining <= 0:
        return ACTION_MONITOR, "No surplus detected."

    # --- 2. Unsafe food → Discard ---
    if safety.lower() == "unsafe":
        return ACTION_DISCARD, "Food safety status marked Unsafe."

    # --- 3. Compute over-prep ratio (how much more was prepared vs predicted) ---
    over_prep = np.nan
    if not np.isnan(predicted_demand) and predicted_demand > 0:
        over_prep = (prepared - predicted_demand) / predicted_demand

    # Short expiry flag
    short_expiry = (not np.isnan(expiry)) and (expiry <= 6)

    # --- 4. High risk decisions ---
    if risk == "High":
        if safety.lower() == "safe":
            if short_expiry:
                # Safe food but running out of time → discount first
                return (
                    ACTION_DISCOUNT,
                    f"High surplus ({remaining:.0f} units) with short expiry ({expiry:.0f}h). "
                    "Consider discounting to sell before expiry.",
                )
            else:
                return (
                    ACTION_REDISTRIBUTE,
                    f"High surplus ({remaining:.0f} units), food marked Safe. "
                    "Candidate for redistribution to eligible organisations.",
                )
        else:
            # Safety unknown/monitor with high surplus
            if short_expiry:
                return (
                    ACTION_DISCOUNT,
                    f"High surplus ({remaining:.0f} units), expiry within {expiry:.0f}h. "
                    "Attempt discounting; verify safety before any redistribution.",
                )
            else:
                return (
                    ACTION_MONITOR,
                    f"High surplus ({remaining:.0f} units). Safety unconfirmed — monitor closely.",
                )

    # --- 5. Medium risk decisions ---
    if risk == "Medium":
        if not np.isnan(over_prep) and over_prep > 0.15:
            return (
                ACTION_REDUCE_PREP,
                f"Consistently over-preparing by ~{over_prep*100:.0f}% vs predicted demand. "
                "Reduce preparation quantity going forward.",
            )
        if short_expiry and safety.lower() == "safe":
            return (
                ACTION_DISCOUNT,
                f"Moderate surplus ({remaining:.0f} units) with short expiry ({expiry:.0f}h). "
                "Offer a controlled discount.",
            )
        return ACTION_MONITOR, f"Moderate surplus ({remaining:.0f} units). Keep monitoring."

    # --- 6. Low risk → Monitor ---
    return ACTION_MONITOR, f"Low surplus ({remaining:.0f} units). No immediate action required."


def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Recommended_Action' and 'Action_Rationale' columns to the dataframe.

    Parameters
    ----------
    df : DataFrame with Waste_Risk, Remaining_Quantity, Expiry_Hours,
         Food_Safety_Status, and optionally Predicted_Demand columns.

    Returns
    -------
    DataFrame with two additional columns.
    """
    df = df.copy()
    actions = []
    rationales = []

    for _, row in df.iterrows():
        action, rationale = _single_recommendation(row)
        actions.append(action)
        rationales.append(rationale)

    df["Recommended_Action"] = actions
    df["Action_Rationale"] = rationales
    return df


def get_action_summary(df: pd.DataFrame) -> dict:
    """
    Count of each recommended action type and key aggregates.
    """
    if "Recommended_Action" not in df.columns:
        df = generate_recommendations(df)

    counts = df["Recommended_Action"].value_counts().to_dict()

    redistribute_df = df[df["Recommended_Action"] == ACTION_REDISTRIBUTE]

    return {
        "action_counts": counts,
        "redistribution_candidates": len(redistribute_df),
        "redistribution_units": int(redistribute_df["Remaining_Quantity"].sum()),
        "discard_records": counts.get(ACTION_DISCARD, 0),
        "reduce_prep_records": counts.get(ACTION_REDUCE_PREP, 0),
        "discount_records": counts.get(ACTION_DISCOUNT, 0),
    }


def get_item_action_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per food-item summary of most frequent recommended action and total surplus.
    """
    if "Recommended_Action" not in df.columns:
        df = generate_recommendations(df)

    summary = (
        df.groupby("Food_Item")
        .agg(
            Category=("Category", "first"),
            Total_Surplus=("Remaining_Quantity", "sum"),
            Dominant_Action=(
                "Recommended_Action",
                lambda x: x.value_counts().index[0],
            ),
            High_Risk_Days=("Waste_Risk", lambda x: (x == "High").sum()),
        )
        .reset_index()
        .sort_values("Total_Surplus", ascending=False)
    )
    return summary
