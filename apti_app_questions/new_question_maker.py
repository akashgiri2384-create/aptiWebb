import pandas as pd
import os

# ================== FILE PATHS ==================
INPUT_TXT_FILE = "question.txt"
OUTPUT_DIR = "profit_loss"
START_FILE_INDEX = 1   # ratio_2.xlsx

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

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================== HELPER FUNCTION ==================
def detect_correct_option_from_explanation(options, explanation):
    for key, value in options.items():
        if str(value) in explanation:
            return key
    return None

# ================== READ FILE ==================
with open(INPUT_TXT_FILE, "r", encoding="utf-8") as file:
    lines = file.readlines()

blocks = []
current_block = []
blank_count = 0

for line in lines:
    line = line.rstrip()

    if not line:
        blank_count += 1
        if blank_count == 2:
            if current_block:
                blocks.append(current_block)
                current_block = []
        continue
    else:
        blank_count = 0
        current_block.append(line)

# add last block
if current_block:
    blocks.append(current_block)

# ================== PROCESS BLOCKS ==================
file_index = START_FILE_INDEX

for block in blocks:
    rows = []
    skipped = []

    for line_no, line in enumerate(block, start=1):

        # skip header
        if line.lower().startswith("question |"):
            continue

        parts = [p.strip() for p in line.split("|")]

        if len(parts) != 7:
            skipped.append((line_no, line))
            continue

        question, a, b, c, d, correct, explanation = parts

        options = {"A": a, "B": b, "C": c, "D": d}
        detected = detect_correct_option_from_explanation(options, explanation)

        if detected and detected != correct:
            correct = detected

        rows.append([question, a, b, c, d, correct, explanation])

    if not rows:
        continue

    df = pd.DataFrame(rows, columns=columns)

    excel_path = f"{OUTPUT_DIR}/{OUTPUT_DIR}_{file_index}.xlsx"
    csv_path = f"{OUTPUT_DIR}/{OUTPUT_DIR}_{file_index}.csv"

    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"✅ Created: {OUTPUT_DIR}_{file_index} ({len(df)} questions)")
    file_index += 1

# ================== SUMMARY ==================
print("\n🎯 DONE")
print(f"📂 Total files created: {file_index - START_FILE_INDEX}")
