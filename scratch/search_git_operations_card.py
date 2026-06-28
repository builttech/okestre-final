with open("gitide_server/static/rebrand.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "git-operations-card" in line:
        print(f"Line {idx+1}: {line.strip()[:100]}")
