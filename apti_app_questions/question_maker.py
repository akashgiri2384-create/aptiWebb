import pandas as pd
import re

# ================== FILE PATHS ==================
INPUT_TXT_FILE = "ratio/ratio.txt"
OUTPUT_EXCEL_FILE = "ratio/ratio_1.xlsx"
OUTPUT_CSV_FILE = "ratio/ratio_1.csv"

# ================== COLUMNS ==================
columns = [
    "question",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",
    "explanation"
]

rows = []
skipped_lines = []

# ================== HELPER FUNCTION ==================
def detect_correct_option_from_explanation(options, explanation):
    """
    Tries to detect correct answer from explanation.
    Returns option letter (A/B/C/D) or None.
    """
    numbers = options.values()
    for key, value in options.items():
        if str(value) in explanation:
            return key
    return None

# ================== READ TXT FILE ==================
with open(INPUT_TXT_FILE, "r", encoding="utf-8") as file:
    for line_no, line in enumerate(file, start=1):
        line = line.strip()
        if not line:
            continue

        parts = [p.strip() for p in line.split("|")]

        if len(parts) != 7:
            skipped_lines.append((line_no, line))
            continue

        question, a, b, c, d, correct, explanation = parts

        options = {
            "A": a,
            "B": b,
            "C": c,
            "D": d
        }

        # ================== AUTO-FIX CORRECT ANSWER ==================
        detected = detect_correct_option_from_explanation(options, explanation)

        if detected and detected != correct:
            correct = detected  # auto-fix

        rows.append([
            question,
            a,
            b,
            c,
            d,
            correct,
            explanation
        ])

# ================== CREATE DATAFRAME ==================
df = pd.DataFrame(rows, columns=columns)

# ================== SAVE FILES ==================
df.to_excel(OUTPUT_EXCEL_FILE, index=False)
df.to_csv(OUTPUT_CSV_FILE, index=False, encoding="utf-8-sig")



# ================== SUMMARY ==================
print("✅ Conversion completed successfully!")
print(f"📘 Excel file saved as: {OUTPUT_EXCEL_FILE}")
print(f"📄 CSV file saved as: {OUTPUT_CSV_FILE}")
print(f"📊 Total questions processed: {len(df)}")

if skipped_lines:
    print(f"⚠️ Skipped {len(skipped_lines)} malformed lines:")
    for ln, txt in skipped_lines:
        print(f"  Line {ln}: {txt}")
