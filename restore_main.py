import builtins

main_py = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(main_py, 'r', encoding='utf-8').read()

target_line = '# append_markdown_specs(functional_dir, "project_spec_file", ".documents/functional-requirements")'
if target_line in content:
    content = content.replace(target_line, 'append_markdown_specs(functional_dir, "project_spec_file", ".documents/functional-requirements")')
    builtins.open(main_py, 'w', encoding='utf-8').write(content)
    print("Fixed main.py!")
else:
    print("Line not found")
