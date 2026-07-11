import builtins

path_js = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
path_correct = 'C:/Users/augus/.gemini/antigravity/brain/2d210172-a204-4a88-b3e2-5e404c3846ae/scratch/correct_js.js'

content = builtins.open(path_js, 'r', encoding='utf-8').read()
correct_content = builtins.open(path_correct, 'r', encoding='utf-8').read()

idx = content.find('// PRICING TAB LOGIC')
if idx != -1:
    content = content[:idx] + correct_content
    builtins.open(path_js, 'w', encoding='utf-8').write(content)
    print("app.js fixed!")
else:
    print("Could not find // PRICING TAB LOGIC in app.js")

