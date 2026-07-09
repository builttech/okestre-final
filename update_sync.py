import builtins
import re

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(path, 'r', encoding='utf-8').read()

old_sync = '''        req_dir = os.path.join(project_path, ".documents", "requirements")
        req_md = os.path.join(req_dir, "REQ-01-template.md")
        
        func_req_dir = os.path.join(req_dir, "functional-requirements")
        rf_md = os.path.join(func_req_dir, "RF-01-01-template.md")'''

new_sync = '''        req_dir = os.path.join(project_path, ".documents", "requirements")
        req_md = os.path.join(req_dir, "REQ-01-template.md")
        
        func_req_dir = os.path.join(project_path, ".documents", "functional-requirements")
        rf_md = os.path.join(func_req_dir, "RF-01-01-template.md")'''

content = content.replace(old_sync, new_sync)

old_mkdir = '''        os.path.join(".documents", "requirements"),
        os.path.join(".documents", "spec"),'''

new_mkdir = '''        os.path.join(".documents", "requirements"),
        os.path.join(".documents", "functional-requirements"),
        os.path.join(".documents", "spec"),'''

content = content.replace(old_mkdir, new_mkdir)

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Updated sync_project_system_files in main.py')
