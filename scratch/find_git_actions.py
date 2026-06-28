with open("gitide_server/static/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "git-commit-msg" in line or "btn-git-deploy" in line or "Commitar e Fazer" in line or "git-deploy-panel" in line:
        print(f"Line {idx+1}: {line.strip()[:120]}")
