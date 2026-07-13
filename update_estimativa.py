import builtins
import os

main_py = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
app_js = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'

# Replace in main.py
content = builtins.open(main_py, 'r', encoding='utf-8').read()
content = content.replace('pricing.md', 'estimativa.md')

# Add creation of estimativa.md in sync_project_system_files
template_hook = '''        template_map = {
            "REQ-01-template.md": req_md,
            "RF-01-01-template.md": rf_md,
            "task.md": task_md,
            "task.details.md": task_details_md,
            "design.md": design_md,
            "dri.md": dri_md,
            "project-charter.md": project_charter_md
        }'''

new_hook = '''        estimativa_path = os.path.join(project_path, ".documents", "estimativa.md")
        if not os.path.exists(estimativa_path):
            with builtins.open(estimativa_path, "w", encoding="utf-8") as f:
                f.write("# Estimativa Global\\n\\nClique em 'Gerar Estimativa' no painel Harness para analisar o projeto.")

        template_map = {
            "REQ-01-template.md": req_md,
            "RF-01-01-template.md": rf_md,
            "task.md": task_md,
            "task.details.md": task_details_md,
            "design.md": design_md,
            "dri.md": dri_md,
            "project-charter.md": project_charter_md
        }'''

if 'estimativa_path =' not in content:
    content = content.replace(template_hook, new_hook)

builtins.open(main_py, 'w', encoding='utf-8').write(content)


# Replace in app.js
app_content = builtins.open(app_js, 'r', encoding='utf-8').read()
app_content = app_content.replace('pricing.md', 'estimativa.md')
builtins.open(app_js, 'w', encoding='utf-8').write(app_content)

print("Replacement and file initialization done.")
