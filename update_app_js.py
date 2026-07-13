import builtins
import re

app_js = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(app_js, 'r', encoding='utf-8').read()

# Update regex
old_regex = r'/\\bTASK-(?:REQ-\\d{2,6}|QA-[A-Z0-9-]+)-\\d{3}\\b/i'
new_regex = r'/\\bTASK-(?:RF-\\d{2,6}-\\d{2}-\\d{3}|QA-[A-Z0-9-]+-\\d{3})\\b/i'
content = content.replace(old_regex, new_regex)

old_regex_title = r'/\\bTASK-(?:REQ-\\d{2,6}|QA-[A-Z0-9-]+)-\\d{3}\\b:?\\s*/i'
new_regex_title = r'/\\bTASK-(?:RF-\\d{2,6}-\\d{2}-\\d{3}|QA-[A-Z0-9-]+-\\d{3})\\b:?\\s*/i'
content = content.replace(old_regex_title, new_regex_title)

# Update empty message 1
old_empty_msg_1 = r'TASK-REQ-0000-001: - Título curto'
new_empty_msg_1 = r'TASK-RF-0000-00-001: Título curto'
content = content.replace(old_empty_msg_1, new_empty_msg_1)

# Update empty message 2 (Task detail missing text)
old_empty_msg_2 = r'<code>## Plano — </code>'
new_empty_msg_2 = r'<code>#  — Título da Task</code>'
content = content.replace(old_empty_msg_2, new_empty_msg_2)

# Update sddActiveSpec fallback to .documents/requirements
old_active_spec_fallback = r'.documents/spec/'
new_active_spec_fallback = r'.documents/requirements/'
content = content.replace(old_active_spec_fallback, new_active_spec_fallback)

# Update "- Specify: todos os REQs em .documents/spec/*.md" to .documents/requirements
old_specify = r'- Specify: todos os REQs em .documents/spec/*.md'
new_specify = r'- Specify: todos os REQs em .documents/requirements/*.md'
content = content.replace(old_specify, new_specify)

builtins.open(app_js, 'w', encoding='utf-8').write(content)
print("app.js updated")
