import builtins

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(path, 'r', encoding='utf-8').read()

content = content.replace(\"className = 'btn-icon btn-generate-business-doc documents-row-action';\", \"className = 'btn-icon btn-generate-business-doc';\")
content = content.replace(\"className = 'btn-icon btn-download-doc documents-row-action';\", \"className = 'btn-icon btn-download-doc';\")

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Removed documents-row-action class successfully!')
