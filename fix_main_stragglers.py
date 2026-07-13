import builtins
main_py = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(main_py, 'r', encoding='utf-8').read()

content = content.replace("TASK-REQ-0000-001", "TASK-RF-0001-01-001")
content = content.replace("TASK-REQ-0000-000", "TASK-RF-0001-01-000")
content = content.replace("## Plano — TASK", "# TASK")

old_task_list = "- Task List deve ficar em .documents/task/task.md e conter somente itens no formato - [ ] TASK-REQ-0000-001: - Título curto ou - [ ] TASK-QA-XXXXXXXX-001: - Título curto."
new_task_list = "- Task List deve ficar em .documents/task/task.md e conter somente itens no formato - [ ] TASK-RF-0000-00-001: Título curto ou - [ ] TASK-QA-XXXXXXXX-001: Título curto."
content = content.replace(old_task_list, new_task_list)

builtins.open(main_py, 'w', encoding='utf-8').write(content)
print("done")
