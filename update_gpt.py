import builtins
import re

path = 'C:/Users/augus/.workspace/act/git-ide/GPT_INSTRUCTIONS.md'
content = builtins.open(path, 'r', encoding='utf-8').read()

# Replace path definitions
content = content.replace(
    ".documents/requirements/<REQ_ID>_<TITLE>/<REQ_ID>_<TITLE>.MD",
    ".documents/requirements/REQ-ID-TITLE.MD"
)
content = content.replace(
    ".documents/requirements/<REQ_ID>_<TITLE>/functional-requirements/RF-XXXX-XX_TITLE.MD",
    ".documents/functional-requirements/RF-ID-TITLE.MD"
)
content = content.replace(
    "functional-requirements/RF-XXXX-XX_TITLE.MD",
    ".documents/functional-requirements/RF-ID-TITLE.MD"
)
content = content.replace(
    "e functional-requirements/RF-XXXX-XX_TITLE.MD",
    "e .documents/functional-requirements/RF-ID-TITLE.MD"
)

builtins.open(path, 'w', encoding='utf-8').write(content)
print('Updated GPT_INSTRUCTIONS.md')
