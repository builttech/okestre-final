import builtins
import re

app_js = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(app_js, 'r', encoding='utf-8').read()

# Replace filename checks with filepath checks
content = content.replace("s.filename.includes('functional-requirements')", "s.filepath.includes('functional-requirements')")
content = content.replace("s.filename.toLowerCase().includes(reqId.toLowerCase())", "s.filepath.toLowerCase().includes(reqId.toLowerCase())")

builtins.open(app_js, 'w', encoding='utf-8').write(content)
print("app.js updated")
