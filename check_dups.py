
import re

file_path = r'd:\aptiWeb\templates\auth\register.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize whitespace in content to handle multi-line options
content = ' '.join(content.split())

# Find all option values
options = re.findall(r'<option\s+value=["\'](.*?)["\']>', content)

seen = set()
duplicates = []
for opt in options:
    if not opt: continue # Skip empty values
    if opt in seen:
        duplicates.append(opt)
    seen.add(opt)

if duplicates:
    print(f"Found {len(duplicates)} duplicates:")
    for d in duplicates:
        print(f"- {d}")
else:
    print("No duplicates found.")
