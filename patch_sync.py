import builtins
import re

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(path, 'r', encoding='utf-8').read()

# 1. Change GPT_INSTRUCTIONS.md to True
content = content.replace('("GPT_INSTRUCTIONS.md", False),', '("GPT_INSTRUCTIONS.md", True),')

# 2. Make template sync overwrite ONLY if the file ends with "template.md"
old_loop = '''        for tpl_name, target_path in template_map.items():
            tpl_path = os.path.join(templates_dir, tpl_name)
            if not os.path.exists(target_path) and os.path.exists(tpl_path):
                shutil.copy2(tpl_path, target_path)'''

new_loop = '''        for tpl_name, target_path in template_map.items():
            tpl_path = os.path.join(templates_dir, tpl_name)
            if os.path.exists(tpl_path):
                # Se for arquivo de template (termina com template.md), sempre sobrescreve para manter a parametrização atualizada.
                # Se for arquivo de trabalho (design.md, task.md), só cria se não existir para não apagar o trabalho da IA.
                if "template.md" in tpl_name:
                    shutil.copy2(tpl_path, target_path)
                elif not os.path.exists(target_path):
                    shutil.copy2(tpl_path, target_path)'''

content = content.replace(old_loop, new_loop)

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Patched main.py successfully!')
