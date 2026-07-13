import builtins
import os

templates_dir = 'C:/Users/augus/.workspace/act/git-ide/gitide_server/templates'

design_md = '''# Design e Arquitetura do Projeto

## 1. Identificação
- **Projeto:** [Nome]
- **Data:** [Data]

## 2. Objetivo
[Qual o objetivo deste design?]

## 3. Visão Técnica Geral
[Visão macro da solução técnica]

## 4. Módulos Impactados
- [Módulo A]
- [Módulo B]

## 5. Arquitetura Funcional
[Como os módulos interagem funcionalmente]

## 6. Arquitetura Técnica
[Desenho da infra, cloud, containers, componentes]

## 7. Modelo de Dados Conceitual
[Estrutura de tabelas e entidades]

## 8. Integrações
[Sistemas externos]

## 9. Serviços ou APIs previstas
[Endpoints principais e contratos]

## 10. Permissões
[Modelo de acesso e roles]

## 11. Estratégia de Frontend
[Framework, state management, patterns]

## 12. Estratégia de Backend
[Linguagem, framework, ORM, padrões]

## 13. Estratégia de Banco de Dados
[SQL/NoSQL, estratégias de indexação]

## 14. Estratégia de Logs e Auditoria
[O que e como será logado]

## 15. Estratégia de QA
[Testes automatizados, CI/CD]

## 16. Dependências Técnicas
[Bibliotecas críticas, infraestrutura pré-requisito]

## 17. Riscos Técnicos
[Gargalos de performance, lock-in, etc.]

## 18. Decisões Técnicas
[Trade-offs mapeados]

## 19. Rastreabilidade com REQs/RFs
- Atende aos REQs: [Lista]

## 20. Próximos Passos
[O que fazer agora]
'''

builtins.open(os.path.join(templates_dir, 'design.md'), 'w', encoding='utf-8').write(design_md)


dri_md = '''# Documento de Requisito de Interface (DRI)

Este documento centraliza as especificações de interfaces (telas, modais, componentes visuais) do projeto.

# RI-0001 — [Nome da Interface]

## 1. Identificação da Interface
- **ID:** RI-0001
- **Nome:** [Nome]
- **RF Vinculado:** [RF-0001-01]

## 2. Objetivo
[O que a interface resolve]

## 3. Contexto de Uso
[Onde o usuário está quando acessa isso]

## 4. Arquitetura da Informação
[Como os dados estão organizados na tela]

## 5. Mapa de Componentes
- [Header, Sidebar, Formulário, Tabela]

## 6. Regras de Exibição
[Condicionais de UI]

## 7. Estados
- **Loading:** [Spinner, Skeleton]
- **Empty:** [Ilustração, mensagem]
- **Error:** [Toaster, red alert]

## 8. Fluxo de Interação
[O que acontece quando clica no botão X]

## 9. Mapeamento de Dados
[De onde vem cada dado exibido na tela]

## 10. Hierarquia Visual
[Prioridade dos elementos]

## 11. Microcopy
[Textos curtos de botões, tooltips, placeholders]

## 12. Responsividade
[Como se comporta no mobile/tablet]

## 13. Acessibilidade
[Aria-labels, contraste, navegação por teclado]

## 14. Critérios de Aceite
- [ ] O componente X aparece quando Y.

## 15. Lacunas e Premissas
[O que falta definir]

## 16. Fora do Escopo
[O que não terá nessa interface]

## 17. Evoluções Futuras
[O que pode ser feito numa v2]

## 18. Rastreabilidade
- **Design no Figma:** [Link]
'''

builtins.open(os.path.join(templates_dir, 'dri.md'), 'w', encoding='utf-8').write(dri_md)

print("Design e DRI atualizados.")
