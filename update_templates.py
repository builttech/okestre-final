import builtins
import os

templates_dir = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/templates'

rf_template = '''# RF-[ID]-[SUB_ID]: [TÍTULO DO REQUISITO FUNCIONAL]

## 1. Identificação e REQ Pai
- **ID:** RF-[ID]-[SUB_ID]
- **Requisito Pai:** [ID do REQ Pai]
- **Responsável:** [Nome]

## 2. Objetivo e Contexto Funcional
[Descreva o objetivo deste RF específico e em qual contexto do sistema ele se aplica.]

## 3. História do Usuário
**Como** [tipo de usuário], 
**Quero** [realizar uma ação], 
**Para que** [eu obtenha um valor/benefício].

## 4. Descrição Funcional
[Descrição detalhada de como a funcionalidade deve se comportar do ponto de vista do usuário final e do sistema.]

## 5. Fluxo Funcional
1. O usuário faz X.
2. O sistema verifica Y.
3. O sistema executa Z.

## 6. Regras de Negócio e Validações Funcionais
- **RN01:** [Regra 1]
- **VAL01:** [Validação: Se X for inválido, o sistema deve impedir a ação.]

## 7. Dados Necessários
- [Campo 1]: [Tipo / Obrigatório?]
- [Campo 2]: [Tipo / Obrigatório?]

## 8. Permissões
- Apenas usuários com o papel [Role] podem acessar esta funcionalidade.

## 9. Integrações
- [Sistemas ou APIs externas que precisam ser chamadas para cumprir o RF.]

## 10. Mensagens
- **MSG01:** "Operação realizada com sucesso."
- **MSG02:** "Erro ao processar a requisição."

## 11. Fora do Escopo
- [O que não será entregue neste RF]

## 12. Dependências
- [Quais outros RFs ou atividades precisam estar prontos antes?]

## 13. Riscos e Pendências
- **Risco 1:** [Risco e mitigação]
- **Pendência 1:** [Dúvida a ser esclarecida]

## 14. Referências Visuais
- [Links para Figma, telas ou mockups, se aplicável.]

## 15. Critérios de Aceite (BDD)
- [ ] **Cenário:** [Nome do cenário]
      **Dado** que [contexto inicial]
      **Quando** [ação tomada]
      **Então** [resultado esperado]

## 16. Rastreabilidade e Próximos Artefatos
- **Artefatos afetados:** [Design, DRI, Task List]

## 17. Histórico
- [Versão] - [Data] - [Autor] - [Alteração]

## 18. Checklist de Qualidade
- [ ] História do usuário clara?
- [ ] Fluxo funcional contempla caminhos felizes e exceções?
- [ ] Regras e validações documentadas?
'''

builtins.open(os.path.join(templates_dir, 'RF-01-01-template.md'), 'w', encoding='utf-8').write(rf_template)

project_charter = '''# Project Charter (TAP)

## 1. Identificação do Projeto
- **Nome do Projeto:** [Nome]
- **Patrocinador:** [Nome]
- **Gerente de Projeto:** [Nome]

## 2. Histórico de Versão
- **Versão:** 1.0
- **Data:** [Data]
- **Alteração:** Criação inicial

## 3. Sumário Executivo
[Resumo do projeto]

## 4. Contexto e Justificativa
[Por que este projeto está sendo feito?]

## 5. Problema ou Oportunidade
[Qual problema o projeto resolve?]

## 6. Objetivos
[Metas SMART do projeto]

## 7. Escopo
[O que faz parte do projeto]

## 8. Fora do Escopo
[O que não faz parte do projeto]

## 9. Stakeholders
- [Nome do Stakeholder e Papel]

## 10. Premissas
- [Premissas assumidas]

## 11. Restrições
- [Restrições de tempo, custo, tecnologia]

## 12. Benefícios Esperados
- [ROI, métricas, melhorias]

## 13. Regras de Negócio Globais
- [Regras de negócio que afetam todo o projeto]

## 14. Fluxo Principal
[Visão macro de como o sistema deve funcionar]

## 15. Integrações
[Sistemas externos mapeados]

## 16. Relatórios e Indicadores
[Painéis e relatórios esperados]

## 17. Cenários
[Cenários de uso mapeados]

## 18. Entregáveis
- [O que será entregue]

## 19. Critérios de Aceite
- [Como validaremos o projeto]

## 20. Riscos
- [Risco e Mitigação]

## 21. Próximos Passos
- [Próximas etapas pós-aprovação da TAP]

## 22. Rastreabilidade
- [Fontes de referência]
'''

builtins.open(os.path.join(templates_dir, 'project-charter.md'), 'w', encoding='utf-8').write(project_charter)

task_md = '''# Task List

Controle rígido de execução das tarefas da Inteligência Artificial.

## RF-0001-01 — Título do RF

- [ ] TASK-RF-0001-01-001: Título curto da implementação.
- [ ] TASK-RF-0001-01-002: Título curto da implementação.
'''

builtins.open(os.path.join(templates_dir, 'task.md'), 'w', encoding='utf-8').write(task_md)

task_details = '''# Task Details

Documento oficial de plano detalhado das tasks. Acumulativo. Nunca apague tasks anteriores.

# TASK-RF-0001-01-001 — Título da Task
- **Objetivo:** [Objetivo da task]
- **Contexto:** [Contexto funcional]
- **História / Motivação:** [História do usuário ou necessidade técnica]
- **Escopo:** [O que será feito]
- **Fora do Escopo:** [O que não será feito]
- **Entradas:** [Dados ou parâmetros]
- **Saídas:** [Resultados esperados]
- **Atividades detalhadas:**
  1. Passo 1
  2. Passo 2
- **Regras relacionadas:** [RNs associadas]
- **Requisitos Técnicos:** [Exigências de framework/linguagem]
- **Arquivos Impactados:**
  - [NOVO] caminho/novo_arquivo.ts
  - [MODIFICAR] caminho/arquivo_existente.ts
- **Dados envolvidos:** [Tabelas/Campos]
- **APIs/Integrações:** [Endpoints]
- **Validações:** [Validações técnicas]
- **Comportamento Esperado:** [O que deve acontecer no fim]
- **Critérios de Aceite:** [Critérios]
- **Plano de testes:** [Como será testado]
- **Evidências:** [Como será comprovado]
- **Dependências:** [Tasks que precisam terminar antes]
- **Riscos / Pendências:** [Atenção]
- **Definition of Ready:** [Pronto para começar?]
- **Definition of Done:** [Pronto para finalizar?]

---

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.
'''

builtins.open(os.path.join(templates_dir, 'task.details.md'), 'w', encoding='utf-8').write(task_details)

print("Templates atualizados.")
