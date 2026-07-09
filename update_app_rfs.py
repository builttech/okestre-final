import builtins
import re

path = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/app.js'
content = builtins.open(path, 'r', encoding='utf-8').read()

old_logic = '''            const reqId = sddState.activeReqId;
            const rfs = specs.filter(s => s.filename.includes('functional-requirements') && s.filename.toLowerCase().includes(reqId.toLowerCase()));'''

new_logic = '''            const reqId = sddState.activeReqId;
            const reqNumMatch = reqId ? reqId.match(/REQ-(\\d+)/i) : null;
            const reqNum = reqNumMatch ? reqNumMatch[1] : reqId;
            
            const rfs = specs.filter(s => {
                if (!s.filename.includes('functional-requirements')) return false;
                // Se for a estrutura aninhada antiga, o caminho contém o REQ ID inteiro
                if (s.filename.toLowerCase().includes(reqId.toLowerCase())) return true;
                // Na nova estrutura achatada, o arquivo chama RF-<ID>-<SUBID>
                const fname = s.filename.split('/').pop().toUpperCase();
                return fname.startsWith(\RF-\-\);
            });'''

content = content.replace(old_logic, new_logic)

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Updated app.js correctly for RF loading')
