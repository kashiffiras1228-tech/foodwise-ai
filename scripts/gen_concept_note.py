r"""
scripts/gen_concept_note.py
Generates FoodWise_AI_Concept_Note.pdf using ReportLab.
Run: .venv\Scripts\python.exe scripts/gen_concept_note.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "FoodWise_AI_Concept_Note.pdf"

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#1a5e3a")
GREEN_MED   = colors.HexColor("#2d8653")
GREEN_LIGHT = colors.HexColor("#e8f5ee")
TEAL        = colors.HexColor("#117a65")
ORANGE      = colors.HexColor("#e07b24")
GREY_TEXT   = colors.HexColor("#444444")
GREY_LIGHT  = colors.HexColor("#f7f7f7")
WHITE       = colors.white
BLACK       = colors.HexColor("#1a1a1a")
BLUE_DARK   = colors.HexColor("#1a4070")

# ── Styles ────────────────────────────────────────────────────────────────────
def ps(name, size=10, leading=14, color=BLACK, font="Helvetica",
       align=TA_JUSTIFY, before=0, after=4):
    return ParagraphStyle(name, fontSize=size, leading=leading,
                          textColor=color, fontName=font,
                          alignment=align, spaceBefore=before, spaceAfter=after)

TITLE_S   = ps("title_s",  size=22, leading=26, color=WHITE,       font="Helvetica-Bold", align=TA_CENTER)
SUBTITLE_S= ps("sub_s",    size=11, leading=14, color=colors.HexColor("#c8f5df"), align=TA_CENTER, after=2)
META_S    = ps("meta_s",   size=9,  leading=12, color=colors.HexColor("#a3e4c0"), align=TA_CENTER, after=0)
H1_S      = ps("h1",       size=13, leading=16, color=GREEN_DARK,  font="Helvetica-Bold", align=TA_LEFT, before=8, after=3)
H2_S      = ps("h2",       size=10.5,leading=13,color=GREEN_MED,   font="Helvetica-Bold", align=TA_LEFT, before=5, after=2)
BODY_S    = ps("body",     size=9.5, leading=13.5, color=GREY_TEXT)
BULLET_S  = ps("bullet",   size=9.5, leading=13, color=GREY_TEXT,  after=2)
SMALL_S   = ps("small",    size=8.5, leading=12, color=GREY_TEXT)
NOTE_S    = ps("note",     size=8.5, leading=11.5, color=ORANGE,   font="Helvetica-Oblique")
CAPTION_S = ps("caption",  size=8,   leading=11, color=colors.HexColor("#777777"), font="Helvetica-Oblique", align=TA_CENTER)
BOX_H_S   = ps("box_h",    size=9.5, leading=12, color=WHITE,      font="Helvetica-Bold", align=TA_LEFT, after=0)
BOX_B_S   = ps("box_b",    size=9,   leading=12, color=GREY_TEXT)

def H1(text): return Paragraph(text, H1_S)
def H2(text): return Paragraph(text, H2_S)
def P(text):  return Paragraph(text, BODY_S)
def Bul(text):return Paragraph(f"\u2022\u00a0\u00a0{text}", BULLET_S)
def Sm(text): return Paragraph(text, SMALL_S)
def Note(text): return Paragraph(f"\u26a0\ufe0f\u00a0{text}", NOTE_S)
def HR(): return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4)
def SPACE(n=4): return Spacer(1, n*mm)

def section_rule():
    return HRFlowable(width="100%", thickness=1.5, color=GREEN_MED, spaceAfter=2, spaceBefore=2)

def info_box(heading, body_text, bg=GREEN_LIGHT, border=GREEN_MED):
    data = [[Paragraph(heading, BOX_H_S)],
            [Paragraph(body_text, BOX_B_S)]]
    t = Table(data, colWidths=[165*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), border),
        ("BACKGROUND", (0,1),(0,1), bg),
        ("BOX",        (0,0),(-1,-1), 0.5, border),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    return t

def metric_table(rows):
    """rows = list of (label, value, note)"""
    data = [[Paragraph(r[0], ps("mh", size=8.5, leading=11, color=WHITE, font="Helvetica-Bold")),
             Paragraph(r[1], ps("mv", size=11, leading=13, color=WHITE, font="Helvetica-Bold", align=TA_CENTER)),
             Paragraph(r[2], ps("mn", size=8, leading=10, color=colors.HexColor("#d0f0e0")))]
            for r in rows]
    t = Table(data, colWidths=[55*mm, 35*mm, 75*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), GREEN_MED),
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [GREEN_MED, colors.HexColor("#245c3d")]),
        ("BOX",        (0,0),(-1,-1), 0.5, GREEN_DARK),
        ("INNERGRID",  (0,0),(-1,-1), 0.3, colors.HexColor("#3d9966")),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",       (1,0),(1,-1), "CENTER"),
    ]))
    return t

def feature_table(features):
    data = [[Paragraph(f[0], ps("fh", size=8.5, leading=11, color=WHITE, font="Helvetica-Bold")),
             Paragraph(f[1], ps("fb", size=8.5, leading=11.5, color=GREY_TEXT))]
            for f in features]
    t = Table(data, colWidths=[52*mm, 113*mm])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [colors.HexColor("#245c3d"), GREEN_MED]),
        ("BACKGROUND", (0,0),(0,-1), GREEN_MED),
        ("BOX",        (0,0),(-1,-1), 0.5, GREEN_DARK),
        ("INNERGRID",  (0,0),(-1,-1), 0.3, colors.HexColor("#aaaaaa")),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
        ("RIGHTPADDING",(0,0),(-1,-1), 8),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
        ("BACKGROUND", (1,0),(1,-1), WHITE),
        ("ROWBACKGROUNDS", (1,0),(1,-1), [WHITE, GREY_LIGHT]),
    ]))
    return t

# ── Document ──────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=12*mm, bottomMargin=15*mm,
)

story = []

# ── Cover banner ──────────────────────────────────────────────────────────────
banner_data = [[
    Paragraph("FoodWise AI", TITLE_S),
    Paragraph("AI-Powered Food Waste Prediction,<br/>Surplus Detection &amp; Redistribution Support Platform", SUBTITLE_S),
    Paragraph("Concept Note  \u2022  IBM SkillsBuild Internship  \u2022  SDG 12 \u2014 Responsible Consumption &amp; Production", META_S),
]]
banner = Table([[banner_data[0][0]], [banner_data[0][1]], [banner_data[0][2]]],
               colWidths=[170*mm])
banner.setStyle(TableStyle([
    ("BACKGROUND", (0,0),(-1,-1), GREEN_DARK),
    ("ALIGN",      (0,0),(-1,-1), "CENTER"),
    ("VALIGN",     (0,0),(-1,-1), "MIDDLE"),
    ("LEFTPADDING",(0,0),(-1,-1), 10),
    ("RIGHTPADDING",(0,0),(-1,-1),10),
    ("TOPPADDING", (0,0),(0,0), 12),
    ("TOPPADDING", (0,1),(-1,1), 4),
    ("TOPPADDING", (0,2),(-1,2), 4),
    ("BOTTOMPADDING",(0,2),(-1,2), 12),
    ("BOTTOMPADDING",(0,0),(0,1), 2),
]))
story.append(banner)
story.append(SPACE(4))

# ── 1. Executive Summary ──────────────────────────────────────────────────────
story.append(KeepTogether([
    H1("1. Executive Summary"),
    section_rule(),
    P("FoodWise AI is an AI-powered <b>decision-support prototype</b> designed to help food-serving "
      "organisations — including canteens, restaurants, hotel food-service departments, and "
      "institutional kitchens — predict food demand, detect potential surplus risk early, and "
      "recommend appropriate actions before food becomes waste."),
    SPACE(2),
    P("The application is built using Python, Streamlit, scikit-learn, and Plotly. It demonstrates "
      "a complete data-driven pipeline: from CSV-based data input and automated cleaning, through "
      "machine-learning demand forecasting, transparent risk scoring, five-category action recommendations, "
      "and simulated redistribution matching. A sustainability insights dashboard presents all key metrics "
      "in the context of <b>SDG 12 — Responsible Consumption and Production, Target 12.3</b>."),
    SPACE(2),
    P("The prototype passed a 100-check functional QA audit with <b>98 PASS, 0 FAIL</b>. The Random "
      "Forest demand prediction model achieved R\u00b2 = 0.797, MAE = 5.80 units, and RMSE = 7.49 units "
      "on the project's synthetic/demo dataset. These are <i>prototype evaluation results on synthetic data</i> "
      "and do not represent production performance."),
]))

# ── 2. Problem Statement ──────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("2. Problem Statement"),
    section_rule(),
    P("Food waste is a major global sustainability challenge. Approximately one-third of all food "
      "produced for human consumption is lost or wasted each year (UN FAO). Food-serving organisations "
      "frequently over-prepare meals due to demand uncertainty, generating avoidable surplus that "
      "often ends up discarded."),
    SPACE(2),
    P("The key contributing factors include:"),
    Bul("Demand uncertainty \u2014 staff rely on manual estimation or intuition, with no systematic prediction tool"),
    Bul("Late surplus detection \u2014 remaining food is identified only after service, when options are limited"),
    Bul("No structured decision framework \u2014 staff lack a data-driven workflow for surplus decisions (discount, redistribute, reduce preparation)"),
    Bul("Missed redistribution opportunities \u2014 surplus that could be shared is discarded due to time constraints or lack of matching infrastructure"),
]))

# ── 3. Background / Context ───────────────────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("3. Background and Context"),
    section_rule(),
    P("The United Nations Sustainable Development Goal 12 \u2014 Responsible Consumption and Production \u2014 "
      "calls for sustainable management and efficient use of natural resources. Its Target 12.3 specifically "
      "calls for halving per-capita global food waste at the retail and consumer levels and reducing food "
      "losses along production and supply chains by 2030."),
    SPACE(2),
    P("At the operational level, food-serving organisations generate daily records of what was prepared and "
      "sold. This data, if analysed systematically, can support earlier identification of surplus risk and "
      "better decisions about preparation quantities and surplus handling. AI and machine learning techniques "
      "offer a practical way to extract actionable insights from this historical data."),
]))

# ── 4. SDG Alignment ─────────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(H1("4. SDG Alignment"))
story.append(section_rule())

sdg_data = [
    [Paragraph("PRIMARY", ps("sh", size=9, leading=11, color=WHITE, font="Helvetica-Bold")),
     Paragraph("SDG 12 \u2014 Responsible Consumption and Production", ps("sv", size=9, leading=12, color=WHITE, font="Helvetica-Bold")),
     Paragraph("Target 12.3: Reduce food waste and food losses", ps("sn", size=8.5, leading=11, color=colors.HexColor("#c8f5df")))],
    [Paragraph("POTENTIAL SECONDARY", ps("sh2", size=8.5, leading=11, color=WHITE, font="Helvetica-Bold")),
     Paragraph("SDG 2 \u2014 Zero Hunger", ps("sv2", size=9, leading=12, color=WHITE, font="Helvetica-Bold")),
     Paragraph("Redistribution support may help eligible surplus reach community organisations", ps("sn2", size=8.5, leading=11, color=colors.HexColor("#fde8cc")))],
]
sdg_table = Table(sdg_data, colWidths=[38*mm, 72*mm, 60*mm])
sdg_table.setStyle(TableStyle([
    ("BACKGROUND",  (0,0),(-1,0), GREEN_DARK),
    ("BACKGROUND",  (0,1),(-1,1), ORANGE),
    ("BOX",         (0,0),(-1,-1), 0.5, GREEN_DARK),
    ("INNERGRID",   (0,0),(-1,-1), 0.3, colors.HexColor("#aaaaaa")),
    ("LEFTPADDING", (0,0),(-1,-1), 8),
    ("RIGHTPADDING",(0,0),(-1,-1), 8),
    ("TOPPADDING",  (0,0),(-1,-1), 6),
    ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
]))
story.append(sdg_table)
story.append(SPACE(2))
story.append(Note("SDG 2 is described only as a potential secondary contribution. FoodWise AI does not claim to solve hunger, "
                  "and no actual redistribution is performed by the prototype. Food safety must be independently verified."))

# ── 5. Target Users ───────────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("5. Target Users"),
    section_rule(),
    P("FoodWise AI is designed for food-serving organisations that prepare food daily and generate preparation records:"),
    Bul("University and college cafeterias"),
    Bul("Restaurants and fast-food outlets"),
    Bul("Hotel food and beverage departments"),
    Bul("Institutional and corporate canteens"),
    Bul("Supermarkets managing perishable inventory"),
    Bul("Catering companies and event kitchens"),
    SPACE(2),
    P("<b>Early adopters</b> are organisations with high daily food volumes, measurable surplus patterns, "
      "and staff responsible for both preparation planning and surplus disposal decisions."),
]))

# ── 6. Proposed Solution ──────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(H1("6. Proposed Solution"))
story.append(section_rule())
story.append(P("FoodWise AI addresses the identified problem through an integrated data-driven pipeline:"))
story.append(SPACE(2))

workflow_data = [
    ["Step", "Component", "Description"],
    ["1", "Data Input", "Load bundled sample CSV or upload real food-preparation records"],
    ["2", "Cleaning & Validation", "Detect and fix date errors, negatives, impossible quantities; report quality metrics"],
    ["3", "Analytics", "Interactive charts: demand trends, category breakdown, day-of-week patterns, top-surplus items"],
    ["4", "Demand Prediction", "Random Forest Regressor predicts Sold_Quantity per item; outputs Predicted_Demand and Predicted_Surplus"],
    ["5", "Waste Risk Scoring", "Transparent Low/Medium/High risk using Waste_Ratio and Expiry_Hours; escalation for short expiry"],
    ["6", "Action Recommendations", "Five-label engine: Monitor, Reduce Preparation, Controlled Discount, Redistribution Candidate, Discard (Unsafe)"],
    ["7", "Redistribution Support", "Matches redistribution-candidate records to simulated recipient organisations by category and capacity"],
    ["8", "Sustainability Insights", "SDG-aligned KPI dashboard: estimated surplus, risk counts, redistribution candidates, model metrics"],
]
wf_table = Table(workflow_data, colWidths=[10*mm, 42*mm, 118*mm])
wf_table.setStyle(TableStyle([
    ("BACKGROUND",  (0,0),(-1,0), GREEN_DARK),
    ("TEXTCOLOR",   (0,0),(-1,0), WHITE),
    ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",    (0,0),(-1,0), 8.5),
    ("FONTSIZE",    (0,1),(-1,-1), 8.5),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, GREY_LIGHT]),
    ("BOX",         (0,0),(-1,-1), 0.5, GREEN_DARK),
    ("INNERGRID",   (0,0),(-1,-1), 0.3, colors.HexColor("#aaaaaa")),
    ("LEFTPADDING", (0,0),(-1,-1), 6),
    ("RIGHTPADDING",(0,0),(-1,-1), 6),
    ("TOPPADDING",  (0,0),(-1,-1), 4),
    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ("VALIGN",      (0,0),(-1,-1), "TOP"),
    ("ALIGN",       (0,0),(0,-1), "CENTER"),
    ("TEXTCOLOR",   (0,1),(0,-1), GREEN_MED),
    ("FONTNAME",    (0,1),(0,-1), "Helvetica-Bold"),
    ("TEXTCOLOR",   (1,1),(1,-1), GREEN_DARK),
    ("FONTNAME",    (1,1),(1,-1), "Helvetica-Bold"),
]))
story.append(wf_table)

# ── 7. AI / Machine Learning Approach ────────────────────────────────────────
story.append(SPACE(3))
story.append(H1("7. AI / Machine Learning Approach"))
story.append(section_rule())
story.append(P("The demand prediction module uses a <b>Random Forest Regressor</b> "
               "(scikit-learn RandomForestRegressor: 100 trees, max depth 10, random state 42). "
               "The model predicts <i>Sold_Quantity</i> for a given food item on a given date."))
story.append(SPACE(2))
story.append(H2("Input Features"))
story.append(Bul("Food_Item (label-encoded) \u2014 which item is being prepared"))
story.append(Bul("Category (label-encoded) \u2014 food category (Grains, Protein, Vegetables, etc.)"))
story.append(Bul("DayOfWeek \u2014 0 = Monday, 6 = Sunday"))
story.append(Bul("Month \u2014 1\u201312"))
story.append(Bul("IsWeekend \u2014 1 if Saturday or Sunday, else 0"))
story.append(SPACE(2))
story.append(H2("Evaluation Approach"))
story.append(P("A <b>time-based 80/20 train/test split</b> is used: earlier dates form the training set, "
               "later dates form the test set. This avoids data leakage from future observations into the model."))
story.append(SPACE(2))
story.append(H2("Prototype Evaluation Results"))
story.append(metric_table([
    ("Mean Absolute Error (MAE)", "5.80 units", "Average absolute difference between predicted and actual sold quantity"),
    ("Root Mean Squared Error (RMSE)", "7.49 units", "Penalises larger errors more heavily than MAE"),
    ("R\u00b2 (Coefficient of Determination)", "0.797", "~80% of variance in sold quantity explained by the five features"),
]))
story.append(SPACE(2))
story.append(Note("These results were obtained entirely on the project's synthetic/demo dataset "
                  "and must not be interpreted as production forecasting performance or real-world accuracy. "
                  "Performance on real operational data will differ."))

# ── 8. Core Features ─────────────────────────────────────────────────────────
story.append(SPACE(3))
story.append(H1("8. Core Features"))
story.append(section_rule())
story.append(feature_table([
    ("Data Input & Validation",    "Loads bundled sample dataset (6,576 synthetic records) or user-uploaded CSV. "
                                    "Validates required columns; reports missing columns clearly."),
    ("Data Cleaning",              "Handles unparseable dates, non-numeric quantities, negatives (clamped to 0), "
                                    "Sold > Prepared (capped), and Remaining always recalculated as Prepared \u2212 Sold."),
    ("Analytics Dashboard",        "Interactive Plotly charts: daily trends, category breakdown, day-of-week patterns, "
                                    "top-surplus items, monthly surplus trend. Date-range filter included."),
    ("Demand Prediction",          "Random Forest Regressor trained on food item, category, and date features. "
                                    "Outputs Predicted_Demand and Predicted_Surplus per record."),
    ("Surplus & Waste Risk",       "Transparent Low/Medium/High risk scoring using Waste_Ratio = Remaining \u00f7 Prepared "
                                    "and Expiry_Hours. Risk is independent of Food_Safety_Status."),
    ("Action Recommendations",     "Five-label engine per record: Monitor, Reduce Preparation, Controlled Discount, "
                                    "Redistribution Candidate (Safe+High only), or Discard (Unsafe only)."),
    ("Redistribution Support",     "Matches redistribution-candidate records to simulated recipient organisations "
                                    "(10 fictional orgs) by food category and daily capacity. Prototype only."),
    ("Sustainability Insights",    "SDG 12.3-aligned KPI dashboard with estimated surplus totals, risk distribution, "
                                    "redistribution candidates, model metrics, and surplus trend chart."),
]))

# ── 9. Expected Benefits ──────────────────────────────────────────────────────
story.append(SPACE(3))
story.append(KeepTogether([
    H1("9. Expected Benefits"),
    section_rule(),
    P("As a decision-support tool, FoodWise AI is <i>designed to support</i> the following outcomes "
      "in a real operational deployment:"),
    Bul("Earlier identification of potential surplus, enabling timely action"),
    Bul("Data-driven preparation planning to reduce over-preparation over time"),
    Bul("Structured decision support for staff managing surplus (discount, prepare less, redistribute)"),
    Bul("A transparent audit trail of surplus events and recommended actions"),
    Bul("A foundation for sustainable food management practices aligned with SDG 12.3"),
    SPACE(2),
    Note("These are designed capabilities of the prototype. The application does not claim to have "
         "already reduced real-world food waste, performed redistribution, or produced verified environmental impact."),
]))

# ── 10. Innovation / Value Proposition ───────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("10. Innovation and Value Proposition"),
    section_rule(),
    P("FoodWise AI's core innovation is the integration of four capabilities into one lightweight platform:"),
    Bul("ML demand forecasting \u2014 moves beyond manual estimation"),
    Bul("Transparent risk scoring \u2014 every decision is explainable using visible thresholds"),
    Bul("Structured action recommendations \u2014 staff receive a specific suggested action, not just a number"),
    Bul("Redistribution matching \u2014 connects eligible surplus with simulated community recipients"),
    SPACE(2),
    P("The application is built on an entirely open-source Python stack, requires no cloud infrastructure "
      "for local deployment, and is designed to be explainable to non-technical decision-makers."),
]))

# ── 11. Technology Stack ──────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("11. Technology Stack"),
    section_rule(),
]))
tech_data = [
    ["Component", "Technology", "Version"],
    ["Web interface", "Streamlit", "1.65.0"],
    ["Data manipulation", "Pandas", "3.0.6"],
    ["Numerical computing", "NumPy", "2.5.3"],
    ["Machine learning", "scikit-learn", "1.9.1"],
    ["Visualisation", "Plotly", "7.1.0"],
    ["Model persistence", "Joblib", "1.6.0"],
    ["Python runtime", "CPython", "3.12.14"],
    ["Environment manager", "uv", "\u2014"],
]
tech_table = Table(tech_data, colWidths=[55*mm, 65*mm, 50*mm])
tech_table.setStyle(TableStyle([
    ("BACKGROUND",  (0,0),(-1,0), GREEN_DARK),
    ("TEXTCOLOR",   (0,0),(-1,0), WHITE),
    ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",    (0,0),(-1,-1), 9),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, GREY_LIGHT]),
    ("BOX",         (0,0),(-1,-1), 0.5, GREEN_DARK),
    ("INNERGRID",   (0,0),(-1,-1), 0.3, colors.HexColor("#aaaaaa")),
    ("LEFTPADDING", (0,0),(-1,-1), 8),
    ("RIGHTPADDING",(0,0),(-1,-1), 8),
    ("TOPPADDING",  (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
]))
story.append(tech_table)

# ── 12. Data Handling ─────────────────────────────────────────────────────────
story.append(SPACE(3))
story.append(KeepTogether([
    H1("12. Data Handling"),
    section_rule(),
    H2("Sample Dataset"),
    P("The application includes a <b>synthetic</b> sample dataset ("
      "<i>data/sample_food_data.csv</i>) generated specifically for this prototype. "
      "It contains <b>6,576 records</b> covering 24 food items across 6 categories "
      "(Grains &amp; Bread, Vegetables, Protein, Snacks, Desserts, Beverages) "
      "for the period 1 January 2024 \u2013 30 September 2024."),
    SPACE(2),
    P("Dataset fields: Date, Food_Item, Category, Prepared_Quantity, Sold_Quantity, "
      "Remaining_Quantity, Expiry_Hours, Food_Safety_Status, Price (\u20b9). "
      "All values are synthetic and do not represent any real organisation or operation."),
    SPACE(2),
    H2("Redistribution Recipient Data"),
    P("Ten fictional recipient organisations are included in <i>data/sample_recipients.csv</i>. "
      "Organisations cover types including NGO / Food Bank, Shelter / Welfare Home, Orphanage, "
      "and Community Centre, across six Indian cities. All organisations, contact details, and "
      "capacity figures are entirely simulated."),
    SPACE(2),
    Note("Redistribution matching is a prototype demonstration. FoodWise AI does not connect to "
         "any real NGO, food bank, or community network, and does not perform actual redistribution."),
]))

# ── 13. Prototype QA Results ──────────────────────────────────────────────────
story.append(SPACE(3))
story.append(H1("13. Prototype Results and QA Status"))
story.append(section_rule())

qa_data = [
    ["QA Check", "Result"],
    ["Total automated checks", "100"],
    ["PASS", "98"],
    ["FAIL", "0"],
    ["Informational warnings", "2 (non-blocking, design-confirmed)"],
    ["Streamlit health check", "HTTP 200 \u2014 application running"],
    ["MVP status", "Ready for demonstration"],
]
qa_table = Table(qa_data, colWidths=[100*mm, 70*mm])
qa_table.setStyle(TableStyle([
    ("BACKGROUND",  (0,0),(-1,0), GREEN_DARK),
    ("TEXTCOLOR",   (0,0),(-1,0), WHITE),
    ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",    (0,0),(-1,-1), 9),
    ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, GREY_LIGHT]),
    ("BACKGROUND",  (0,3),(1,3), GREEN_LIGHT),
    ("FONTNAME",    (0,3),(1,3), "Helvetica-Bold"),
    ("TEXTCOLOR",   (0,3),(1,3), GREEN_DARK),
    ("BOX",         (0,0),(-1,-1), 0.5, GREEN_DARK),
    ("INNERGRID",   (0,0),(-1,-1), 0.3, colors.HexColor("#aaaaaa")),
    ("LEFTPADDING", (0,0),(-1,-1), 8),
    ("RIGHTPADDING",(0,0),(-1,-1), 8),
    ("TOPPADDING",  (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
]))
story.append(qa_table)

# ── 14. Limitations ───────────────────────────────────────────────────────────
story.append(SPACE(3))
story.append(KeepTogether([
    H1("14. Limitations"),
    section_rule(),
    Bul("All results are based on a <b>synthetic/demo dataset</b> and cannot be used to make real-world claims"),
    Bul("No real-time integration with restaurant POS, inventory management, or IoT sensors"),
    Bul("No integration with real NGO, food-bank, or redistribution networks"),
    Bul("Food safety is <b>not</b> autonomously certified \u2014 the Food_Safety_Status field is a rule-based demo label"),
    Bul("ML model trained on synthetic data \u2014 real-world performance requires real operational data"),
    Bul("Does not account for food weight, portion sizes, or caloric content"),
    Bul("Redistribution matching is simulated \u2014 capacity figures and categories are fictional"),
    Bul("Recommendation engine is a decision-support tool; all suggestions require human review"),
    Bul("No multi-location, multi-organisation, or user authentication support in current prototype"),
]))

# ── 15. Future Scope ──────────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("15. Future Scope"),
    section_rule(),
    Bul("Integration with operational POS, inventory, or ERP systems for real data"),
    Bul("Improved forecasting: LSTM / time-series models with weather and event features"),
    Bul("Real-time inventory monitoring via IoT sensors or API polling"),
    Bul("Verified partnerships with real NGOs and food banks"),
    Bul("Geospatial distance-based recipient matching"),
    Bul("Responsible IBM watsonx / LLM explanation layer for recommendations"),
    Bul("Automated PDF/Excel reporting for management review"),
    Bul("Role-based dashboards for canteen staff vs. managers"),
    Bul("Multi-location and multi-organisation support"),
]))

# ── 16. Conclusion ────────────────────────────────────────────────────────────
story.append(SPACE(2))
story.append(KeepTogether([
    H1("16. Conclusion"),
    section_rule(),
    P("FoodWise AI demonstrates that a lightweight, open-source Python application can provide "
      "meaningful decision support for food waste reduction at the operational level. By combining "
      "machine-learning demand forecasting, transparent risk scoring, structured action recommendations, "
      "and redistribution matching in a single platform, it offers food-serving organisations a practical "
      "starting point for data-driven surplus management."),
    SPACE(2),
    P("The prototype is aligned with <b>SDG 12 \u2014 Responsible Consumption and Production, "
      "Target 12.3</b>, and its redistribution support feature represents a potential contribution "
      "to SDG 2 in a real-world deployment. It is presented as a <i>decision-support prototype</i> "
      "with clearly documented capabilities, limitations, and honest evaluation results."),
    SPACE(2),
    P("The application passed its full functional QA audit (98/100 checks), is running successfully, "
      "and is ready for demonstration."),
]))

# ── Footer ────────────────────────────────────────────────────────────────────
story.append(SPACE(3))
story.append(HRFlowable(width="100%", thickness=1, color=GREEN_MED))
story.append(Paragraph(
    "FoodWise AI \u2014 IBM SkillsBuild Internship Project  |  "
    "Decision-support prototype only. All metrics are prototype results on synthetic/demo data.  |  "
    "No verified real-world impact claimed.",
    ps("footer", size=7.5, leading=10, color=colors.HexColor("#888888"), align=TA_CENTER, after=0)
))

doc.build(story)
print(f"Generated: {OUTPUT}")
