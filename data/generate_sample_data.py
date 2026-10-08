"""
Utility script to regenerate sample_food_data.csv.
Run: python data/generate_sample_data.py
"""
import pandas as pd
import numpy as np
from datetime import date, timedelta

rng = np.random.default_rng(42)

FOOD_ITEMS = {
    "Grains & Bread": ["Steamed Rice", "Chapati", "Bread Rolls", "Pasta", "Noodles"],
    "Vegetables": ["Mixed Veg Curry", "Stir-Fried Greens", "Potato Masala", "Cabbage Stir Fry"],
    "Protein": ["Dal (Lentils)", "Paneer Curry", "Egg Bhurji", "Chicken Curry", "Fish Fry"],
    "Snacks": ["Samosa", "Vada", "Spring Roll", "Pakora"],
    "Desserts": ["Kheer (Rice Pudding)", "Halwa", "Fruit Salad"],
    "Beverages": ["Lemonade", "Buttermilk", "Tea"],
}

BASE_DEMAND = {
    "Steamed Rice": 80, "Chapati": 70, "Bread Rolls": 50, "Pasta": 45, "Noodles": 40,
    "Mixed Veg Curry": 60, "Stir-Fried Greens": 35, "Potato Masala": 55, "Cabbage Stir Fry": 30,
    "Dal (Lentils)": 65, "Paneer Curry": 50, "Egg Bhurji": 45, "Chicken Curry": 70, "Fish Fry": 40,
    "Samosa": 60, "Vada": 50, "Spring Roll": 35, "Pakora": 45,
    "Kheer (Rice Pudding)": 30, "Halwa": 25, "Fruit Salad": 40,
    "Lemonade": 55, "Buttermilk": 50, "Tea": 80,
}

PRICE = {
    "Steamed Rice": 25, "Chapati": 10, "Bread Rolls": 15, "Pasta": 40, "Noodles": 35,
    "Mixed Veg Curry": 45, "Stir-Fried Greens": 35, "Potato Masala": 40, "Cabbage Stir Fry": 30,
    "Dal (Lentils)": 40, "Paneer Curry": 70, "Egg Bhurji": 55, "Chicken Curry": 90, "Fish Fry": 85,
    "Samosa": 15, "Vada": 12, "Spring Roll": 20, "Pakora": 18,
    "Kheer (Rice Pudding)": 30, "Halwa": 25, "Fruit Salad": 35,
    "Lemonade": 20, "Buttermilk": 15, "Tea": 10,
}

EXPIRY_HOURS = {
    "Steamed Rice": 6, "Chapati": 8, "Bread Rolls": 12, "Pasta": 6, "Noodles": 6,
    "Mixed Veg Curry": 8, "Stir-Fried Greens": 6, "Potato Masala": 8, "Cabbage Stir Fry": 6,
    "Dal (Lentils)": 10, "Paneer Curry": 8, "Egg Bhurji": 6, "Chicken Curry": 6, "Fish Fry": 4,
    "Samosa": 24, "Vada": 12, "Spring Roll": 12, "Pakora": 8,
    "Kheer (Rice Pudding)": 12, "Halwa": 24, "Fruit Salad": 6,
    "Lemonade": 24, "Buttermilk": 8, "Tea": 4,
}

records = []
start = date(2024, 1, 1)
end = date(2024, 9, 30)
current = start

while current <= end:
    dow = current.weekday()          # 0=Mon … 6=Sun
    is_weekend = dow >= 5
    month = current.month
    # Seasonal multiplier: higher in winter (Nov-Feb), slightly lower in summer
    season_mult = 1.15 if month in (11, 12, 1, 2) else (0.90 if month in (5, 6, 7) else 1.0)
    # Weekend multiplier: more footfall on weekends
    weekend_mult = 1.25 if is_weekend else 1.0

    for category, items in FOOD_ITEMS.items():
        for item in items:
            base = BASE_DEMAND[item]
            # Expected demand with noise
            demand = base * season_mult * weekend_mult
            demand += rng.normal(0, base * 0.12)          # ~12% noise
            demand = max(5, round(demand))

            # Canteen typically over-prepares by 10–30 %
            over_prep_pct = rng.uniform(0.10, 0.30)
            prepared = round(demand * (1 + over_prep_pct))

            # Sold is at most prepared, slightly less than demand sometimes
            sold = min(prepared, round(demand * rng.uniform(0.80, 1.00)))
            sold = max(0, sold)

            remaining = prepared - sold

            # Food-safety status: meat/fish perishes faster
            perishable = category == "Protein" and item in ("Chicken Curry", "Fish Fry", "Egg Bhurji")
            if remaining == 0:
                safety = "Safe"
            elif perishable and remaining > 10:
                safety = "Unsafe"
            elif EXPIRY_HOURS[item] <= 6 and remaining > 15:
                safety = "Monitor"
            else:
                safety = "Safe"

            records.append({
                "Date": current.strftime("%Y-%m-%d"),
                "Food_Item": item,
                "Category": category,
                "Prepared_Quantity": prepared,
                "Sold_Quantity": sold,
                "Remaining_Quantity": remaining,
                "Expiry_Hours": EXPIRY_HOURS[item],
                "Food_Safety_Status": safety,
                "Price": PRICE[item],
            })

    current += timedelta(days=1)

df = pd.DataFrame(records)
df.to_csv("data/sample_food_data.csv", index=False)
print(f"Generated {len(df)} records -> data/sample_food_data.csv")
