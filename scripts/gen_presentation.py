r"""
scripts/gen_presentation.py
Generates FoodWise_AI_Presentation.pptx using python-pptx.
Run: .venv\Scripts\python.exe scripts/gen_presentation.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import pptx.oxml.ns as nsmap
from lxml import etree
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "FoodWise_AI_Presentation.pptx"

# ── Colour palette ─────────────────────────────────────────────────────────────
C_GREEN_DARK  = RGBColor(0x1a, 0x5e, 0x3a)
C_GREEN_MED   = RGBColor(0x2d, 0x86, 0x53)
C_GREEN_LIGHT = RGBColor(0xd6, 0xed, 0xe1)
C_GREEN_PALE  = RGBColor(0xf0, 0xfa, 0xf4)
C_TEAL        = RGBColor(0x11, 0x7a, 0x65)
C_ORANGE      = RGBColor(0xe0, 0x7b, 0x24)
C_WHITE       = RGBColor(0xff, 0xff, 0xff)
C_BLACK       = RGBColor(0x1a, 0x1a, 0x1a)
C_GREY        = RGBColor(0x44, 0x44, 0x44)
C_GREY_LIGHT  = RGBColor(0xf5, 0xf5, 0xf5)
C_BLUE_DARK   = RGBColor(0x1a, 0x40, 0x70)
C_AMBER       = RGBColor(0xd4, 0x8c, 0x00)

# ── Presentation setup ────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # completely blank

W  = prs.slide_width   # 13.33"
H  = prs.slide_height  # 7.5"

# ── Low-level helpers ─────────────────────────────────────────────────────────
def rgb_hex(r,g,b): return RGBColor(r,g,b)

def add_rect(slide, left, top, width, height, fill_rgb=None, line_rgb=None, line_width_pt=0):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    fill = shape.fill
    if fill_rgb:
        fill.solid()
        fill.fore_color.rgb = fill_rgb
    else:
        fill.background()
    line = shape.line
    if line_rgb:
        line.color.rgb = line_rgb
        line.width = Pt(line_width_pt)
    else:
        line.fill.background()
    shape.shadow.inherit = False
    return shape

def add_text_box(slide, text, left, top, width, height,
                 font_size=18, bold=False, italic=False,
                 color=C_BLACK, align=PP_ALIGN.LEFT,
                 wrap=True, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name
    return txBox

def add_para(tf, text, font_size=14, bold=False, italic=False,
             color=C_BLACK, align=PP_ALIGN.LEFT, space_before=0,
             bullet=False, indent_level=0):
    p = tf.add_paragraph()
    p.alignment = align
    p.space_before = Pt(space_before)
    p.level = indent_level
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return p

def add_content_box(slide, left, top, width, height,
                    header_text, header_bg=C_GREEN_DARK, header_fg=C_WHITE,
                    body_bg=C_WHITE, border=C_GREEN_MED):
    """Add a titled content box."""
    # Header bar
    hdr = add_rect(slide, left, top, width, 0.38, fill_rgb=header_bg)
    add_text_box(slide, header_text, left+0.08, top+0.04, width-0.16, 0.30,
                 font_size=12, bold=True, color=header_fg, align=PP_ALIGN.LEFT)
    # Body background
    add_rect(slide, left, top+0.38, width, height-0.38, fill_rgb=body_bg,
             line_rgb=border, line_width_pt=0.5)
    # Return top of body area
    return top + 0.38

def slide_header(slide, title, subtitle=None, stripe=True):
    """Green header bar at top of content slides."""
    if stripe:
        add_rect(slide, 0, 0, 13.33, 1.0, fill_rgb=C_GREEN_DARK)
        add_rect(slide, 0, 1.0, 13.33, 0.07, fill_rgb=C_GREEN_MED)
    add_text_box(slide, title, 0.3, 0.08, 12.5, 0.65,
                 font_size=28, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
    if subtitle:
        add_text_box(slide, subtitle, 0.3, 0.68, 12.5, 0.30,
                     font_size=13, italic=True, color=C_GREEN_LIGHT, align=PP_ALIGN.LEFT)

def slide_footer(slide, text="FoodWise AI  |  IBM SkillsBuild Internship  |  Decision-support prototype  |  SDG 12 Target 12.3"):
    add_rect(slide, 0, 7.18, 13.33, 0.32, fill_rgb=C_GREEN_DARK)
    add_text_box(slide, text, 0.2, 7.20, 12.9, 0.26,
                 font_size=9, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.CENTER)

def bullet_lines(slide, items, left, top, width, height,
                 font_size=14, color=C_GREY, bullet_char="\u2022"):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if first:
            p = tf.paragraphs[0]; first = False
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(3)
        run = p.add_run()
        run.text = f"{bullet_char}  {item}"
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
        run.font.name = "Calibri"
    return tb

def numbered_steps(slide, steps, left, top, width, step_h,
                   num_color=C_GREEN_MED, text_color=C_GREY,
                   num_size=11, text_size=12):
    """Render numbered step boxes horizontally."""
    n = len(steps)
    box_w = width / n
    arrow_w = 0.18
    for i, (num, title, body) in enumerate(steps):
        bx = left + i * box_w
        # Box
        add_rect(slide, bx+0.04, top, box_w-0.08-arrow_w, step_h,
                 fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
        # Number circle (small rectangle acting as badge)
        add_rect(slide, bx+0.12, top+0.06, 0.32, 0.32, fill_rgb=C_GREEN_MED)
        add_text_box(slide, str(num), bx+0.12, top+0.04, 0.32, 0.34,
                     font_size=num_size, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
        # Title
        add_text_box(slide, title, bx+0.50, top+0.07, box_w-0.62, 0.32,
                     font_size=text_size, bold=True, color=C_GREEN_DARK, align=PP_ALIGN.LEFT)
        # Body text
        add_text_box(slide, body, bx+0.12, top+0.44, box_w-0.24-arrow_w, step_h-0.5,
                     font_size=10, color=C_GREY, align=PP_ALIGN.LEFT, wrap=True)
        # Arrow (except last)
        if i < n-1:
            ax = bx + box_w - arrow_w - 0.04
            add_text_box(slide, "\u25b6", ax+0.01, top + step_h/2 - 0.18, 0.22, 0.36,
                         font_size=16, bold=True, color=C_GREEN_MED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 1 — Title Slide
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)

# Full background
add_rect(sl, 0, 0, 13.33, 7.5, fill_rgb=C_GREEN_DARK)
# Accent stripe
add_rect(sl, 0, 5.0, 13.33, 0.06, fill_rgb=C_GREEN_MED)
# Side accent
add_rect(sl, 0, 0, 0.12, 7.5, fill_rgb=C_GREEN_MED)

add_text_box(sl, "🌿 FoodWise AI", 0.5, 1.0, 12.5, 1.4,
             font_size=52, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text_box(sl, "AI-Powered Food Waste Prediction, Surplus Detection &\nRedistribution Support Platform",
             0.5, 2.5, 12.3, 1.0,
             font_size=22, italic=False, color=RGBColor(0xc8,0xf5,0xdf), align=PP_ALIGN.CENTER)
add_rect(sl, 3.5, 3.7, 6.33, 0.04, fill_rgb=C_GREEN_MED)
add_text_box(sl, "IBM SkillsBuild Internship Project", 0.5, 3.85, 12.3, 0.45,
             font_size=16, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.CENTER)
add_text_box(sl, "SDG 12 \u2014 Responsible Consumption and Production  |  Target 12.3",
             0.5, 4.35, 12.3, 0.45,
             font_size=15, bold=True, color=RGBColor(0x7b,0xd4,0xa8), align=PP_ALIGN.CENTER)
add_text_box(sl, "Decision-support prototype  \u2022  Python  \u2022  Streamlit  \u2022  scikit-learn  \u2022  Plotly",
             0.5, 6.55, 12.3, 0.4,
             font_size=11, italic=True, color=RGBColor(0x70,0xa8,0x85), align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 2 — Problem Statement
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "The Problem", "Why do food-serving organisations need a better tool?")
slide_footer(sl)

# Left: problem areas
problems = [
    ("\U0001f4ca  Demand Uncertainty",
     "Staff rely on manual estimation with no systematic prediction — resulting in chronic over-preparation."),
    ("\u23f0  Late Surplus Detection",
     "Remaining food is identified only after service, when most options (discount, redistribute) are gone."),
    ("\u274c  No Decision Framework",
     "There is no structured, data-driven workflow to decide what to do with identified surplus."),
    ("\U0001f501  Missed Redistribution",
     "Surplus that could benefit community organisations is discarded due to time pressure or lack of matching."),
]

y = 1.2
for icon_title, body in problems:
    add_rect(sl, 0.35, y, 7.8, 1.18, fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
    add_text_box(sl, icon_title, 0.5, y+0.08, 7.5, 0.38,
                 font_size=14, bold=True, color=C_GREEN_DARK)
    add_text_box(sl, body, 0.55, y+0.46, 7.4, 0.65,
                 font_size=12, color=C_GREY, wrap=True)
    y += 1.28

# Right: stat call-out
add_rect(sl, 8.5, 1.4, 4.5, 4.2, fill_rgb=C_GREEN_DARK)
add_text_box(sl, "~1/3", 8.6, 1.7, 4.3, 1.3,
             font_size=60, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text_box(sl, "of all food produced\nfor human consumption\nis lost or wasted\n(UN FAO)",
             8.6, 3.0, 4.3, 1.8,
             font_size=14, color=RGBColor(0xc8,0xf5,0xdf), align=PP_ALIGN.CENTER)
add_rect(sl, 8.7, 4.95, 4.1, 0.04, fill_rgb=C_GREEN_MED)
add_text_box(sl, "SDG 12 Target 12.3 calls for halving\nper-capita food waste by 2030.",
             8.6, 5.05, 4.3, 0.7,
             font_size=11, italic=True, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 3 — SDG Alignment
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "SDG Alignment", "Primary: SDG 12 | Potential Secondary: SDG 2")
slide_footer(sl)

# SDG 12 box
add_rect(sl, 0.4, 1.2, 5.8, 5.6, fill_rgb=C_GREEN_DARK)
add_text_box(sl, "PRIMARY SDG", 0.6, 1.25, 5.4, 0.38,
             font_size=11, bold=True, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.LEFT)
add_text_box(sl, "SDG 12", 0.6, 1.6, 5.4, 0.85,
             font_size=40, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
add_text_box(sl, "Responsible Consumption\nand Production", 0.6, 2.45, 5.4, 0.75,
             font_size=17, bold=True, color=RGBColor(0xc8,0xf5,0xdf), align=PP_ALIGN.LEFT)
add_rect(sl, 0.6, 3.28, 5.4, 0.04, fill_rgb=C_GREEN_MED)
add_text_box(sl, "Target 12.3", 0.6, 3.38, 5.4, 0.45,
             font_size=15, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
add_text_box(sl, "By 2030, halve per-capita global food waste\nat the retail and consumer levels and reduce\nfood losses along production and supply chains.",
             0.6, 3.88, 5.3, 0.85,
             font_size=11.5, italic=True, color=RGBColor(0xc8,0xf5,0xdf), align=PP_ALIGN.LEFT)
add_rect(sl, 0.6, 4.85, 5.4, 0.04, fill_rgb=C_GREEN_MED)
add_text_box(sl, "How FoodWise AI supports this:", 0.6, 4.95, 5.4, 0.35,
             font_size=11, bold=True, color=RGBColor(0xa3,0xe4,0xc0))
for item in ["Demand prediction reduces over-preparation",
             "Risk scoring enables earlier surplus action",
             "Recommendations guide better decisions"]:
    pass
bullet_lines(sl, [
    "Demand prediction supports better preparation planning",
    "Risk scoring enables timely surplus identification",
    "Action recommendations guide decision-making",
], 0.6, 5.35, 5.3, 1.1, font_size=11, color=RGBColor(0xd6,0xed,0xe1), bullet_char="\u2714")

# SDG 2 box
add_rect(sl, 6.7, 1.2, 6.2, 3.4, fill_rgb=C_ORANGE)
add_text_box(sl, "POTENTIAL SECONDARY  (prototype only)", 6.9, 1.25, 5.8, 0.38,
             font_size=10, bold=True, color=RGBColor(0xff,0xee,0xd6), align=PP_ALIGN.LEFT)
add_text_box(sl, "SDG 2", 6.9, 1.6, 5.8, 0.85,
             font_size=40, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
add_text_box(sl, "Zero Hunger", 6.9, 2.45, 5.8, 0.55,
             font_size=20, bold=True, color=RGBColor(0xff,0xee,0xd6), align=PP_ALIGN.LEFT)
add_rect(sl, 6.9, 3.1, 5.8, 0.04, fill_rgb=RGBColor(0xff,0xff,0xff))
add_text_box(sl, "The redistribution support feature identifies surplus food\n"
                 "that may be eligible for sharing with community organisations.\n\n"
                 "This represents a potential secondary contribution \u2014 not a\n"
                 "claim that FoodWise AI solves hunger.",
             6.9, 3.2, 5.8, 1.3,
             font_size=11.5, italic=False, color=RGBColor(0xff,0xf3,0xe0), wrap=True)

# Important note box
add_rect(sl, 6.7, 4.75, 6.2, 1.65, fill_rgb=RGBColor(0xff,0xf8,0xe1),
         line_rgb=C_ORANGE, line_width_pt=1.5)
add_text_box(sl, "\u26a0\ufe0f  Important", 6.9, 4.82, 5.8, 0.35,
             font_size=11, bold=True, color=C_ORANGE)
add_text_box(sl, "FoodWise AI does NOT claim to:\n"
                 "\u2022 Solve hunger    \u2022 Certify food as safe\n"
                 "\u2022 Perform actual redistribution\n"
                 "\u2022 Produce verified environmental impact",
             6.9, 5.18, 5.8, 1.1,
             font_size=11, color=RGBColor(0x7d,0x66,0x08), wrap=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 4 — Proposed Solution
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "Proposed Solution", "An integrated data-driven pipeline for food surplus management")
slide_footer(sl)

add_text_box(sl, "FoodWise AI connects four capabilities in a single lightweight platform:",
             0.4, 1.15, 12.5, 0.4, font_size=14, color=C_GREY)

steps_4 = [
    (1, "Predict Demand",
     "Random Forest model forecasts expected Sold_Quantity per item using date & item features"),
    (2, "Score Surplus Risk",
     "Transparent Low / Medium / High risk using Waste_Ratio and Expiry_Hours"),
    (3, "Recommend Action",
     "Five-label engine: Monitor, Reduce Prep, Discount, Redistribute, Discard"),
    (4, "Support Redistribution",
     "Match eligible surplus to simulated recipient orgs by category & capacity"),
]
numbered_steps(sl, steps_4, left=0.35, top=1.65, width=12.6, step_h=2.0)

add_rect(sl, 0.4, 3.85, 12.53, 0.04, fill_rgb=C_GREEN_MED)
add_text_box(sl, "All four steps run automatically from a single CSV upload. Every recommendation is a decision-support suggestion requiring human verification.",
             0.4, 3.98, 12.5, 0.45,
             font_size=12, italic=True, color=C_GREY, align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 5 — System Workflow
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "System Workflow", "Data Input \u2192 Cleaning \u2192 Analytics \u2192 Prediction \u2192 Risk \u2192 Recommendations \u2192 Redistribution \u2192 Insights")
slide_footer(sl)

workflow = [
    ("Data\nInput",      "CSV upload\nor sample\ndataset"),
    ("Cleaning &\nValidation", "Dates, negatives,\ninconsistencies\nfixed automatically"),
    ("Analytics\nEDA",   "Trends, category\nbreakdown, day-of-\nweek patterns"),
    ("Demand\nPrediction","Random Forest:\nPredicted_Demand\nPredicted_Surplus"),
    ("Waste\nRisk",       "Low / Medium\n/ High per record\n(transparent rules)"),
    ("Action\nRecs",      "5 actions:\nMonitor, Reduce,\nDiscount, etc."),
    ("Redistribution\nSupport","Simulated\nrecipient\nmatching"),
    ("Sustainability\nInsights","SDG dashboard\nKPIs & metrics"),
]

bw = 12.7 / len(workflow)
bh = 4.2
by = 1.3
COLORS = [C_GREEN_DARK, C_GREEN_MED, C_TEAL, C_GREEN_MED,
          C_GREEN_DARK, C_TEAL, C_GREEN_MED, C_GREEN_DARK]

for i, (title, body) in enumerate(workflow):
    bx = 0.3 + i * bw
    # Box
    add_rect(sl, bx+0.02, by, bw-0.08, bh,
             fill_rgb=COLORS[i % len(COLORS)], line_rgb=C_WHITE, line_width_pt=1)
    # Title
    add_text_box(sl, title, bx+0.06, by+0.2, bw-0.14, 0.7,
                 font_size=11, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_rect(sl, bx+0.15, by+0.95, bw-0.34, 0.03, fill_rgb=RGBColor(0xa3,0xe4,0xc0))
    # Body
    add_text_box(sl, body, bx+0.06, by+1.08, bw-0.14, 3.0,
                 font_size=9.5, color=RGBColor(0xd6,0xed,0xe1), align=PP_ALIGN.CENTER)
    # Arrow between boxes
    if i < len(workflow)-1:
        ax = bx + bw - 0.1
        add_text_box(sl, "\u25b6", ax, by + bh/2 - 0.18, 0.18, 0.36,
                     font_size=11, bold=True, color=C_GREEN_LIGHT, align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 6 — Core Features
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "Core Features", "Eight implemented capabilities in the current MVP")
slide_footer(sl)

features = [
    ("\U0001f4c1  Data Input & Validation",
     "Sample dataset (6,576 records) or CSV upload. Required columns validated with clear error messages."),
    ("\U0001f9f9  Data Cleaning",
     "Dates parsed, negatives clamped, Sold \u2264 Prepared enforced, Remaining recalculated, quality report shown."),
    ("\U0001f4ca  Analytics Dashboard",
     "Interactive Plotly charts: daily trends, category breakdown, day-of-week, monthly surplus, top-surplus items."),
    ("\U0001f916  ML Demand Prediction",
     "Random Forest Regressor. Features: item, category, day, month, weekend. Time-based 80/20 split."),
    ("\u26a0\ufe0f  Surplus & Waste Risk",
     "Low/Medium/High risk per record. Uses Waste_Ratio (Remaining\u00f7Prepared) and Expiry_Hours. Food safety is separate."),
    ("\U0001f4a1  Action Recommendations",
     "5-label engine per record: Monitor, Reduce Preparation, Controlled Discount, Redistribution Candidate, Discard (Unsafe)."),
    ("\U0001f91d  Redistribution Support",
     "Matches Safe+High-risk surplus to simulated recipients by food category and daily capacity. Prototype only."),
    ("\U0001f30d  Sustainability Insights",
     "SDG 12.3-aligned dashboard: estimated surplus totals, risk counts, redistribution candidates, model metrics."),
]

cols = 2
rows = 4
fw = 6.1
fh = 1.3
for i, (title, body) in enumerate(features):
    col = i % cols
    row = i // cols
    fx = 0.3 + col * (fw + 0.5)
    fy = 1.22 + row * (fh + 0.12)
    add_rect(sl, fx, fy, fw, fh, fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
    add_rect(sl, fx, fy, fw, 0.36, fill_rgb=C_GREEN_MED)
    add_text_box(sl, title, fx+0.1, fy+0.04, fw-0.2, 0.28,
                 font_size=11, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)
    add_text_box(sl, body, fx+0.1, fy+0.42, fw-0.2, fh-0.5,
                 font_size=10, color=C_GREY, wrap=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 7 — AI / Machine Learning
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "AI / Machine Learning Approach",
             "Random Forest Regressor \u2014 Prototype evaluation on synthetic/demo data")
slide_footer(sl)

# Left column: model details
add_rect(sl, 0.3, 1.2, 5.9, 5.5, fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
add_rect(sl, 0.3, 1.2, 5.9, 0.4, fill_rgb=C_GREEN_MED)
add_text_box(sl, "Model & Features", 0.45, 1.25, 5.6, 0.3,
             font_size=12, bold=True, color=C_WHITE)
add_text_box(sl, "Algorithm", 0.45, 1.7, 5.6, 0.3,
             font_size=11, bold=True, color=C_GREEN_DARK)
add_text_box(sl, "Random Forest Regressor (scikit-learn)\n100 trees  |  max depth 10  |  random state 42",
             0.45, 2.0, 5.6, 0.55, font_size=10.5, color=C_GREY)
add_text_box(sl, "Target Variable", 0.45, 2.62, 5.6, 0.3,
             font_size=11, bold=True, color=C_GREEN_DARK)
add_text_box(sl, "Sold_Quantity (units sold per item per day)",
             0.45, 2.92, 5.6, 0.35, font_size=10.5, color=C_GREY)
add_text_box(sl, "Input Features (5)", 0.45, 3.35, 5.6, 0.3,
             font_size=11, bold=True, color=C_GREEN_DARK)
bullet_lines(sl, [
    "Food_Item (label-encoded)",
    "Category (label-encoded)",
    "DayOfWeek (0=Mon \u2026 6=Sun)",
    "Month (1\u201312)",
    "IsWeekend (1 if Sat/Sun)",
], 0.45, 3.65, 5.5, 1.6, font_size=10.5, color=C_GREY)
add_text_box(sl, "Train/Test Split", 0.45, 5.3, 5.6, 0.3,
             font_size=11, bold=True, color=C_GREEN_DARK)
add_text_box(sl, "Time-based 80/20 split (earlier dates \u2192 train, later dates \u2192 test)\nNo data leakage from future observations.",
             0.45, 5.6, 5.6, 0.7, font_size=10.5, color=C_GREY, wrap=True)

# Right column: metrics
add_rect(sl, 6.6, 1.2, 6.3, 2.5, fill_rgb=C_GREEN_DARK)
add_text_box(sl, "Prototype Evaluation Results", 6.75, 1.28, 6.0, 0.35,
             font_size=12, bold=True, color=RGBColor(0xa3,0xe4,0xc0))
add_text_box(sl, "on synthetic/demo dataset", 6.75, 1.63, 6.0, 0.28,
             font_size=10, italic=True, color=RGBColor(0x70,0xa8,0x85))

for mi, (label, val, desc) in enumerate([
    ("MAE", "5.80 units", "Mean Absolute Error"),
    ("RMSE", "7.49 units", "Root Mean Squared Error"),
    ("R\u00b2", "0.797", "~80% variance explained"),
]):
    mx = 6.7 + mi * 2.1
    add_rect(sl, mx, 2.0, 1.95, 1.3, fill_rgb=C_GREEN_MED)
    add_text_box(sl, label, mx+0.05, 2.05, 1.85, 0.38,
                 font_size=14, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text_box(sl, val, mx+0.05, 2.43, 1.85, 0.5,
                 font_size=18, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text_box(sl, desc, mx+0.05, 2.93, 1.85, 0.32,
                 font_size=8.5, italic=True, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.CENTER)

# Disclaimer
add_rect(sl, 6.6, 3.85, 6.3, 1.4, fill_rgb=RGBColor(0xff,0xf8,0xe1),
         line_rgb=C_ORANGE, line_width_pt=1.5)
add_text_box(sl, "\u26a0\ufe0f  Important Disclaimer", 6.75, 3.92, 6.0, 0.35,
             font_size=11, bold=True, color=C_ORANGE)
add_text_box(sl,
    "These results were obtained entirely on the project's synthetic/demo dataset.\n"
    "They must NOT be interpreted as:\n"
    "\u2022 Production forecasting accuracy\n"
    "\u2022 Real-world performance\n"
    "\u2022 Verified food waste reduction",
    6.75, 4.3, 6.0, 1.2, font_size=10.5, color=RGBColor(0x7d,0x66,0x08), wrap=True)

# Fallback note
add_rect(sl, 6.6, 5.4, 6.3, 1.0, fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.5)
add_text_box(sl, "Fallback: Item-Adjusted Linear Model (NumPy)",
             6.75, 5.45, 6.0, 0.35, font_size=10, bold=True, color=C_GREEN_DARK)
add_text_box(sl, "Activates automatically if scikit-learn is unavailable (e.g. security policy). "
                 "Prototype achieved R\u00b2 = 0.485 with this fallback.",
             6.75, 5.82, 6.0, 0.5, font_size=9.5, italic=True, color=C_GREY, wrap=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 8 — Application Screenshots Placeholder
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "Application \u2014 Dashboard Screens",
             "Running at http://localhost:8501 using Streamlit")
slide_footer(sl)

screens = [
    ("Home & Overview",     "KPI cards: total records,\nprepared, sold, est. surplus"),
    ("Analytics",           "Daily trend, category pie,\nday-of-week demand chart"),
    ("Demand Prediction",   "Feature importance, predicted\nvs actual scatter, per-item table"),
    ("Surplus & Waste Risk","Risk distribution pie,\nheatmap, high-risk items table"),
    ("Action Recommendations","Action distribution bar chart,\nfilterable detail table"),
    ("Redistribution Support","Recipient orgs table,\nmatch results, surplus by org"),
]

sw = 4.1; sh = 2.4
positions = [(0.25,1.2),(4.55,1.2),(8.85,1.2),(0.25,3.8),(4.55,3.8),(8.85,3.8)]
for (sx,sy), (title, desc) in zip(positions, screens):
    add_rect(sl, sx, sy, sw, sh, fill_rgb=C_GREEN_DARK,
             line_rgb=C_GREEN_MED, line_width_pt=0.8)
    add_text_box(sl, title, sx+0.1, sy+0.1, sw-0.2, 0.38,
                 font_size=11, bold=True, color=C_WHITE)
    add_rect(sl, sx+0.1, sy+0.52, sw-0.2, sh-0.7,
             fill_rgb=RGBColor(0x0e,0x4a,0x2d))
    add_text_box(sl, "[ Screenshot ]\nInsert screenshot of the\nrunning application here",
                 sx+0.1, sy+0.62, sw-0.2, sh-0.8,
                 font_size=9, italic=True,
                 color=RGBColor(0x6b,0xb8,0x8a), align=PP_ALIGN.CENTER)
    add_text_box(sl, desc, sx+0.1, sy+sh-0.52, sw-0.2, 0.48,
                 font_size=9, italic=True, color=RGBColor(0xa3,0xe4,0xc0))

add_text_box(sl, "Run: .venv\\Scripts\\python.exe -m streamlit run app.py   |   Opens at: http://localhost:8501",
             0.3, 6.88, 12.7, 0.25, font_size=9.5, italic=True,
             color=RGBColor(0x70,0xa8,0x85), align=PP_ALIGN.CENTER)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 9 — Action Recommendations & Redistribution
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "Action Recommendations & Redistribution Support",
             "Transparent rules \u2014 decision-support only \u2014 human verification required")
slide_footer(sl)

# Actions grid
actions = [
    ("Monitor",              C_TEAL,     "Low surplus, no immediate action required. Continue monitoring."),
    ("Reduce Preparation",   C_AMBER,    "Model shows consistent over-preparation vs predicted demand. Adjust tomorrow's batch."),
    ("Controlled Discount",  RGBColor(0x7b,0x35,0x9e), "Moderate/high surplus with approaching expiry. Offer price reduction to sell."),
    ("Redistribution Candidate", C_GREEN_MED, "High surplus + Food_Safety_Status = Safe + Expiry > 6h. Flag for potential sharing."),
    ("Discard (Unsafe)",     RGBColor(0xc0,0x39,0x2b), "Food_Safety_Status = Unsafe. Do not discount or redistribute."),
]
aw = 2.35; ah = 1.9; ay = 1.25
for i, (label, col, body) in enumerate(actions):
    ax = 0.3 + i * (aw + 0.1)
    add_rect(sl, ax, ay, aw, ah, fill_rgb=col, line_rgb=C_WHITE, line_width_pt=0.5)
    add_text_box(sl, label, ax+0.08, ay+0.1, aw-0.16, 0.4,
                 font_size=11, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_rect(sl, ax+0.1, ay+0.56, aw-0.2, 0.03, fill_rgb=C_WHITE)
    add_text_box(sl, body, ax+0.08, ay+0.68, aw-0.16, ah-0.8,
                 font_size=9.5, color=C_WHITE, align=PP_ALIGN.CENTER, wrap=True)

# Redistribution section
add_rect(sl, 0.3, 3.35, 12.73, 0.4, fill_rgb=C_GREEN_DARK)
add_text_box(sl, "Redistribution Support \u2014 Simulated Prototype Matching System",
             0.45, 3.4, 12.4, 0.3, font_size=12, bold=True, color=C_WHITE)

rr = [
    ("Eligibility Gate",  "Only records with Action = \u201cRedistribution Candidate\u201d\n(Safe + High risk + Expiry > 6h) proceed to matching."),
    ("Category Match",    "Recipient organisation must accept\nthe food\u2019s category."),
    ("Capacity Check",    "Recipient daily capacity must be\n\u2265 surplus units."),
    ("Ranked Results",    "Up to 3 recipients suggested,\nranked by capacity (highest first)."),
]
rw = 12.73/4; rh = 2.5; ry = 3.9
for i, (title, body) in enumerate(rr):
    rx = 0.3 + i * rw
    add_rect(sl, rx+0.04, ry, rw-0.08, rh,
             fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
    add_text_box(sl, title, rx+0.12, ry+0.1, rw-0.24, 0.4,
                 font_size=11, bold=True, color=C_GREEN_DARK)
    add_text_box(sl, body, rx+0.12, ry+0.55, rw-0.24, rh-0.7,
                 font_size=10, color=C_GREY, wrap=True)

add_rect(sl, 0.3, 6.5, 12.73, 0.5, fill_rgb=RGBColor(0xff,0xf8,0xe1),
         line_rgb=C_ORANGE, line_width_pt=1)
add_text_box(sl,
    "\u26a0\ufe0f  All recipient organisations are FICTIONAL. Food safety is NOT certified by this system. "
    "No actual redistribution is performed. Human verification required before any action.",
    0.45, 6.55, 12.4, 0.38, font_size=10.5, bold=True, color=RGBColor(0x7d,0x66,0x08))

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 10 — Prototype Results & QA
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "Prototype Results & QA Status",
             "Functional QA: 98 PASS, 0 FAIL \u2014 Streamlit HTTP 200 \u2014 MVP ready for demonstration")
slide_footer(sl)

# QA badge
add_rect(sl, 0.3, 1.25, 4.1, 4.7, fill_rgb=C_GREEN_DARK)
add_text_box(sl, "QA AUDIT", 0.5, 1.4, 3.7, 0.4,
             font_size=13, bold=True, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.CENTER)
add_text_box(sl, "98", 0.5, 1.85, 3.7, 1.3,
             font_size=72, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text_box(sl, "PASS", 0.5, 3.15, 3.7, 0.55,
             font_size=28, bold=True, color=C_GREEN_LIGHT, align=PP_ALIGN.CENTER)
add_rect(sl, 0.6, 3.78, 3.5, 0.04, fill_rgb=C_GREEN_MED)
add_text_box(sl, "0  FAIL", 0.5, 3.9, 3.7, 0.5,
             font_size=20, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text_box(sl, "2 informational warnings\n(non-blocking, design-confirmed)", 0.5, 4.5, 3.7, 0.55,
             font_size=10, italic=True, color=RGBColor(0xa3,0xe4,0xc0), align=PP_ALIGN.CENTER)
add_text_box(sl, "Streamlit HTTP 200 \u2713", 0.5, 5.15, 3.7, 0.45,
             font_size=13, bold=True, color=RGBColor(0x7b,0xd4,0xa8), align=PP_ALIGN.CENTER)

# Model results
add_rect(sl, 4.8, 1.25, 8.2, 2.15, fill_rgb=C_GREEN_PALE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
add_rect(sl, 4.8, 1.25, 8.2, 0.38, fill_rgb=C_TEAL)
add_text_box(sl, "Model Evaluation Results  (synthetic/demo data)", 4.95, 1.3, 7.9, 0.28,
             font_size=11, bold=True, color=C_WHITE)
for mi, (lbl, val, desc) in enumerate([
    ("MAE", "5.80 units", "Mean Absolute Error"),
    ("RMSE", "7.49 units", "Root Mean Squared Error"),
    ("R\u00b2", "0.797", "~80% variance explained"),
]):
    mx = 4.95 + mi * 2.7
    add_rect(sl, mx, 1.75, 2.45, 1.45, fill_rgb=C_GREEN_MED)
    add_text_box(sl, lbl, mx+0.05, 1.82, 2.35, 0.38,
                 font_size=13, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text_box(sl, val, mx+0.05, 2.2, 2.35, 0.55,
                 font_size=18, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
    add_text_box(sl, desc, mx+0.05, 2.75, 2.35, 0.3,
                 font_size=8.5, italic=True, color=RGBColor(0xd6,0xed,0xe1), align=PP_ALIGN.CENTER)

# Key QA findings
add_rect(sl, 4.8, 3.55, 8.2, 2.35, fill_rgb=C_WHITE, line_rgb=C_GREEN_MED, line_width_pt=0.8)
add_rect(sl, 4.8, 3.55, 8.2, 0.38, fill_rgb=C_GREEN_MED)
add_text_box(sl, "Key QA Findings", 4.95, 3.6, 7.9, 0.28,
             font_size=11, bold=True, color=C_WHITE)
qa_items = [
    "Impossible quantities (Sold>Prepared, negatives) correctly handled",
    "Unsafe food never receives Redistribution Candidate action (0 violations)",
    "Waste risk and food safety confirmed as independent concepts",
    "No data leakage: time-based split, no future-derived features",
    "All KPI metrics derived live from active dataset (no hardcoded values)",
    "Data source switching correctly clears all cached pipeline results",
]
bullet_lines(sl, qa_items, 4.95, 4.0, 7.9, 1.8, font_size=10, color=C_GREY)

# Disclaimer
add_rect(sl, 4.8, 6.02, 8.2, 0.68, fill_rgb=RGBColor(0xff,0xf8,0xe1),
         line_rgb=C_ORANGE, line_width_pt=1)
add_text_box(sl, "\u26a0\ufe0f Metrics are prototype results on synthetic data \u2014 NOT production performance.",
             4.95, 6.1, 7.9, 0.5, font_size=11, bold=True, color=RGBColor(0x7d,0x66,0x08))

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 11 — Limitations & Future Scope
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
slide_header(sl, "Limitations & Future Scope",
             "Honest prototype positioning \u2014 clear path to production")
slide_footer(sl)

add_rect(sl, 0.3, 1.2, 6.1, 5.6, fill_rgb=RGBColor(0xff,0xf8,0xe1),
         line_rgb=C_ORANGE, line_width_pt=1)
add_rect(sl, 0.3, 1.2, 6.1, 0.42, fill_rgb=C_ORANGE)
add_text_box(sl, "\u26a0\ufe0f  Limitations (Current Prototype)", 0.45, 1.25, 5.8, 0.3,
             font_size=12, bold=True, color=C_WHITE)
limits = [
    "Synthetic/demo dataset \u2014 no real-world claims",
    "No real-time POS/inventory integration",
    "No real NGO or food-bank network",
    "Food safety NOT autonomously certified",
    "ML trained on demo data \u2014 not production accuracy",
    "No food weight/caloric content consideration",
    "No multi-location or authentication support",
    "All recommendations require human verification",
]
bullet_lines(sl, limits, 0.45, 1.75, 5.8, 4.9, font_size=11, color=RGBColor(0x7d,0x40,0x00))

add_rect(sl, 6.9, 1.2, 6.1, 5.6, fill_rgb=C_GREEN_PALE,
         line_rgb=C_GREEN_MED, line_width_pt=1)
add_rect(sl, 6.9, 1.2, 6.1, 0.42, fill_rgb=C_GREEN_MED)
add_text_box(sl, "\U0001f680  Future Scope", 7.05, 1.25, 5.8, 0.3,
             font_size=12, bold=True, color=C_WHITE)
futures = [
    "Real operational POS/inventory data integration",
    "LSTM/time-series models with weather/event features",
    "Real-time IoT inventory monitoring",
    "Verified NGO/food-bank API partnerships",
    "Geospatial distance-based recipient matching",
    "Responsible IBM watsonx / LLM explanation layer",
    "PDF/Excel reporting for management",
    "Role-based dashboards (staff vs managers)",
    "Multi-location & multi-organisation support",
]
bullet_lines(sl, futures, 7.05, 1.75, 5.8, 4.9, font_size=11, color=C_GREY)

# ══════════════════════════════════════════════════════════════════════════════
#  SLIDE 12 — Conclusion
# ══════════════════════════════════════════════════════════════════════════════
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, 13.33, 7.5, fill_rgb=C_GREEN_DARK)
add_rect(sl, 0, 0, 0.12, 7.5, fill_rgb=C_GREEN_MED)
add_rect(sl, 0, 6.0, 13.33, 0.06, fill_rgb=C_GREEN_MED)
slide_footer(sl)

add_text_box(sl, "Conclusion", 0.5, 0.3, 12.3, 0.75,
             font_size=32, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_rect(sl, 3.0, 1.1, 7.33, 0.05, fill_rgb=C_GREEN_MED)

conclusions = [
    ("\U0001f4ca  Decision Support", "FoodWise AI provides an integrated, explainable decision-support workflow "
     "for food surplus management \u2014 combining prediction, risk, recommendations and redistribution in one platform."),
    ("\U0001f30d  SDG 12.3 Aligned", "The application directly supports the objective of SDG 12 Target 12.3 \u2014 "
     "reducing food losses through better demand planning and earlier surplus identification."),
    ("\U0001f916  ML-Powered", "A Random Forest Regressor delivers R\u00b2 = 0.797, MAE = 5.80 units on the "
     "prototype dataset. Metrics are clearly labelled as synthetic/demo results."),
    ("\u2705  QA Verified", "98/100 automated checks pass. Streamlit HTTP 200. MVP is running and ready for demonstration."),
    ("\U0001f4a1  Honest Positioning", "No claims of verified impact, actual redistribution, or production accuracy. "
     "A responsible, auditable foundation for future real-world deployment."),
]

cy = 1.3
for icon_title, body in conclusions:
    add_rect(sl, 0.5, cy, 12.3, 0.92, fill_rgb=RGBColor(0x15,0x4a,0x2d))
    add_text_box(sl, icon_title, 0.65, cy+0.07, 3.0, 0.35,
                 font_size=12, bold=True, color=RGBColor(0xa3,0xe4,0xc0))
    add_text_box(sl, body, 3.8, cy+0.1, 8.8, 0.72,
                 font_size=11, color=RGBColor(0xd6,0xed,0xe1), wrap=True)
    cy += 1.02

add_text_box(sl, "IBM SkillsBuild Internship  \u2022  FoodWise AI  \u2022  SDG 12 \u2014 Responsible Consumption and Production",
             0.5, 6.45, 12.3, 0.4,
             font_size=11, italic=True, color=RGBColor(0x70,0xa8,0x85), align=PP_ALIGN.CENTER)

# ── Save ──────────────────────────────────────────────────────────────────────
prs.save(str(OUTPUT))
print(f"Generated: {OUTPUT}  ({prs.slides.__len__()} slides)")
