# Estimativa Global do Projeto

> Revisada em 2026-10-12T01:06:49.761Z para REQ-0003 Local Devices; 6 tarefas abertas; valor-hora R$ 150.00; capacidade diária 8h.

## Resumo Executivo

| Cenário | Horas | Dias úteis equivalentes | Custo |
| --- | ---: | ---: | ---: |
| Sem IA | 47.0h | 5.88 | R$ 7050.00 |
| Com IA (esforço humano) | 21.0h | 2.63 | R$ 3150.00 |
| Economia estimada | 26.0h | - | R$ 3900.00 (55.3%) |

## Estimativa por Tarefa Aberta

| Tarefa | Título | Tipo | Área | Complexidade | Sem IA | Com IA | Economia |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| TASK-RF-0003-01-001 | Localizar a implementação real de local-devices e integrar navegação em duas abas. | implementation | frontend | high | 6.0h | 2.5h | 3.5h |
| TASK-RF-0003-01-002 | Implementar listagem de computadores, seleção e empty state com Adicionar dispositivo. | implementation | frontend | medium | 5.0h | 2.0h | 3.0h |
| TASK-RF-0003-02-001 | Criar persistência e endpoints para computadores e emissão segura de chaves com validade. | implementation | backend | high | 12.0h | 6.0h | 6.0h |
| TASK-RF-0003-02-002 | Implementar modal de cadastro com validade e visualização única da chave. | implementation | frontend | medium | 6.0h | 2.5h | 3.5h |
| TASK-RF-0003-03-001 | Implementar cadastro, listagem e remoção de vínculos de pastas por computador. | implementation | backend | high | 10.0h | 4.5h | 5.5h |
| TASK-RF-0003-03-002 | Implementar cards de pastas, confirmação de exclusão e testes de segurança e interface. | implementation | frontend | medium | 8.0h | 3.5h | 4.5h |

## Justificativas técnicas individuais

- **TASK-RF-0003-01-001**: Há incerteza estrutural: a tela local-devices não aparece na árvore atual. O esforço contempla localizar o serviço real, conferir contratos, integrar tabs e validar a navegação. A IA acelera busca e revisão, mas o diagnóstico técnico e integração dependem do ambiente.
- **TASK-RF-0003-01-002**: Listagem remota e empty state requerem controle de estados assíncronos, seleção persistente e segurança entre usuários. A IA acelera os componentes e a revisão, com testes e ajuste de integração ainda necessários.
- **TASK-RF-0003-02-001**: Persistência com migração eventual, emissão criptográfica de credenciais, cálculo de meses, transações, idempotência e autorização multiusuário exigem revisão humana extensa. O ganho com IA é moderado pela criticidade de segurança.
- **TASK-RF-0003-02-002**: Modal acessível, expiração, validações e apresentação única da chave incluem estados sensíveis e tratamento de falhas. A IA gera estrutura e handlers, mantendo revisão humana de segurança e comportamento.
- **TASK-RF-0003-03-001**: Modelo relacional e APIs de pastas exigem isolamento entre computadores, validação de caminhos remotos e garantia de exclusão apenas cadastral. Testes de permissão e preservação dos arquivos físicos elevam esforço.
- **TASK-RF-0003-03-002**: Cards, formulários, confirmação de exclusão, responsividade e QA de múltiplos computadores/pastas exigem integração E2E. A IA acelera UI e testes, mas homologação e regressão permanecem humanas.

## Incertezas da estimativa

- O módulo `local-devices` não consta do workspace 46 verificado. O esforço de inventário da TASK-RF-0003-01-001 é bloqueante; se o frontend residir fora deste repositório, revisar planejamento e estimativas antes da implementação.
- Não confundir esforço técnico estimado com promessa de calendário. Testes de integração com agente remoto e regras de autenticação real podem ampliar escopo.
- Registros concluídos anteriormente permanecem no histórico e não entram nestes totais.

## Histórico de Tarefas Fechadas

> 10 tarefa(s) concluída(s) preservada(s) no histórico de estimativas.

| Tarefa | Título | Tipo | Área | Complexidade | Sem IA | Com IA | Economia |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| TASK-QA-QA-C118E4B1-001 | Garantir exibição da seção Auto Layout ao selecionar frame no Design Canvas | correction | frontend | low | 1.0h | 0.3h | 0.7h |
| TASK-RF-0001-01-001 | Adicionar modelo de Auto Layout e ativação/remoção em frames | implementation | frontend | medium | 2.0h | 0.7h | 1.3h |
| TASK-RF-0001-02-001 | Implementar motor Flex Layout para frames no Konva | implementation | frontend | high | 4.5h | 1.4h | 3.1h |
| TASK-RF-0001-03-001 | Criar controles de Auto Layout no inspector da aba Design | implementation | frontend | medium | 2.5h | 0.8h | 1.7h |
| TASK-RF-0001-04-001 | Implementar persistência, undo/redo e validação da feature Auto Layout | implementation | frontend | medium | 1.5h | 0.5h | 1.0h |
| TASK-RF-0002-01-001 | Implementar estado de viewport e conversões Screen/World | implementation | frontend | medium | 2.0h | 0.7h | 1.3h |
| TASK-RF-0002-02-001 | Implementar zoom relativo ao cursor, botões e atalhos de zoom | implementation | frontend | medium | 2.5h | 0.8h | 1.7h |
| TASK-RF-0002-03-001 | Implementar pan por wheel, trackpad, botão central, Hand e Space Drag | implementation | frontend | medium | 2.5h | 0.8h | 1.7h |
| TASK-RF-0002-04-001 | Implementar stage responsivo, touch/pinch e grid dinâmico | implementation | frontend | high | 3.0h | 1.0h | 2.0h |
| TASK-RF-0002-05-001 | Persistir viewport por página e validar performance/acessibilidade | implementation | frontend | medium | 1.5h | 0.5h | 1.0h |

## Premissas

- A estimativa considera somente as tarefas em aberto de REQs, RFs, Task List e Task Details.
- Tarefas concluídas (`[x]`) não entram no esforço, prazo ou custo projetado.
- Cada task é estimada individualmente a partir do título, Task Details e documentos vinculados.
- A estimativa não usa valores fixos por task e não preenche artificialmente a capacidade diária disponível.
- O cenário Sem IA representa execução manual por profissional técnico.
- O cenário Com IA representa o esforço humano real para orientar, revisar, validar, corrigir e aprovar a execução com apoio do Act IA.
- O ganho com IA é estimado individualmente por task, sem aplicar percentual fixo de redução.
- Horas, custos, capacidade diária e sequência devem ser revisados quando o escopo documental mudar.
