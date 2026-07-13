import builtins
import re

app_js = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(app_js, 'r', encoding='utf-8').read()

# Fix sddRenderSpecList: use startsWith('RF-')
old_filter_req = "const reqs = specs.filter(s => !s.filepath.includes('functional-requirements'));"
new_filter_req = "const reqs = specs.filter(s => !s.filename.toUpperCase().startsWith('RF-') && !s.filepath.includes('functional-requirements'));"
content = content.replace(old_filter_req, new_filter_req)

old_filter_rf = "if (!s.filepath.includes('functional-requirements')) return false;"
new_filter_rf = "if (!s.filename.toUpperCase().startsWith('RF-') && !s.filepath.includes('functional-requirements')) return false;"
content = content.replace(old_filter_rf, new_filter_rf)

# Fix sddSelectSpec: use startsWith('RF-')
old_select_rf = "if (filename.includes('functional-requirements')) {"
new_select_rf = "if (filename.toUpperCase().startsWith('RF-') || filename.includes('functional-requirements')) {"
content = content.replace(old_select_rf, new_select_rf)

builtins.open(app_js, 'w', encoding='utf-8').write(content)
print("app.js updated again")
