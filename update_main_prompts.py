import builtins

main_py = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/main.py'
content = builtins.open(main_py, 'r', encoding='utf-8').read()

import re

# Replace specific prompt strings
old_req_rule = "- REQ individual deve ficar em .documents/spec/*.md e conter obrigatoriamente: ## 1. Specify - Especificação Funcional, ### 1.1 Identificação e Metadados Básicos, ### 1.2 Contexto, ### 1.3 Objetivo Funcional, ### 1.4 Descrição do Requisito, ### 1.5 História de Usuário, ### 1.6 Regras de Negócio, ### 1.7 Restrições e Premissas, ### 1.8 Fora do Escopo, ### 1.9 Critérios de Aceite e ### 1.10 Rastreabilidade Funcional."
new_req_rule = "- REQ individual deve ficar em .documents/requirements/*.md e RFs em .documents/functional-requirements/*.md de acordo com a nomenclatura REQ-0000 e RF-0000-00."
content = content.replace(old_req_rule, new_req_rule)

old_task_rule = "- Task List deve ficar em .documents/task/task.md e conter somente itens no formato - [ ] TASK-REQ-0000-001: - Título curto ou - [ ] TASK-QA-XXXXXXXX-001: - Título curto."
new_task_rule = "- Task List deve ficar em .documents/task/task.md e conter somente itens no formato - [ ] TASK-RF-0000-00-001: Título curto ou - [ ] TASK-QA-XXXXXXXX-001: Título curto."
content = content.replace(old_task_rule, new_task_rule)

old_task_details_rule = "- Task Details deve ficar em .documents/task/task.details.md, ser acumulativo, nunca apagar seções anteriores e usar seções ## Plano — TASK-... contendo as subseções: Título, Objetivo, História do usuário, Escopo, Regras de negócio, Critérios de aceite, Dependências e Definition of Done, além de pedir a autorização única do pacote Harness."
new_task_details_rule = "- Task Details deve ficar em .documents/task/task.details.md, ser acumulativo, nunca apagar seções anteriores e usar seções # TASK-RF-... contendo as subseções exigidas e, ao final, pedir a autorização única do pacote Harness."
content = content.replace(old_task_details_rule, new_task_details_rule)

old_alert_rule = "Não coloque plano detalhado aqui. Use .documents/task/task.details.md para o plano da task atual."
new_alert_rule = "Não coloque plano detalhado aqui. Use .documents/task/task.details.md."
content = content.replace(old_alert_rule, new_alert_rule)

old_spec_fallback = "Regra: tente localizar em .documents/spec. Se não existir, crie o REQ antes de qualquer execução técnica usando obrigatoriamente o template oficial completo com seções 1.1 a 1.10."
new_spec_fallback = "Regra: Localize os requisitos em .documents/requirements e .documents/functional-requirements."
content = content.replace(old_spec_fallback, new_spec_fallback)

builtins.open(main_py, 'w', encoding='utf-8').write(content)
print("main.py updated!")
