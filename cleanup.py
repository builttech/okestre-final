import builtins

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/agent.py'
lines = builtins.open(path, encoding='utf-8').read().split('\n')

for i in range(len(lines) - 1, -1, -1):
    if "yield f\"data: {json.dumps({'type': 'start'" in lines[i]:
        if "step = 0" in lines[i+2]:
            del lines[i]
            break

builtins.open(path, 'w', encoding='utf-8').write('\n'.join(lines))
