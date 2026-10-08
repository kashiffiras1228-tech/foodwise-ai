"""
app.py
------
FOODWISE AI — AI-Powered Food Waste Prediction, Surplus Detection &
Redistribution Support Platform.

Run:
    streamlit run app.py

Project context:
    IBM SkillsBuild Internship — Student Project
    Primary SDG: SDG 12 — Responsible Consumption and Production
    Target: 12.3 — Food Loss and Waste Reduction
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Local modules
from src.data_processing import load_and_clean, get_summary_stats, validate_columns, load_data
from src.forecasting import train_model, generate_forecast_df
from src.waste_risk import calculate_risk, get_risk_summary, get_category_risk_profile
from src.recommendations import generate_recommendations, get_action_summary, get_item_action_summary
from src.redistribution import load_recipients, match_recipients, get_redistribution_summary

# ------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------
st.set_page_config(
    page_title="FoodWise AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Custom CSS — minimal but polished
# ------------------------------------------------------------------
st.markdown("""
<style>
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #1a5276 0%, #117a65 100%);
        padding: 1.8rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p { margin: 0.3rem 0 0 0; opacity: 0.88; font-size: 0.95rem; }

    /* KPI metric cards */
    .kpi-card {
        background: #f7f9fc;
        border: 1px solid #dde3ea;
        border-left: 4px solid #1a5276;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
    }
    .kpi-card .kpi-label { font-size: 0.78rem; color: #6c757d; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-card .kpi-value { font-size: 1.7rem; font-weight: 700; color: #1a5276; line-height: 1.2; }
    .kpi-card .kpi-sub   { font-size: 0.78rem; color: #868e96; }

    /* Risk badge */
    .badge-high   { background:#ffe0e0; color:#c0392b; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:600; }
    .badge-medium { background:#fff3cd; color:#856404; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:600; }
    .badge-low    { background:#d4edda; color:#155724; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:600; }

    /* Section divider */
    .section-title { font-size:1.15rem; font-weight:700; color:#1a5276; border-bottom:2px solid #1a5276; padding-bottom:0.3rem; margin-bottom:1rem; }

    /* Disclaimer box */
    .disclaimer {
        background:#fff8e1; border-left:4px solid #f39c12;
        padding:0.75rem 1rem; border-radius:6px; font-size:0.82rem; color:#7d6608;
    }
    .sdg-box {
        background:#eaf4fb; border-left:4px solid #1a5276;
        padding:0.75rem 1rem; border-radius:6px; font-size:0.85rem; color:#154360;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# Session-state helpers
# ------------------------------------------------------------------
def _init_state():
    defaults = {
        "df": None,
        "df_risk": None,
        "df_rec": None,
        "forecast_result": None,
        "df_forecast": None,
        "recipients": None,
        "matches": None,
        "quality_report": None,
        "data_source": "sample",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ------------------------------------------------------------------
# Cached loaders / trainers
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _cached_load(source_key):
    """Load & clean the bundled sample dataset (cached by key)."""
    df, report = load_and_clean()
    return df, report


@st.cache_data(show_spinner=False)
def _cached_train(_df_hash, df):
    """Train model — cached so re-renders don't retrain."""
    return train_model(df)


@st.cache_data(show_spinner=False)
def _cached_recipients():
    return load_recipients()


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
def render_sidebar():
    st.sidebar.image(
        "https://img.shields.io/badge/SDG%2012-Responsible%20Consumption-green?style=for-the-badge",
        use_container_width=True,
    )
    st.sidebar.markdown("## 🌿 FoodWise AI")
    st.sidebar.caption("IBM SkillsBuild Internship Project")
    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Navigate",
        [
            "🏠 Home & Overview",
            "📂 Data & Quality",
            "📊 Analytics",
            "🤖 Demand Prediction",
            "⚠️ Surplus & Waste Risk",
            "💡 Action Recommendations",
            "🤝 Redistribution Support",
            "🌍 Sustainability Insights",
        ],
    )

    st.sidebar.markdown("---")

    # Data source selector
    st.sidebar.markdown("### Data Source")
    data_choice = st.sidebar.radio(
        "Choose data",
        ["Use sample dataset", "Upload my CSV"],
        key="data_choice",
    )

    if data_choice == "Upload my CSV":
        uploaded = st.sidebar.file_uploader(
            "Upload food data CSV", type=["csv"], key="uploader"
        )
        if uploaded is not None:
            try:
                raw = load_data(uploaded)
                ok, missing = validate_columns(raw)
                if not ok:
                    st.sidebar.error(f"Missing columns: {missing}")
                else:
                    from src.data_processing import clean_data
                    df, report = clean_data(raw)
                    st.session_state["df"] = df
                    st.session_state["quality_report"] = report
                    st.session_state["data_source"] = "upload"
                    st.session_state["df_risk"] = None
                    st.session_state["df_rec"] = None
                    st.session_state["forecast_result"] = None
                    st.session_state["df_forecast"] = None
                    st.sidebar.success(f"Loaded {len(df)} rows.")
            except Exception as e:
                st.sidebar.error(str(e))
    else:
        if st.session_state.get("data_source") != "sample" or st.session_state["df"] is None:
            df, report = _cached_load("sample_v1")
            st.session_state["df"] = df
            st.session_state["quality_report"] = report
            st.session_state["data_source"] = "sample"

    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0  |  For demonstration only")
    return page


# ------------------------------------------------------------------
# Ensure downstream computations are available
# ------------------------------------------------------------------
def ensure_pipeline(df):
    """Run risk + recommendations + forecast if not already done."""
    # Recipients
    if st.session_state["recipients"] is None:
        st.session_state["recipients"] = _cached_recipients()

    # Forecast
    if st.session_state["forecast_result"] is None or st.session_state["df_forecast"] is None:
        with st.spinner("Training demand prediction model…"):
            df_hash = pd.util.hash_pandas_object(df).sum()
            result = _cached_train(df_hash, df)
            st.session_state["forecast_result"] = result
            st.session_state["df_forecast"] = generate_forecast_df(df, result)

    df_f = st.session_state["df_forecast"]

    # Risk
    if st.session_state["df_risk"] is None:
        st.session_state["df_risk"] = calculate_risk(df_f)

    df_r = st.session_state["df_risk"]

    # Recommendations
    if st.session_state["df_rec"] is None:
        st.session_state["df_rec"] = generate_recommendations(df_r)

    df_rec = st.session_state["df_rec"]

    # Redistribution matches
    if st.session_state["matches"] is None:
        st.session_state["matches"] = match_recipients(
            df_rec, st.session_state["recipients"]
        )

    return df_f, df_r, df_rec, st.session_state["matches"]


# ------------------------------------------------------------------
# KPI card helper
# ------------------------------------------------------------------
def kpi(label, value, sub=""):
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ==================================================================
# PAGE RENDERERS
# ==================================================================

# ------------------------------------------------------------------
# 1. Home & Overview
# ------------------------------------------------------------------
def page_home(df):
    st.markdown("""
    <div class="main-header">
        <h1>🌿 FoodWise AI</h1>
        <p>AI-Powered Food Waste Prediction · Surplus Detection · Redistribution Support</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sdg-box">
        <strong>SDG Alignment:</strong>&nbsp;
        <strong>SDG 12 — Responsible Consumption and Production</strong> |
        Target 12.3: Halve per-capita global food waste and reduce food losses.<br>
        <em>Secondary contribution (prototype only):</em> Supporting surplus redistribution
        aligns with SDG 2 (Zero Hunger) as a potential benefit — not a proven outcome.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    stats = get_summary_stats(df)

    cols = st.columns(4)
    with cols[0]:
        kpi("Total Records", f"{stats['total_records']:,}", f"{stats['unique_items']} unique items")
    with cols[1]:
        kpi("Total Prepared", f"{stats['total_prepared']:,} units", "across all items")
    with cols[2]:
        kpi("Total Sold", f"{stats['total_sold']:,} units", "")
    with cols[3]:
        kpi("Est. Surplus", f"{stats['total_remaining']:,} units", f"{stats['overall_waste_pct']}% of prepared")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-title">What This Application Does</div>', unsafe_allow_html=True)
        st.markdown("""
        **FoodWise AI** is a decision-support prototype for food-serving organisations (canteens,
        cloud kitchens, school cafeterias) to:

        - 📈 **Predict demand** for each menu item using machine learning
        - ⚠️ **Detect surplus risk** before it becomes waste
        - 💡 **Recommend actions** — discount, reduce preparation, or redistribute
        - 🤝 **Match surplus** with simulated community recipient organisations

        > **Disclaimer:** This is a student prototype. All recommendations are decision-support
        > aids and must be verified by humans. Food safety is not automatically confirmed.
        """)

    with col2:
        st.markdown('<div class="section-title">Data Overview</div>', unsafe_allow_html=True)
        st.markdown(f"""
        | Field | Value |
        |-------|-------|
        | Date range | {stats['date_range_start']} – {stats['date_range_end']} |
        | Food items | {stats['unique_items']} |
        | Categories | {stats['unique_categories']} |
        | Records | {stats['total_records']:,} |
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">How to Use</div>', unsafe_allow_html=True)
    steps = ["📂 Data & Quality", "📊 Analytics", "🤖 Demand Prediction",
             "⚠️ Surplus & Waste Risk", "💡 Action Recommendations",
             "🤝 Redistribution Support", "🌍 Sustainability Insights"]
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        col.markdown(f"**{i+1}.** {step}")


# ------------------------------------------------------------------
# 2. Data & Quality
# ------------------------------------------------------------------
def page_data(df):
    st.markdown("## 📂 Data & Data Quality")

    report = st.session_state.get("quality_report", {})
    src = st.session_state.get("data_source", "sample")

    st.info(
        f"**Data source:** {'Bundled sample dataset' if src == 'sample' else 'User-uploaded CSV'}  |  "
        f"**Rows after cleaning:** {report.get('final_rows', len(df)):,}  |  "
        f"**Original rows:** {report.get('original_rows', len(df)):,}"
    )

    # Quality report
    st.markdown('<div class="section-title">Data Quality Report</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Original Rows", report.get("original_rows", len(df)))
    col2.metric("Rows Removed", report.get("rows_removed_total", 0))
    col3.metric("Duplicate Rows", report.get("duplicate_rows_removed", 0))
    col4.metric("Date Errors", report.get("date_parse_failures", 0))

    col5, col6 = st.columns(2)
    col5.metric("Negative Values Fixed", report.get("negative_values_fixed", 0))
    col6.metric("Final Clean Rows", report.get("final_rows", len(df)))

    st.markdown("<br>", unsafe_allow_html=True)

    # Data preview
    st.markdown('<div class="section-title">Data Preview</div>', unsafe_allow_html=True)
    display_cols = ["Date", "Food_Item", "Category", "Prepared_Quantity",
                    "Sold_Quantity", "Remaining_Quantity", "Expiry_Hours",
                    "Food_Safety_Status", "Price"]
    show_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[show_cols].head(100), use_container_width=True, height=350)

    # Descriptive stats
    st.markdown('<div class="section-title">Descriptive Statistics</div>', unsafe_allow_html=True)
    numeric_df = df[["Prepared_Quantity", "Sold_Quantity", "Remaining_Quantity"]].describe().round(2)
    st.dataframe(numeric_df, use_container_width=True)

    # Missing-value summary
    st.markdown('<div class="section-title">Missing Values</div>', unsafe_allow_html=True)
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        st.success("No missing values in the cleaned dataset.")
    else:
        st.dataframe(missing.rename("Missing Count").to_frame(), use_container_width=True)


# ------------------------------------------------------------------
# 3. Analytics
# ------------------------------------------------------------------
def page_analytics(df):
    st.markdown("## 📊 Exploratory Data Analysis")

    # --- Date range filter ---
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    col1, col2 = st.columns(2)
    start_d = col1.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    end_d = col2.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

    mask = (df["Date"].dt.date >= start_d) & (df["Date"].dt.date <= end_d)
    dff = df[mask].copy()

    if dff.empty:
        st.warning("No data in selected date range.")
        return

    # --- 1. Daily totals trend ---
    st.markdown('<div class="section-title">Daily Prepared vs Sold vs Surplus</div>', unsafe_allow_html=True)
    daily = dff.groupby("Date")[["Prepared_Quantity", "Sold_Quantity", "Remaining_Quantity"]].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Prepared_Quantity"],
                             name="Prepared", line=dict(color="#1a5276", width=2)))
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Sold_Quantity"],
                             name="Sold", line=dict(color="#117a65", width=2)))
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Remaining_Quantity"],
                             name="Surplus (Remaining)", fill="tozeroy",
                             line=dict(color="#e74c3c", width=1.5), fillcolor="rgba(231,76,60,0.12)"))
    fig.update_layout(height=360, margin=dict(t=20, b=20), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    # --- 2. Category breakdown ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Prepared by Category</div>', unsafe_allow_html=True)
        cat_total = dff.groupby("Category")["Prepared_Quantity"].sum().reset_index()
        fig2 = px.pie(cat_total, names="Category", values="Prepared_Quantity",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Surplus by Category</div>', unsafe_allow_html=True)
        cat_surplus = dff.groupby("Category")["Remaining_Quantity"].sum().reset_index().sort_values("Remaining_Quantity", ascending=True)
        fig3 = px.bar(cat_surplus, x="Remaining_Quantity", y="Category",
                      orientation="h", color="Remaining_Quantity",
                      color_continuous_scale="Reds")
        fig3.update_layout(height=320, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    # --- 3. Day-of-week patterns ---
    st.markdown('<div class="section-title">Average Demand by Day of Week</div>', unsafe_allow_html=True)
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_df = dff.groupby("DayName")[["Sold_Quantity", "Remaining_Quantity"]].mean().reset_index()
    dow_df["DayName"] = pd.Categorical(dow_df["DayName"], categories=dow_order, ordered=True)
    dow_df = dow_df.sort_values("DayName")
    fig4 = px.bar(dow_df, x="DayName", y=["Sold_Quantity", "Remaining_Quantity"],
                  barmode="group", color_discrete_map={"Sold_Quantity": "#117a65", "Remaining_Quantity": "#e74c3c"},
                  labels={"value": "Avg Units", "DayName": "Day"})
    fig4.update_layout(height=320, margin=dict(t=10, b=10), legend_title="")
    st.plotly_chart(fig4, use_container_width=True)

    # --- 4. Top surplus items ---
    st.markdown('<div class="section-title">Top 10 Items by Total Estimated Surplus</div>', unsafe_allow_html=True)
    item_surplus = dff.groupby("Food_Item")["Remaining_Quantity"].sum().reset_index().nlargest(10, "Remaining_Quantity")
    fig5 = px.bar(item_surplus, x="Food_Item", y="Remaining_Quantity",
                  color="Remaining_Quantity", color_continuous_scale="OrRd",
                  labels={"Remaining_Quantity": "Total Surplus Units", "Food_Item": ""})
    fig5.update_layout(height=340, margin=dict(t=10, b=20), coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

    # --- 5. Monthly trend ---
    st.markdown('<div class="section-title">Monthly Surplus Trend</div>', unsafe_allow_html=True)
    monthly = dff.groupby(["MonthName", "Month"])["Remaining_Quantity"].sum().reset_index().sort_values("Month")
    fig6 = px.line(monthly, x="MonthName", y="Remaining_Quantity",
                   markers=True, color_discrete_sequence=["#e74c3c"])
    fig6.update_layout(height=280, margin=dict(t=10, b=10))
    st.plotly_chart(fig6, use_container_width=True)


# ------------------------------------------------------------------
# 4. Demand Prediction
# ------------------------------------------------------------------
def page_forecast(df, df_f, result):
    st.markdown("## 🤖 Demand Prediction")

    model_type_label = result.get("model_type", "Demand Prediction Model")
    sklearn_ok = result.get("sklearn_available", False)
    model_note = (
        "The model uses a <strong>Random Forest Regressor</strong> (scikit-learn)."
        if sklearn_ok else
        "The model uses an <strong>Item-Adjusted Linear Model</strong> (NumPy fallback — scikit-learn unavailable)."
    )
    st.markdown(f"""
    <div class="disclaimer">
        {model_note} Trained on historical sales data.
        Features: food item, category, day of week, month, weekend indicator.
        Evaluation metrics below reflect held-out test data (time-based split).
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    metrics = result["metrics"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Model Type", result.get("model_type", "Random Forest" if result["enough_data"] else "Baseline (Mean)"))
    col2.metric("MAE", metrics["MAE"], help="Mean Absolute Error — average prediction error in units")
    col3.metric("RMSE", metrics["RMSE"], help="Root Mean Squared Error")
    col4.metric("R²", str(metrics["R2"]), help="Proportion of variance explained (closer to 1.0 is better)")

    if not result["enough_data"]:
        st.info("Dataset is small — using a per-item historical mean as the baseline predictor. "
                "Upload more data for the Random Forest model to activate.")

    # Feature importance
    fi = result.get("feature_importance")
    if fi is not None and not fi.empty:
        st.markdown('<div class="section-title">Feature Importance</div>', unsafe_allow_html=True)
        fi_df = fi.reset_index()
        fi_df.columns = ["Feature", "Importance"]
        feature_labels = {
            "Food_Item_enc": "Food Item",
            "Category_enc": "Category",
            "DayOfWeek": "Day of Week",
            "Month": "Month",
            "IsWeekend": "Is Weekend",
        }
        fi_df["Feature"] = fi_df["Feature"].map(feature_labels).fillna(fi_df["Feature"])
        fig = px.bar(fi_df, x="Importance", y="Feature", orientation="h",
                     color="Importance", color_continuous_scale="Blues")
        fig.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Predicted vs Actual chart
    st.markdown('<div class="section-title">Predicted vs Actual Sold Quantity (Sample)</div>', unsafe_allow_html=True)
    sample = df_f.sample(min(300, len(df_f)), random_state=42).sort_values("Date")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sample["Date"], y=sample["Sold_Quantity"],
                              name="Actual Sold", mode="markers",
                              marker=dict(color="#117a65", size=4, opacity=0.6)))
    fig2.add_trace(go.Scatter(x=sample["Date"], y=sample["Predicted_Demand"],
                              name="Predicted Demand", mode="markers",
                              marker=dict(color="#e67e22", size=4, opacity=0.6)))
    fig2.update_layout(height=360, margin=dict(t=20, b=20), legend=dict(orientation="h"))
    st.plotly_chart(fig2, use_container_width=True)

    # Item-level prediction summary
    st.markdown('<div class="section-title">Per-Item Prediction Summary</div>', unsafe_allow_html=True)
    item_pred = df_f.groupby("Food_Item").agg(
        Category=("Category", "first"),
        Avg_Actual=("Sold_Quantity", "mean"),
        Avg_Predicted=("Predicted_Demand", "mean"),
        Avg_Surplus=("Remaining_Quantity", "mean"),
    ).round(1).reset_index()
    item_pred["Prediction_Gap"] = (item_pred["Avg_Predicted"] - item_pred["Avg_Actual"]).round(1)
    st.dataframe(item_pred.sort_values("Avg_Actual", ascending=False), use_container_width=True, height=380)


# ------------------------------------------------------------------
# 5. Surplus & Waste Risk
# ------------------------------------------------------------------
def page_risk(df_r):
    st.markdown("## ⚠️ Surplus & Waste Risk Analysis")

    st.markdown("""
    <div class="disclaimer">
        Risk levels are determined by waste ratio (remaining ÷ prepared) and expiry window.
        <strong>Low</strong> ≤10% remaining | <strong>Medium</strong> 10–30% |
        <strong>High</strong> ≥30% or ≥20 units remaining.
        Short expiry (≤6 hours) escalates risk one level.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    risk_sum = get_risk_summary(df_r)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 Low Risk Records", f"{risk_sum['low_count']:,}")
    col2.metric("🟡 Medium Risk Records", f"{risk_sum['medium_count']:,}")
    col3.metric("🔴 High Risk Records", f"{risk_sum['high_count']:,}")
    col4.metric("Avg Waste Ratio", f"{risk_sum['avg_waste_ratio_pct']}%")

    # Risk distribution pie
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Risk Distribution</div>', unsafe_allow_html=True)
        risk_counts = pd.DataFrame({
            "Risk": ["Low", "Medium", "High"],
            "Count": [risk_sum["low_count"], risk_sum["medium_count"], risk_sum["high_count"]]
        })
        fig = px.pie(risk_counts, names="Risk", values="Count",
                     color="Risk",
                     color_discrete_map={"Low": "#27ae60", "Medium": "#f39c12", "High": "#e74c3c"})
        fig.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Category Risk Profile</div>', unsafe_allow_html=True)
        cat_risk = get_category_risk_profile(df_r)
        fig2 = px.bar(cat_risk, x="Category", y="Waste_Ratio_Pct",
                      color="Waste_Ratio_Pct", color_continuous_scale="RdYlGn_r",
                      labels={"Waste_Ratio_Pct": "Avg Waste %", "Category": ""})
        fig2.update_layout(height=300, margin=dict(t=10, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # High risk items table
    st.markdown('<div class="section-title">High-Risk Items</div>', unsafe_allow_html=True)
    hi = risk_sum["high_risk_items"]
    if hi.empty:
        st.success("No high-risk items detected.")
    else:
        hi["Avg_Waste_Ratio"] = (hi["Avg_Waste_Ratio"] * 100).round(1).astype(str) + "%"
        st.dataframe(hi, use_container_width=True, height=300)

    # Heatmap: waste ratio by day-of-week and category
    st.markdown('<div class="section-title">Waste Ratio Heatmap (Category × Day of Week)</div>', unsafe_allow_html=True)
    heat_df = df_r.groupby(["Category", "DayName"])["Waste_Ratio"].mean().reset_index()
    heat_pivot = heat_df.pivot(index="Category", columns="DayName", values="Waste_Ratio")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heat_pivot = heat_pivot.reindex(columns=[d for d in day_order if d in heat_pivot.columns])
    fig3 = px.imshow(heat_pivot, color_continuous_scale="RdYlGn_r", aspect="auto",
                     labels={"color": "Waste Ratio"})
    fig3.update_layout(height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)


# ------------------------------------------------------------------
# 6. Action Recommendations
# ------------------------------------------------------------------
def page_recommendations(df_rec):
    st.markdown("## 💡 Action Recommendations")

    st.markdown("""
    <div class="disclaimer">
        Recommendations are generated automatically based on risk level, surplus quantity,
        expiry window, and food safety status. They are <strong>decision-support aids</strong>
        — human verification is required before acting on any suggestion.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    action_sum = get_action_summary(df_rec)
    counts = action_sum["action_counts"]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Monitor", counts.get("Monitor", 0))
    col2.metric("Reduce Preparation", counts.get("Reduce Preparation", 0))
    col3.metric("Controlled Discount", counts.get("Controlled Discount", 0))
    col4.metric("Redistribution Candidate", counts.get("Redistribution Candidate", 0))
    col5.metric("Discard (Unsafe)", counts.get("Discard (Unsafe)", 0))

    # Action distribution bar chart
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Action Distribution</div>', unsafe_allow_html=True)
        act_df = pd.DataFrame(list(counts.items()), columns=["Action", "Count"])
        color_map = {
            "Monitor": "#3498db",
            "Reduce Preparation": "#e67e22",
            "Controlled Discount": "#9b59b6",
            "Redistribution Candidate": "#27ae60",
            "Discard (Unsafe)": "#e74c3c",
        }
        fig = px.bar(act_df.sort_values("Count", ascending=True),
                     x="Count", y="Action", orientation="h",
                     color="Action", color_discrete_map=color_map)
        fig.update_layout(height=300, showlegend=False, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Per-Item Dominant Action</div>', unsafe_allow_html=True)
        item_acts = get_item_action_summary(df_rec)
        top = item_acts.head(15)[["Food_Item", "Category", "Total_Surplus", "Dominant_Action", "High_Risk_Days"]]
        st.dataframe(top, use_container_width=True, height=300)

    # Filterable detailed table
    st.markdown('<div class="section-title">Detailed Recommendations (Filter by Action)</div>', unsafe_allow_html=True)
    action_filter = st.multiselect(
        "Filter by action",
        options=list(counts.keys()),
        default=list(counts.keys()),
    )
    filtered = df_rec[df_rec["Recommended_Action"].isin(action_filter)]
    show_cols = ["Date", "Food_Item", "Category", "Prepared_Quantity",
                 "Sold_Quantity", "Remaining_Quantity", "Waste_Risk",
                 "Recommended_Action", "Action_Rationale"]
    show_cols = [c for c in show_cols if c in filtered.columns]
    st.dataframe(
        filtered[show_cols].sort_values(["Date", "Food_Item"], ascending=[False, True]).head(200),
        use_container_width=True, height=380,
    )


# ------------------------------------------------------------------
# 7. Redistribution Support
# ------------------------------------------------------------------
def page_redistribution(df_rec, matches, recipients):
    st.markdown("## 🤝 Redistribution Support")

    st.markdown("""
    <div class="disclaimer">
        <strong>PROTOTYPE DISCLAIMER:</strong> This is a simulated redistribution matching system
        for demonstration purposes only. The recipient organisations listed are fictional.
        This system does NOT connect to any real NGO, food bank, or donation network.
        Food safety must be independently verified before any actual redistribution.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    red_sum = get_redistribution_summary(matches)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Redistribution Candidates", df_rec[df_rec["Recommended_Action"] == "Redistribution Candidate"].shape[0])
    col2.metric("Matched Pairs Found", red_sum["total_matches"])
    col3.metric("Unique Items Matched", red_sum["unique_items"])
    col4.metric("Est. Eligible Units", f"{red_sum['total_eligible_units']:,}")

    # Simulated recipients table
    st.markdown('<div class="section-title">Simulated Recipient Organisations</div>', unsafe_allow_html=True)
    rdf = recipients[["Organization_Name", "Organization_Type", "City",
                       "Capacity_Per_Day", "Accepted_Categories"]].copy()
    st.dataframe(rdf, use_container_width=True, height=280)

    if matches.empty:
        st.info("No redistribution matches found for the current dataset. "
                "This could mean no records meet the redistribution criteria "
                "(Safe status + High risk + sufficient surplus).")
        return

    # Matches by organisation
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Matches by Organisation</div>', unsafe_allow_html=True)
        org_counts = matches.groupby("Organisation")["Surplus_Units"].sum().reset_index().sort_values("Surplus_Units", ascending=True)
        fig = px.bar(org_counts, x="Surplus_Units", y="Organisation", orientation="h",
                     color="Surplus_Units", color_continuous_scale="Greens")
        fig.update_layout(height=320, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Surplus by Food Category (Eligible)</div>', unsafe_allow_html=True)
        cat_match = matches.groupby("Category")["Surplus_Units"].sum().reset_index()
        fig2 = px.pie(cat_match, names="Category", values="Surplus_Units",
                      color_discrete_sequence=px.colors.qualitative.Safe)
        fig2.update_layout(height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # Full match table
    st.markdown('<div class="section-title">Redistribution Match Details</div>', unsafe_allow_html=True)
    st.dataframe(
        matches.sort_values(["Date", "Food_Item"], ascending=[False, True]).head(200),
        use_container_width=True, height=380,
    )


# ------------------------------------------------------------------
# 8. Sustainability Insights
# ------------------------------------------------------------------
def page_sustainability(df, df_rec, result, matches):
    st.markdown("## 🌍 Sustainability Insights Dashboard")

    st.markdown("""
    <div class="sdg-box">
        <strong>SDG 12 — Responsible Consumption and Production</strong><br>
        Target 12.3: By 2030, halve per-capita global food waste at the retail and consumer levels
        and reduce food losses along production and supply chains.<br><br>
        <em>All figures below are <strong>estimates based on historical records</strong> in this
        dataset. They are not verified real-world impact measurements.</em>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    stats = get_summary_stats(df)
    action_sum = get_action_summary(df_rec)
    red_sum = get_redistribution_summary(matches)
    risk_sum = get_risk_summary(df_rec if "Waste_Risk" in df_rec.columns else df)
    metrics = result["metrics"]

    # Top KPIs
    cols = st.columns(4)
    with cols[0]: kpi("Total Records Analysed", f"{stats['total_records']:,}", "food preparation records")
    with cols[1]: kpi("Est. Total Surplus", f"{stats['total_remaining']:,} units", f"{stats['overall_waste_pct']}% of all prepared")
    with cols[2]: kpi("High-Risk Records", f"{risk_sum['high_count']:,}", "records flagged for action")
    with cols[3]: kpi("Redistribution Candidates", f"{action_sum['redistribution_candidates']:,}", "records eligible for sharing")

    st.markdown("<br>", unsafe_allow_html=True)
    cols2 = st.columns(4)
    with cols2[0]: kpi("Model MAE", str(metrics["MAE"]) + " units", "demand prediction error")
    with cols2[1]: kpi("Model R²", str(metrics["R2"]), "variance explained")
    with cols2[2]: kpi("Est. Eligible Units", f"{red_sum['total_eligible_units']:,}", "matched to recipients (simulated)")
    with cols2[3]: kpi("Reduce-Prep Flags", f"{action_sum['reduce_prep_records']:,}", "items to prepare less of")

    st.markdown("<br>", unsafe_allow_html=True)

    # Surplus trend over time
    st.markdown('<div class="section-title">Estimated Surplus Trend Over Time</div>', unsafe_allow_html=True)
    daily = df.groupby("Date")["Remaining_Quantity"].sum().reset_index()
    daily_7 = daily.copy()
    daily_7["7-Day MA"] = daily_7["Remaining_Quantity"].rolling(7, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=daily_7["Date"], y=daily_7["Remaining_Quantity"],
                         name="Daily Surplus", marker_color="rgba(231,76,60,0.4)"))
    fig.add_trace(go.Scatter(x=daily_7["Date"], y=daily_7["7-Day MA"],
                             name="7-Day Moving Avg", line=dict(color="#c0392b", width=2)))
    fig.update_layout(height=340, margin=dict(t=20, b=20), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    # SDG framing
    st.markdown('<div class="section-title">SDG Alignment Summary</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Primary — SDG 12.3 (Responsible Consumption)**
        - This prototype helps food-serving organisations identify and act on surplus
        - Demand prediction reduces over-preparation
        - Risk scoring enables timely intervention
        - Action recommendations guide decision-making

        **Potential Secondary — SDG 2 (Zero Hunger)**
        - Redistribution matching identifies surplus that *may* be shareable
        - Not a proven outcome — food safety must be independently verified
        """)
    with col2:
        st.markdown("""
        **Methodology Transparency**
        - All surplus figures are *estimates* based on Prepared − Sold
        - Risk levels use transparent thresholds (adjustable)
        - ML model uses standard scikit-learn; no black-box claims
        - Redistribution matching is simulated; no real NGO network

        **Limitations**
        - Does not account for portion sizes or actual food weight
        - Food safety cannot be confirmed programmatically
        - Predictions improve with more historical data
        - No real-time IoT or inventory integration
        """)

    st.markdown("""
    <div class="disclaimer" style="margin-top:1rem;">
        <strong>Academic Integrity Notice:</strong> This prototype is a student project for
        IBM SkillsBuild. It does not claim to solve food waste or feed people directly.
        All numbers are derived from a synthetic dataset and are for demonstration only.
    </div>
    """, unsafe_allow_html=True)


# ==================================================================
# MAIN ROUTER
# ==================================================================
def main():
    page = render_sidebar()

    df = st.session_state.get("df")
    if df is None:
        st.error("Data not loaded. Please wait…")
        st.stop()

    # Run the full pipeline once and cache results
    df_f, df_r, df_rec, matches = ensure_pipeline(df)
    result = st.session_state["forecast_result"]
    recipients = st.session_state["recipients"]

    if "🏠" in page:
        page_home(df)
    elif "📂" in page:
        page_data(df)
    elif "📊" in page:
        page_analytics(df)
    elif "🤖" in page:
        page_forecast(df, df_f, result)
    elif "⚠️" in page:
        page_risk(df_r)
    elif "💡" in page:
        page_recommendations(df_rec)
    elif "🤝" in page:
        page_redistribution(df_rec, matches, recipients)
    elif "🌍" in page:
        page_sustainability(df, df_rec, result, matches)


if __name__ == "__main__":
    main()
