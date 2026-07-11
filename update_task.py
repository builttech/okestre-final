import builtins
path = 'C:/Users/augus/.gemini/antigravity/brain/2d210172-a204-4a88-b3e2-5e404c3846ae/task.md'
content = builtins.open(path, 'r', encoding='utf-8').read()
content = content.replace('- [/] 5', '- [x] 5')
builtins.open(path, 'w', encoding='utf-8').write(content)
