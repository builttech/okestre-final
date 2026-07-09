import builtins
import re

# Update settings-tabs.js height
path_js = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/settings-tabs.js'
content_js = builtins.open(path_js, 'r', encoding='utf-8').read()
content_js = content_js.replace('height: 500px;', 'height: calc(100vh - 180px); min-height: 500px;')
builtins.open(path_js, 'w', encoding='utf-8').write(content_js)

# Update settings-tabs.css max-width
path_css = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/settings-tabs.css'
content_css = builtins.open(path_css, 'r', encoding='utf-8').read()
content_css = content_css.replace('max-width: 1180px !important;', 'max-width: calc(100vw - 80px) !important;')
builtins.open(path_css, 'w', encoding='utf-8').write(content_css)

print('Updated UI styling successfully!')
