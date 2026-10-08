# 🌿 FoodWise AI

**AI-Powered Food Waste Prediction, Surplus Detection & Redistribution Support Platform**

> IBM SkillsBuild Internship — Student Project  
> Python · Streamlit · scikit-learn · Plotly · Pandas

---

## Project Overview

FoodWise AI is an AI-powered **decision-support prototype** designed to help food-serving
organisations — such as canteens, cloud kitchens, and school cafeterias — make better
decisions about food preparation and surplus management.

Using historical food-preparation records, the application:

- Predicts expected demand for each menu item using machine learning
- Detects potential surplus and assigns a transparent waste-risk level
- Recommends appropriate actions (reduce preparation, apply a discount, flag for redistribution)
- Matches surplus-eligible food to simulated community recipient organisations
- Presents a sustainability insights dashboard aligned with SDG 12 Target 12.3

FoodWise AI is a **prototype and decision-support tool**. It does not autonomously
manage inventory, sell food, perform redistribution, or certify food safety.
All outputs are recommendations that require human verification before any action is taken.

---

## SDG Alignment

### Primary — SDG 12: Responsible Consumption and Production

| | |
|---|---|
| **Goal** | SDG 12 — Responsible Consumption and Production |
| **Target** | 12.3 — By 2030, halve per-capita global food waste at the retail and consumer levels and reduce food losses along production and supply chains |
| **Relevance** | FoodWise AI helps food-serving organisations identify over-preparation, detect surplus risk early, and act before food becomes waste |

### Potential Secondary — SDG 2: Zero Hunger

The redistribution support feature identifies surplus food that *may* be eligible for
sharing with community organisations. This represents a **potential secondary contribution**
to SDG 2 in a real-world deployment. It does **not** mean this prototype solves hunger,
and no donation or redistribution is performed by the system. Food safety must be
independently verified before any actual redistribution takes place.

---

## Problem Statement

Food waste is a global sustainability challenge. According to the UN Food and Agriculture
Organisation, approximately one-third of all food produced for human consumption is lost or
wasted each year. Food-serving organisations frequently over-prepare meals due to demand
uncertainty, resulting in significant daily surplus that often ends up as waste.

The root causes include:

- **Demand uncertainty** — no systematic prediction of how much food will be sold on a
  given day
- **Late detection** — surplus is identified too late to act on (discount, redistribute)
- **No decision framework** — staff lack a structured tool to decide what to do with surplus

---

## Proposed Solution

FoodWise AI addresses these causes through a data-driven pipeline:

1. **Demand forecasting** — a machine learning model predicts expected sales quantity per
   item, reducing guesswork about how much to prepare
2. **Risk scoring** — a transparent rule-based system assigns a waste-risk level
   (Low / Medium / High) to each item based on surplus ratio and expiry window
3. **Action recommendations** — the system suggests a specific action for each item:
   reduce preparation, offer a controlled discount, flag as a redistribution candidate,
   or monitor
4. **Redistribution matching** — surplus flagged as eligible is matched against a
   simulated dataset of community organisations based on food category and capacity

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Data Input** | Load the bundled sample dataset or upload your own CSV file |
| **Data Validation & Cleaning** | Detects and handles missing values, unparseable dates, negative quantities, and impossible quantity relationships (e.g. Sold > Prepared) |
| **Analytics Dashboard** | Interactive charts showing demand trends, prepared vs sold vs surplus, category breakdowns, day-of-week patterns, and top-surplus items |
| **ML Demand Prediction** | Random Forest Regressor predicts Sold_Quantity per item per day; evaluated on a held-out time-based test set |
| **Surplus & Waste Risk** | Transparent rule-based scoring assigns Low / Medium / High risk; risk does not imply food unsafety |
| **Action Recommendations** | Five action labels — Monitor, Reduce Preparation, Controlled Discount, Redistribution Candidate, Discard (Unsafe) — derived per record from risk level, expiry, and food safety status |
| **Redistribution Support** | Matches redistribution-candidate records to simulated recipient organisations by food category and capacity |
| **Sustainability Insights** | KPI dashboard showing estimated surplus, high-risk records, redistribution candidates, and model evaluation metrics — all framed as estimates from demo data |

---

## System Workflow

