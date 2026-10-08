r"""
Cross-consistency checker for all three deliverables.
Run: .venv\Scripts\python.exe scripts/check_consistency.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from pptx import Presentation
from pypdf import PdfReader

def extract_pdf_text(path):
    reader = PdfReader(str(path))
    return " ".join(
        page.extract_text() or "" for page in reader.pages
    )

# Extract text from all three documents
lc_text  = extract_pdf_text("FoodWise_AI_Lean_Canvas.pdf")
cn_text  = extract_pdf_text("FoodWise_AI_Concept_Note.pdf")

prs = Presentation("FoodWise_AI_Presentation.pptx")
pptx_text = " ".join(
    p.text for slide in prs.slides
    for shape in slide.shapes if shape.has_text_frame
    for p in shape.text_frame.paragraphs
)

docs    = ["Lean Canvas", "Concept Note", "PPTX"]
sources = [lc_text, cn_text, pptx_text]

checks_positive = [
    ("FoodWise AI title",             "FoodWise AI"),
    ("SDG 12 reference",              "SDG 12"),
    ("Target 12.3",                   "12.3"),
    ("Potential secondary SDG 2",     "potential"),
    ("Random Forest model",           "Random Forest"),
    ("MAE = 5.80",                    "5.80"),
    ("RMSE = 7.49",                   "7.49"),
    ("R2 = 0.797",                    "0.797"),
    ("Synthetic/demo data labelling", "synthetic"),
    ("QA 98 pass count",              "98"),
    ("Simulated recipients",          "simulated"),
    ("Decision-support framing",      "decision"),
    ("IBM SkillsBuild",               "SkillsBuild"),
    ("IBM SkillsBuild in LC",         "IBM"),
]

checks_negative = [
    ("No CO2 claims",                  "CO2"),
    ("No meals-served claims",         "meals served"),
    ("No eliminates food waste claim", "eliminates food waste"),
    ("No reduces food waste by X%",    "reduces food waste by"),
    ("No actual redistribution claim", "actually redistributes"),
    ("No fake user/impact numbers",    "100,000 meals"),
]

print("=" * 65)
print("  CROSS-CONSISTENCY CHECK  —  All Three Deliverables")
print("=" * 65)

all_ok = True

print("\nPositive checks (term must be present in ALL three documents):")
for label, term in checks_positive:
    results = [term.lower() in t.lower() for t in sources]
    status = "OK  " if all(results) else "FAIL"
    if not all(results):
        all_ok = False
    missing = [docs[i] for i, r in enumerate(results) if not r]
    note = f"  -- missing in: {missing}" if missing else ""
    print(f"  [{status}] {label}{note}")

print("\nNegative checks (term must NOT appear in any document):")
for label, term in checks_negative:
    present = [term.lower() in t.lower() for t in sources]
    if any(present):
        found_in = [docs[i] for i, p in enumerate(present) if p]
        print(f"  [WARN] {label}: found in {found_in}")
        all_ok = False
    else:
        print(f"  [OK  ] {label}: absent (correct)")

print("\nDocument page / slide counts:")
for fname in ["FoodWise_AI_Lean_Canvas.pdf", "FoodWise_AI_Concept_Note.pdf"]:
    r = PdfReader(fname)
    sz = Path(fname).stat().st_size
    print(f"  {fname}: {len(r.pages)} page(s), {sz:,} bytes")
print(f"  FoodWise_AI_Presentation.pptx: {len(prs.slides)} slides, "
      f"{Path('FoodWise_AI_Presentation.pptx').stat().st_size:,} bytes")

print(f"\nLean Canvas extracted chars : {len(lc_text)}")
print(f"Concept Note extracted chars: {len(cn_text)}")
print(f"PPTX text chars             : {len(pptx_text)}")

print("\n" + "=" * 65)
print("  FINAL RESULT:", "ALL CONSISTENT — PASS" if all_ok else "ISSUES FOUND")
print("=" * 65)
sys.exit(0 if all_ok else 1)
