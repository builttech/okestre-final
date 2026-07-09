import builtins
import re

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(path, 'r', encoding='utf-8').read()

old_logic = '''    if (kind === 'rf') {
        const pId = parentId || 'REQ-XX';
        const pSlug = pId.toLowerCase(); // simplified
        folderPath = ${pSlug}/functional-requirements/;
        baseFilename = ${id.toLowerCase()}_;
    } else {
        const reqSlug = ${id.toLowerCase()}_;
        folderPath = ${reqSlug}/;
        baseFilename = reqSlug;
    }'''

new_logic = '''    if (kind === 'rf') {
        // Nova estrutura achatada: RF-ID-TITLE.md em functional-requirements
        folderPath = unctional-requirements/;
        baseFilename = ${id.toUpperCase()}-;
    } else {
        // Nova estrutura achatada: REQ-ID-TITLE.md em requirements
        folderPath = equirements/;
        baseFilename = ${id.toUpperCase()}-;
    }'''

content = content.replace(old_logic, new_logic)

# In deleteDocumentFile and other places where filename is passed from specs list, 
# filename in list_sdd_specs now comes with "requirements/REQ-01.md" or "functional-requirements/RF-01.md".
# So the API will receive that directly. The backend splits by "/" and routes correctly.

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Updated app.js successfully')