```
Data Input (CSV / sample)
        │
        ▼
Data Cleaning & Validation
  • Parse dates (format="mixed")
  • Coerce numeric columns
  • Clamp negative quantities
  • Cap Sold ≤ Prepared
  • Recalculate Remaining = Prepared − Sold
  • Fill optional columns (Expiry_Hours, Food_Safety_Status, Price)
  • Derive date features (DayOfWeek, Month, IsWeekend, Week)
        │
        ▼
Analytics (Exploratory Data Analysis)
  • Daily / weekly / monthly trends
  • Category and item breakdowns
        │
        ▼
Demand Prediction
  • Random Forest Regressor
  • Features: Food_Item, Category, DayOfWeek, Month, IsWeekend
  • Time-based 80/20 train/test split
  • Outputs: Predicted_Demand, Predicted_Surplus
        │
        ▼
Surplus & Waste Risk Scoring
  • Waste_Ratio = Remaining ÷ Prepared
  • Low  (≤10% remaining, < 20 units)
  • Medium (10–30% remaining or ≥ 20 units)
  • High (≥30% remaining or ≥ 20 units)
  • Short expiry (≤6 h) escalates risk one level
        │
        ▼
Action Recommendations
  • Monitor
  • Reduce Preparation
  • Controlled Discount
  • Redistribution Candidate  ← only when Safety = Safe AND Risk = High
  • Discard (Unsafe)          ← only when Food_Safety_Status = Unsafe
        │
        ▼
Redistribution Support
  • Filters: Redistribution Candidate records only
  • Matches by food category compatibility and daily capacity
  • Returns up to 3 recipient suggestions per record
  • All recipient data is SIMULATED
        │
        ▼
Sustainability Insights Dashboard
  • Estimated surplus totals, risk counts, redistribution candidates
  • Model evaluation metrics
  • SDG 12.3 framing
```

---

## Technology Stack

| Component | Library / Tool | Version (installed) |
|-----------|---------------|---------------------|
| Web interface | Streamlit | 1.65.0 |
| Data manipulation | Pandas | 3.0.6 |
| Numerical computing | NumPy | 2.5.3 |
| Machine learning | scikit-learn | 1.9.1 |
| Visualisation | Plotly | 7.1.0 |
| Model persistence | Joblib | 1.6.0 |
| Python version | CPython | 3.12.14 |
| Environment manager | uv | — |

