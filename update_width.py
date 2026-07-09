import builtins

path_html = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/index.html'
content_html = builtins.open(path_html, 'r', encoding='utf-8').read()
content_html = content_html.replace('max-width: 1200px;', 'max-width: 100%;')
builtins.open(path_html, 'w', encoding='utf-8').write(content_html)

path_css = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/static/settings-tabs.css'
content_css = builtins.open(path_css, 'r', encoding='utf-8').read()
content_css = content_css.replace('max-width: calc(100vw - 80px) !important;', 'max-width: 100% !important; width: 100% !important;')
builtins.open(path_css, 'w', encoding='utf-8').write(content_css)

print('Updated max-width successfully!')
