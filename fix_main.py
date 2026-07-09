import builtins
import re

path = 'C:/Users/augus/.workspace/act\git-ide/gitide_server/main.py'
content = builtins.open(path, 'r', encoding='utf-8').read()

# Fix save_sdd_spec
old_save_spec = '''    spec_dir = _sdd_spec_dir(project, create=True)
    legacy_specs_dir = os.path.join(_sdd_documents_dir(project), "specs")
    spec_path = os.path.join(spec_dir, filename)'''

new_save_spec = '''    legacy_specs_dir = os.path.join(_sdd_documents_dir(project), "specs")
    
    # Se for um RF, salva em functional-requirements, senão em requirements
    if filename.startswith("RF-") or "functional-requirements" in filename:
        spec_dir = os.path.join(_sdd_documents_dir(project), "functional-requirements")
        # Remove a pasta do nome do arquivo se o frontend enviar para não aninhar
        if "/" in filename:
            filename = filename.split("/")[-1]
    else:
        spec_dir = os.path.join(_sdd_documents_dir(project), "requirements")
        if "/" in filename:
            filename = filename.split("/")[-1]
            
    os.makedirs(spec_dir, exist_ok=True)
    spec_path = os.path.join(spec_dir, filename)'''

content = content.replace(old_save_spec, new_save_spec)

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Fixed save_sdd_spec in main.py')