**Runtime requirements** (`requirements.txt`):

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.26.0
scikit-learn>=1.4.0
plotly>=5.18.0
joblib>=1.3.0
```

---

## Machine Learning Model

### Algorithm

**Random Forest Regressor** (`sklearn.ensemble.RandomForestRegressor`)

- 100 decision trees, max depth 10, random state 42
- Falls back to a pure-NumPy Item-Adjusted Linear Model if scikit-learn's compiled
  extensions are unavailable (e.g. due to system security policies)

### Features

| Feature | Description |
|---------|-------------|
| `Food_Item_enc` | Label-encoded food item identifier |
| `Category_enc` | Label-encoded food category |
| `DayOfWeek` | 0 = Monday … 6 = Sunday |
| `Month` | 1–12 |
| `IsWeekend` | 1 if Saturday or Sunday, else 0 |

**Target:** `Sold_Quantity` (units sold on a given day)

### Train / Test Split

- **Method:** Time-based (chronological) — earlier dates for training, later dates for
  testing. This avoids data leakage from future observations into the training set.
- **Split:** 80 % train / 20 % test

### Prototype Evaluation Results

> ⚠️ **Important:** The figures below are prototype evaluation results obtained entirely
> using a **synthetic/demo dataset**. They must **not** be interpreted as production
> performance, real-world forecasting accuracy, or any measured reduction in actual food
> waste. Performance on real operational data will differ.

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **MAE** | **5.80 units** | Average absolute error between predicted and actual sold quantity |
| **RMSE** | **7.49 units** | Root mean squared error (penalises larger errors more) |
| **R²** | **0.797** | ~80% of variance in sold quantity explained by the model features |

---

## Data Handling

### Sample Dataset (`data/sample_food_data.csv`)

A synthetic dataset generated by `data/generate_sample_data.py`.

| Property | Value |
|----------|-------|
| Date range | 1 January 2024 – 30 September 2024 |
| Total records | 6,576 |
| Food items | 24 |
| Categories | 6 (Grains & Bread, Vegetables, Protein, Snacks, Desserts, Beverages) |
| Total prepared (demo) | 424,968 units |
| Total sold (demo) | 318,531 units |
| Est. surplus (demo) | 106,437 units (25.0% of prepared) |

**Dataset columns:**

| Column | Type | Description |
|--------|------|-------------|
| `Date` | date | Date of food preparation |
| `Food_Item` | string | Name of the food item |
| `Category` | string | Food category |
| `Prepared_Quantity` | int | Units prepared |
| `Sold_Quantity` | int | Units sold |
| `Remaining_Quantity` | int | Units unsold (re-derived as Prepared − Sold after cleaning) |
| `Expiry_Hours` | float | Approximate shelf life in hours |
| `Food_Safety_Status` | string | Safe / Monitor / Unsafe (rule-based, for demo purposes) |
| `Price` | float | Unit price (₹) |

> All data is **entirely synthetic**. It does not represent any real restaurant, canteen,
> organisation, or operational system.

### CSV Upload

Users may upload their own CSV file via the sidebar. The application validates that all
required columns are present (`Date`, `Food_Item`, `Category`, `Prepared_Quantity`,
`Sold_Quantity`, `Remaining_Quantity`) and reports missing columns clearly. The cleaning
pipeline then handles:

- Unparseable dates (rows are dropped; count reported)
- Non-numeric values in quantity columns (coerced to NaN and dropped)
- Negative quantities (clamped to 0; count reported)
- `Sold_Quantity > Prepared_Quantity` (Sold clamped to Prepared)
- `Remaining_Quantity` is always recalculated from `Prepared − Sold` to ensure consistency

### Simulated Recipients (`data/sample_recipients.csv`)

10 fictional recipient organisations covering 6 Indian cities (Mumbai, Delhi, Bangalore,
Pune, Chennai, Hyderabad). Fields: `Organization_Name`, `Organization_Type`, `City`,
`Capacity_Per_Day`, `Accepted_Categories`, `Contact`.

Organisation types represented: NGO / Community Kitchen, NGO / Food Bank,
Shelter / Welfare Home, Elderly Care, Orphanage, Community Centre,
Medical / Health Camp, Skill / Training Centre.

---

## Redistribution Support

> ⚠️ **Prototype Disclaimer:** The redistribution matching feature is a **simulated
> demonstration system** for prototype purposes only. It does **not** connect to any real
> NGO, food bank, or donation network. All recipient organisations and contact details
> are entirely fictional.

### How matching works

1. Only records with `Recommended_Action = "Redistribution Candidate"` are considered.
   A record reaches this action only when `Food_Safety_Status = Safe` **and**
   `Waste_Risk = High` **and** `Expiry_Hours > 6`.
2. Recipients are filtered by food category compatibility.
3. Recipients are filtered to those whose `Capacity_Per_Day >= Surplus_Units`.
4. Up to 3 recipients are suggested per record, ranked by capacity (highest first).

### Food safety

FoodWise AI does **not** autonomously certify food as safe for donation or redistribution.
The `Food_Safety_Status` column in the sample dataset is a rule-based label generated for
demonstration purposes. In any real deployment, food safety assessment must be performed
by qualified food-safety personnel according to applicable local regulations.

---

## Limitations

| # | Limitation |
|---|-----------|
| 1 | All analytics and ML results are based on a **synthetic dataset** and are for demonstration only |
| 2 | No real-time integration with restaurant POS systems, inventory management, or IoT sensors |
| 3 | No integration with real NGO, food-bank, or redistribution networks |
| 4 | Food safety is **not** autonomously certified; `Food_Safety_Status` is a rule-based demo label |
| 5 | ML model trained on synthetic data — real-world forecasting accuracy requires real operational data |
| 6 | Does not account for food weight, portion sizes, or caloric content |
| 7 | Redistribution matching is simulated — capacity figures and categories are fictional |
| 8 | Recommendation engine is a decision-support tool; all suggestions require human review |
| 9 | No multi-location, multi-organisation, or user authentication support |

---

## Future Scope

Potential enhancements for a production deployment:

| Area | Description |
|------|-------------|
| Real data | Integration with operational POS, inventory, or ERP systems |
| Improved forecasting | LSTM / time-series models; weather and event features |
| Real-time monitoring | Live inventory tracking via IoT sensors or API polling |
| Verified redistribution | Partnerships with real NGOs and food banks with API integration |
| Notifications | Alerts for high-risk surplus approaching expiry |
| Location matching | Geospatial distance-based recipient matching |
| AI explanations | Responsible IBM watsonx / LLM explanation layer for recommendations |
| Reporting | Automated PDF / Excel export for management review |
| Authentication | Role-based dashboards for canteen staff vs. managers |

---

## Installation

### Requirements

- Windows (PowerShell) or macOS / Linux
- [uv](https://github.com/astral-sh/uv) — fast Python package and environment manager
- Internet connection for first install (packages downloaded once)

### Step 1 — Clone or download the project

```powershell
cd C:\Users\YourName\Desktop
# Place the foodwise-ai folder here
cd foodwise-ai
```

### Step 2 — Install Python 3.12 via uv (if not already installed)

```powershell
uv python install 3.12
```

### Step 3 — Create the virtual environment

```powershell
uv venv .venv --python 3.12
```

### Step 4 — Install dependencies

```powershell
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

### Step 5 — (Optional) Regenerate the sample dataset

```powershell
.venv\Scripts\python.exe data\generate_sample_data.py
```

---

## Running the Application

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

The application opens automatically in your browser at:

```
http://localhost:8501
```

Alternatively, activate the virtual environment first:

