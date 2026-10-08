r"""
scripts/gen_lean_canvas.py
Generates FoodWise_AI_Lean_Canvas.pdf using ReportLab.
Run: .venv\Scripts\python.exe scripts/gen_lean_canvas.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "FoodWise_AI_Lean_Canvas.pdf"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#1a5e3a")
GREEN_MED   = colors.HexColor("#2d8653")
GREEN_LIGHT = colors.HexColor("#d6ede1")
GREEN_PALE  = colors.HexColor("#f0faf4")
TEAL        = colors.HexColor("#117a65")
GREY_LIGHT  = colors.HexColor("#f5f5f5")
WHITE       = colors.white
BLACK       = colors.HexColor("#1a1a1a")
ORANGE      = colors.HexColor("#e07b24")
BLUE_LIGHT  = colors.HexColor("#e8f4fb")
BLUE_MED    = colors.HexColor("#1a5276")

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def make_style(name, fontSize=7, leading=9, textColor=BLACK,
               fontName="Helvetica", alignment=TA_LEFT, spaceAfter=1):
    return ParagraphStyle(
        name, fontSize=fontSize, leading=leading, textColor=textColor,
        fontName=fontName, alignment=alignment, spaceAfter=spaceAfter
    )

title_s  = make_style("title_s",  fontSize=9,  leading=11, fontName="Helvetica-Bold",
                       textColor=GREEN_DARK)
body_s   = make_style("body_s",   fontSize=6.5, leading=8.5)
bullet_s = make_style("bullet_s", fontSize=6.5, leading=8.5)
hdr_s    = make_style("hdr_s",    fontSize=7.5, leading=9, fontName="Helvetica-Bold",
                       textColor=WHITE, alignment=TA_CENTER)
sub_s    = make_style("sub_s",    fontSize=5.8, leading=7.5, textColor=colors.HexColor("#555555"))
note_s   = make_style("note_s",   fontSize=5.5, leading=7, textColor=ORANGE, fontName="Helvetica-Oblique")

def hdr(text, bg=GREEN_DARK):
    return Paragraph(text, hdr_s)

def T(text):
    return Paragraph(text, title_s)

def B(items):
    """Build a Paragraph with bullet items."""
    lines = [Paragraph(f"\u2022 {i}", bullet_s) for i in items]
    return lines

def N(text):
    return Paragraph(text, note_s)

def cell(*content):
    """Flatten a list of Paragraphs into a list for a table cell."""
    result = []
    for item in content:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


# ── Content ───────────────────────────────────────────────────────────────────

# ROW 1 — top banner
banner_cell = cell(
    Paragraph("FoodWise AI", make_style("bn", fontSize=16, leading=18,
              fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_CENTER)),
    Paragraph("AI-Powered Food Waste Prediction, Surplus Detection & Redistribution Support Platform",
              make_style("bns", fontSize=8, leading=10, textColor=colors.HexColor("#c8f5df"),
                         alignment=TA_CENTER)),
    Paragraph("IBM SkillsBuild Internship  |  SDG 12 — Responsible Consumption & Production  |  Target 12.3",
              make_style("bni", fontSize=7, leading=9, textColor=colors.HexColor("#a3e4c0"),
                         alignment=TA_CENTER)),
)

# MAIN GRID — following Lean Canvas structure
# Column headers (top labels)
problem_hdr     = hdr("PROBLEM")
solution_hdr    = hdr("SOLUTION", bg=GREEN_MED)
uvp_hdr         = hdr("UNIQUE VALUE PROPOSITION", bg=TEAL)
unfair_hdr      = hdr("UNFAIR ADVANTAGE", bg=GREEN_MED)
segments_hdr    = hdr("CUSTOMER SEGMENTS")

alt_hdr         = hdr("EXISTING ALTERNATIVES", bg=colors.HexColor("#3a6b50"))
metrics_hdr     = hdr("KEY METRICS", bg=colors.HexColor("#1f7a55"))
concept_hdr     = hdr("HIGH-LEVEL CONCEPT", bg=TEAL)
channels_hdr    = hdr("CHANNELS", bg=colors.HexColor("#1f7a55"))
adopters_hdr    = hdr("EARLY ADOPTERS", bg=colors.HexColor("#3a6b50"))

cost_hdr        = hdr("COST STRUCTURE")
revenue_hdr     = hdr("REVENUE STREAMS")

# ── Cell bodies ───────────────────────────────────────────────────────────────

problem_body = cell(
    *B([
        "Food-serving orgs struggle to match preparation with fluctuating demand",
        "Potential surplus often identified too late for effective action",
        "Staff lack a structured, data-driven workflow for surplus decisions",
        "Manual estimation leads to recurring over-preparation",
    ])
)

solution_body = cell(
    *B([
        "ML-based demand prediction (Random Forest Regressor)",
        "Transparent Low/Medium/High surplus-risk scoring",
        "Five-action recommendation engine (Monitor, Reduce Prep, Discount, Redistribute, Discard)",
        "Simulated redistribution recipient matching",
        "Sustainability insights dashboard",
    ])
)

uvp_body = cell(
    Paragraph(
        "<b>Predict food demand, detect surplus early,<br/>and turn potential food waste into<br/>actionable decisions.</b>",
        make_style("uvp", fontSize=7.5, leading=10, textColor=GREEN_DARK,
                   fontName="Helvetica-Bold", alignment=TA_CENTER)
    ),
    Spacer(1, 3),
    Paragraph(
        "A lightweight, explainable AI platform that helps food-serving organisations "
        "act on surplus risk before food is wasted.",
        make_style("uvp2", fontSize=6.5, leading=8.5, alignment=TA_CENTER)
    ),
)

unfair_body = cell(
    *B([
        "Integrated end-to-end workflow: prediction \u2192 risk \u2192 recommendation \u2192 redistribution",
        "Transparent, explainable risk logic — every decision can be explained",
        "Lightweight Python/Streamlit stack — deployable without cloud infrastructure",
        "Built for food-serving orgs, not generic analytics",
    ])
)

segments_body = cell(
    *B([
        "Restaurants & cafeterias",
        "University/college canteens",
        "Hotel food & beverage depts.",
        "Institutional kitchens",
        "Supermarkets (perishables)",
        "Food-service organisations",
    ])
)

alt_body = cell(
    *B([
        "Manual demand estimation",
        "Spreadsheets / basic POS reports",
        "Traditional inventory software",
        "Informal surplus coordination",
        "No systematic surplus workflow",
    ])
)

metrics_body = cell(
    *B([
        "Demand prediction: MAE, RMSE, R\u00b2",
        "Predicted surplus quantity per item",
        "Waste-risk distribution (L/M/H)",
        "Redistribution-eligible surplus units",
        "No. of surplus alerts / recommendations",
    ]),
    N("Prototype results on synthetic/demo data:\nMAE 5.80 | RMSE 7.49 | R\u00b2 0.797\nQA audit: 98 PASS, 0 FAIL (100 checks)")
)

concept_body = cell(
    Paragraph(
        "An AI-powered decision-support platform combining "
        "demand forecasting, surplus-risk analysis, action recommendations "
        "and redistribution support — for food-serving organisations.",
        make_style("con", fontSize=7, leading=9, alignment=TA_CENTER)
    ),
    Spacer(1, 4),
    Paragraph(
        "Like a \u201cweather forecast for food waste\u201d — identifying risk early enough to act.",
        make_style("con2", fontSize=6.5, leading=8, textColor=TEAL,
                   fontName="Helvetica-Oblique", alignment=TA_CENTER)
    ),
)

channels_body = cell(
    *B([
        "Web app (Streamlit, browser-based)",
        "Direct institutional partnerships",
        "Pilot programmes with canteens/hotels",
        "University sustainability programmes",
        "Demonstration workshops",
    ])
)

adopters_body = cell(
    *B([
        "University cafeterias (high daily volume)",
        "Restaurants with significant preparation",
        "Institutional kitchens & catering",
        "Hotels with buffet/catering operations",
        "Orgs with sustainability mandates",
    ])
)

cost_body = cell(
    *B([
        "Software development & maintenance",
        "Cloud hosting & data storage",
        "ML model development & retraining",
        "API integrations (future)",
        "Deployment & customer support",
    ])
)

revenue_body = cell(
    *B([
        "SaaS subscription tiers (future)",
        "Enterprise licences (future)",
        "Institutional analytics plans (future)",
        "Custom deployment & support (future)",
    ]),
    N("Revenue streams represent potential future business models, not current project income.")
)

# ── Build PDF ─────────────────────────────────────────────────────────────────

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=landscape(A4),
    leftMargin=8*mm, rightMargin=8*mm,
    topMargin=6*mm, bottomMargin=6*mm,
)

PW, PH = landscape(A4)
usable_w = PW - 16*mm

# Column widths: 5 equal columns
cw = usable_w / 5

# Row heights
RH_BANNER = 20*mm
RH_TOP    = 38*mm
RH_SUB    = 28*mm
RH_BTM    = 24*mm

# ── Banner row ────────────────────────────────────────────────────────────────
banner_table = Table(
    [[banner_cell]],
    colWidths=[usable_w], rowHeights=[RH_BANNER]
)
banner_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), GREEN_DARK),
    ("ALIGN",      (0,0), (-1,-1), "CENTER"),
    ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0),(-1,-1), 6),
    ("RIGHTPADDING",(0,0),(-1,-1), 6),
    ("TOPPADDING",  (0,0),(-1,-1), 4),
    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ("BOX",        (0,0), (-1,-1), 0.5, WHITE),
]))

# ── Main grid top row: Problem | Solution | UVP | Unfair Adv | Segments ───────
# UVP spans rows 1 and 2; Segments spans rows 1 and 2 on right
# Build as single table with SPAN commands
main_data = [
    # Header row
    [problem_hdr, solution_hdr, uvp_hdr, unfair_hdr, segments_hdr],
    # Body row
    [problem_body, solution_body, uvp_body, unfair_body, segments_body],
    # Sub-header row
    [alt_hdr, metrics_hdr, concept_hdr, channels_hdr, adopters_hdr],
    # Sub-body row
    [alt_body, metrics_body, concept_body, channels_body, adopters_body],
    # Cost + Revenue header row (2+3 col split)
    [cost_hdr,  "", revenue_hdr, "", ""],
    # Cost + Revenue body row
    [cost_body, "", revenue_body, "", ""],
]

COL_WIDTHS = [cw]*5
ROW_HEIGHTS = [
    7*mm,   # top headers
    RH_TOP, # top bodies
    7*mm,   # sub headers
    RH_SUB, # sub bodies
    7*mm,   # bottom headers
    RH_BTM, # bottom bodies
]

main_table = Table(main_data, colWidths=COL_WIDTHS, rowHeights=ROW_HEIGHTS)

sty = [
    # --- borders ---
    ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#aaaaaa")),
    ("BOX",         (0,0), (-1,-1), 0.8, GREEN_DARK),
    # --- header backgrounds ---
    ("BACKGROUND",  (0,0), (0,0), GREEN_DARK),   # Problem hdr
    ("BACKGROUND",  (1,0), (1,0), GREEN_MED),    # Solution hdr
    ("BACKGROUND",  (2,0), (2,0), TEAL),         # UVP hdr
    ("BACKGROUND",  (3,0), (3,0), GREEN_MED),    # Unfair hdr
    ("BACKGROUND",  (4,0), (4,0), GREEN_DARK),   # Segments hdr
    ("BACKGROUND",  (0,2), (0,2), colors.HexColor("#3a6b50")),
    ("BACKGROUND",  (1,2), (1,2), colors.HexColor("#1f7a55")),
    ("BACKGROUND",  (2,2), (2,2), TEAL),
    ("BACKGROUND",  (3,2), (3,2), colors.HexColor("#1f7a55")),
    ("BACKGROUND",  (4,2), (4,2), colors.HexColor("#3a6b50")),
    ("BACKGROUND",  (0,4), (1,4), GREEN_DARK),   # Cost hdr spans 2
    ("BACKGROUND",  (2,4), (4,4), ORANGE),       # Revenue hdr spans 3
    # --- body backgrounds ---
    ("BACKGROUND",  (0,1), (0,1), GREEN_PALE),
    ("BACKGROUND",  (1,1), (1,1), WHITE),
    ("BACKGROUND",  (2,1), (2,1), BLUE_LIGHT),
    ("BACKGROUND",  (3,1), (3,1), WHITE),
    ("BACKGROUND",  (4,1), (4,1), GREEN_PALE),
    ("BACKGROUND",  (0,3), (0,3), GREY_LIGHT),
    ("BACKGROUND",  (1,3), (1,3), WHITE),
    ("BACKGROUND",  (2,3), (2,3), BLUE_LIGHT),
    ("BACKGROUND",  (3,3), (3,3), WHITE),
    ("BACKGROUND",  (4,3), (4,3), GREY_LIGHT),
    ("BACKGROUND",  (0,5), (1,5), GREEN_PALE),
    ("BACKGROUND",  (2,5), (4,5), colors.HexColor("#fff5ec")),
    # --- spans ---
    ("SPAN", (0,4), (1,4)),   # Cost header spans cols 0-1
    ("SPAN", (0,5), (1,5)),   # Cost body spans cols 0-1
    ("SPAN", (2,4), (4,4)),   # Revenue header spans cols 2-4
    ("SPAN", (2,5), (4,5)),   # Revenue body spans cols 2-4
    # --- alignment ---
    ("VALIGN",      (0,0), (-1,-1), "TOP"),
    ("VALIGN",      (0,0), (-1,0), "MIDDLE"),
    ("VALIGN",      (0,2), (-1,2), "MIDDLE"),
    ("VALIGN",      (0,4), (-1,4), "MIDDLE"),
    ("ALIGN",       (0,0), (-1,0), "CENTER"),
    ("ALIGN",       (0,2), (-1,2), "CENTER"),
    ("ALIGN",       (0,4), (-1,4), "CENTER"),
    # --- padding ---
    ("LEFTPADDING",  (0,0), (-1,-1), 4),
    ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ("TOPPADDING",   (0,0), (-1,-1), 3),
    ("BOTTOMPADDING",(0,0), (-1,-1), 3),
    ("TOPPADDING",   (0,1), (-1,1), 5),
    ("TOPPADDING",   (0,3), (-1,3), 5),
    ("TOPPADDING",   (0,5), (-1,5), 5),
]
main_table.setStyle(TableStyle(sty))

# Footer
footer = Paragraph(
    "Decision-support prototype only. All metrics are prototype results on synthetic/demo data. "
    "Redistribution data is simulated. Food safety is not autonomously certified by this system.",
    make_style("foot", fontSize=5.5, leading=7, textColor=colors.HexColor("#666666"),
               alignment=TA_CENTER)
)

story = [banner_table, Spacer(1, 2*mm), main_table, Spacer(1, 2*mm), footer]
doc.build(story)
print(f"Generated: {OUTPUT}")
