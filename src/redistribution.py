"""
src/redistribution.py
---------------------
Matches surplus-eligible food records to simulated recipient organisations.

IMPORTANT DISCLAIMER:
This is a prototype matching system for demonstration purposes only.
It does NOT connect to any real NGO, food bank, or donation network.
All recipient data is simulated.

Matching logic:
    1. Only records with Recommended_Action == "Redistribution Candidate" are considered.
    2. A recipient must accept the food's category.
    3. A recipient must have sufficient daily capacity remaining.
    4. Recipients are ranked by capacity (largest first) so higher-capacity
       organisations are suggested when multiple matches exist.
"""

import pandas as pd
from pathlib import Path

from src.recommendations import ACTION_REDISTRIBUTE

RECIPIENTS_PATH = Path(__file__).parent.parent / "data" / "sample_recipients.csv"


def load_recipients(source=None) -> pd.DataFrame:
    """Load the recipient organisations dataset."""
    path = source or RECIPIENTS_PATH
    df = pd.read_csv(path)
    # Parse Accepted_Categories into a list
    df["Accepted_Cat_List"] = df["Accepted_Categories"].apply(
        lambda x: [c.strip() for c in str(x).split(",")]
    )
    return df


def _category_match(category: str, accepted_list: list) -> bool:
    """Return True if the food category is in the recipient's accepted list."""
    return any(category.lower() == ac.lower() for ac in accepted_list)


def match_recipients(
    df: pd.DataFrame,
    recipients: pd.DataFrame,
    max_matches_per_record: int = 3,
) -> pd.DataFrame:
    """
    For each redistribution-candidate record, find up to
    `max_matches_per_record` suitable recipient organisations.

    Parameters
    ----------
    df           : recommendations DataFrame (must have Recommended_Action column)
    recipients   : loaded recipients DataFrame
    max_matches  : maximum number of recipient suggestions per record

    Returns
    -------
    DataFrame of (food record columns) + matched recipient columns.
    Each row = one (food record, recipient) pair.
    """
    candidates = df[df["Recommended_Action"] == ACTION_REDISTRIBUTE].copy()

    if candidates.empty:
        return pd.DataFrame()

    rows = []
    for _, food_row in candidates.iterrows():
        category = food_row["Category"]
        qty = food_row["Remaining_Quantity"]

        # Filter recipients by category compatibility and capacity
        matched = recipients[
            recipients["Accepted_Cat_List"].apply(
                lambda lst: _category_match(category, lst)
            )
            & (recipients["Capacity_Per_Day"] >= qty)
        ].copy()

        # Sort by capacity descending (prefer higher-capacity organisations)
        matched = matched.sort_values("Capacity_Per_Day", ascending=False)
        matched = matched.head(max_matches_per_record)

        for _, rec_row in matched.iterrows():
            rows.append({
                "Date": food_row["Date"],
                "Food_Item": food_row["Food_Item"],
                "Category": food_row["Category"],
                "Surplus_Units": food_row["Remaining_Quantity"],
                "Expiry_Hours": food_row.get("Expiry_Hours", "N/A"),
                "Food_Safety_Status": food_row.get("Food_Safety_Status", "Unknown"),
                "Organisation": rec_row["Organization_Name"],
                "Org_Type": rec_row["Organization_Type"],
                "City": rec_row["City"],
                "Capacity_Per_Day": rec_row["Capacity_Per_Day"],
                "Contact": rec_row["Contact"],
            })

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    return result.sort_values(["Date", "Food_Item"]).reset_index(drop=True)


def get_redistribution_summary(matches: pd.DataFrame) -> dict:
    """
    High-level summary of redistribution matches.
    """
    if matches.empty:
        return {
            "total_matches": 0,
            "unique_items": 0,
            "unique_orgs": 0,
            "total_eligible_units": 0,
        }

    return {
        "total_matches": len(matches),
        "unique_items": matches["Food_Item"].nunique(),
        "unique_orgs": matches["Organisation"].nunique(),
        "total_eligible_units": int(
            matches.drop_duplicates(subset=["Date", "Food_Item"])["Surplus_Units"].sum()
        ),
    }