```powershell
.venv\Scripts\activate
python -m streamlit run app.py
```

---

## Usage

### Navigation

Use the **sidebar radio buttons** to move between sections:

| Section | What it shows |
|---------|--------------|
| 🏠 Home & Overview | KPI summary, SDG alignment, data overview |
| 📂 Data & Quality | Data quality report, preview, descriptive statistics |
| 📊 Analytics | Interactive EDA charts with date-range filter |
| 🤖 Demand Prediction | Model metrics, feature importance, predicted vs actual |
| ⚠️ Surplus & Waste Risk | Risk distribution, category profile, heatmap |
| 💡 Action Recommendations | Action counts, per-item summary, filterable detail table |
| 🤝 Redistribution Support | Simulated recipient orgs, match results |
| 🌍 Sustainability Insights | SDG dashboard, surplus trend, model metrics |

### Data source

- **Use sample dataset** (default) — loads the bundled `data/sample_food_data.csv`
  automatically on startup
- **Upload my CSV** — select "Upload my CSV" in the sidebar, then choose a `.csv` file.
  The application validates required columns and reports any issues. Switching back to
  "Use sample dataset" restores the original data and clears all cached pipeline results.

### Required columns for CSV upload

`Date`, `Food_Item`, `Category`, `Prepared_Quantity`, `Sold_Quantity`,
`Remaining_Quantity`

Optional columns (used when present): `Expiry_Hours`, `Food_Safety_Status`, `Price`

---

## Project Structure

```
foodwise-ai/
│
├── app.py                        # Main Streamlit application (8 pages)
├── requirements.txt              # Python package dependencies
├── README.md                     # This file
│
├── data/
│   ├── sample_food_data.csv      # Synthetic food-preparation records (6,576 rows)
│   ├── sample_recipients.csv     # Simulated recipient organisations (10 rows)
│   └── generate_sample_data.py   # Script to regenerate sample_food_data.csv
│
├── src/
│   ├── data_processing.py        # CSV loading, column validation, cleaning pipeline
│   ├── forecasting.py            # RandomForestRegressor demand prediction + NumPy fallback
│   ├── waste_risk.py             # Rule-based Low/Medium/High surplus risk scoring
│   ├── recommendations.py        # Action recommendation engine (5 action labels)
│   └── redistribution.py        # Simulated recipient-matching logic
│
├── models/                       # Saved model files (populated at runtime if joblib used)
│
└── .venv/                        # Python 3.12 virtual environment (not committed to git)
```

**Test / validation scripts** (development artefacts, not required to run the app):

```
test_pipeline.py      # Quick end-to-end pipeline smoke test
test_validate.py      # Full pipeline validation with assertions
test_qa.py            # 100-check functional QA test suite (98 PASS, 0 FAIL)
test_edge_cases.py    # Targeted edge-case tests for data cleaning
```

---

## QA Status

| Check | Result |
|-------|--------|
| Total automated checks | 100 |
| **PASS** | **98** |
| **FAIL** | **0** |
| Informational warnings | 2 (see below) |
| Streamlit health check | HTTP 200 ✅ |

**Informational warnings (non-blocking):**

1. The sample dataset contains no rows with `Prepared_Quantity = 0`, so the
   division-by-zero guard in `Waste_Ratio` calculation cannot be live-tested against
   the sample data. The guard is present and verified by an isolated edge-case test.
2. `Waste_Risk` and `Food_Safety_Status` are intentionally independent concepts.
   Risk scoring uses only `Waste_Ratio` and `Expiry_Hours`; food safety flows only into
   the recommendations layer. This is correct design, confirmed by code review.

**The MVP passed the completed functional QA and is ready for demonstration.**

---

## Responsible Claims

FoodWise AI is a **student prototype** built for the IBM SkillsBuild Internship programme.

The following claims are explicitly **not** made by this application:

- ❌ It has reduced real-world food waste
- ❌ It has performed actual food donation or redistribution
- ❌ It certifies food as safe for human consumption
- ❌ Its ML metrics represent production forecasting performance
- ❌ It has produced any quantified environmental impact (CO₂, meals served, money saved)
- ❌ Recipient organisations are real and the contact details are operational

The application is accurately described as:

> An **AI-powered decision-support prototype** that helps food-serving organisations
> identify potential surplus, understand demand patterns, and consider appropriate
> actions — in support of the objectives of **SDG 12 Target 12.3**.

---

## Acknowledgements

Built as a student prototype for the **IBM SkillsBuild Internship** programme.

Primary SDG alignment: **SDG 12 — Responsible Consumption and Production**  
Specific target: **Target 12.3 — Food Loss and Waste Reduction**

All data, organisations, contact details, and impact figures used in this application
are simulated and exist solely for demonstration purposes.
