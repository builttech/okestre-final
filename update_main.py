import builtins
import re

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(path, 'r', encoding='utf-8').read()

# 1. list_sdd_specs
old_list = '''    requirements_dir = os.path.join(documents_dir, "requirements")
    spec_dir = os.path.join(documents_dir, "spec")'''
new_list = '''    requirements_dir = os.path.join(documents_dir, "requirements")
    functional_dir = os.path.join(documents_dir, "functional-requirements")
    spec_dir = os.path.join(documents_dir, "spec")'''
content = content.replace(old_list, new_list)

old_append = '''        append_markdown_specs(requirements_dir, "project_spec_file", ".documents/requirements")
        append_markdown_specs(spec_dir, "project_spec_file", ".documents/spec")'''
new_append = '''        append_markdown_specs(requirements_dir, "project_spec_file", ".documents/requirements")
        append_markdown_specs(functional_dir, "project_spec_file", ".documents/functional-requirements")
        append_markdown_specs(spec_dir, "project_spec_file", ".documents/spec")'''
content = content.replace(old_append, new_append)

# 2. _sdd_req_pai_template and _sdd_rf_template
old_req_path = 'f"| RF-01-01 | Primeiro fluxo de {title} | functional-requirements/RF-01-01.md | Levantado |\\n\\n"'
new_req_path = 'f"| RF-01-01 | Primeiro fluxo de {title} | .documents/functional-requirements/RF-01-01.md | Levantado |\\n\\n"'
content = content.replace(old_req_path, new_req_path)

# 3. generate_sdd_spec context
old_context = 'folder_context = f"REQ-01-nome/functional-requirements/RF-01-01-nome.md" if is_rf else f"REQ-01-nome/REQ-01.md"'
new_context = 'folder_context = f"RF-01-01-nome.md (em .documents/functional-requirements)" if is_rf else f"REQ-01-nome.md (em .documents/requirements)"'
content = content.replace(old_context, new_context)

# 4. get_sdd_spec
old_get_spec = '''    spec_path_requirements = os.path.join(project.path, ".documents", "requirements", filename)
    spec_path = os.path.join(_sdd_spec_dir(project), filename)
    legacy_spec_path = os.path.join(project.path, ".documents", "specs", filename)'''
new_get_spec = '''    spec_path_requirements = os.path.join(project.path, ".documents", "requirements", filename)
    spec_path_functional = os.path.join(project.path, ".documents", "functional-requirements", filename)
    spec_path = os.path.join(_sdd_spec_dir(project), filename)
    legacy_spec_path = os.path.join(project.path, ".documents", "specs", filename)'''
content = content.replace(old_get_spec, new_get_spec)

old_get_for = 'for p in [spec_path_requirements, spec_path, legacy_spec_path]:'
new_get_for = 'for p in [spec_path_requirements, spec_path_functional, spec_path, legacy_spec_path]:'
content = content.replace(old_get_for, new_get_for)

# 5. delete_sdd_spec
old_del_spec = '''    spec_path = os.path.join(docs_dir, "requirements", filename)
    legacy_spec_path = os.path.join(docs_dir, "specs", filename)
    legacy_spec2_path = os.path.join(docs_dir, "spec", filename)'''
new_del_spec = '''    spec_path = os.path.join(docs_dir, "requirements", filename)
    func_spec_path = os.path.join(docs_dir, "functional-requirements", filename)
    legacy_spec_path = os.path.join(docs_dir, "specs", filename)
    legacy_spec2_path = os.path.join(docs_dir, "spec", filename)'''
content = content.replace(old_del_spec, new_del_spec)

old_del_for = 'for p in [spec_path, legacy_spec_path, legacy_spec2_path]:'
new_del_for = 'for p in [spec_path, func_spec_path, legacy_spec_path, legacy_spec2_path]:'
content = content.replace(old_del_for, new_del_for)

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Updated main.py successfully')
