# Design — Planejamento Técnico do Projeto

## Projeto

git-ide

## 1. Arquitetura Proposta

### Referência

- REQ relacionado: `REQ-3091 — Rebrand visual dark technical console da ferramenta`.
- Fonte visual prioritária da correção: imagem de referência enviada pelo usuário no chat.
- Observação: a etapa anterior aplicou uma leitura light; a task atual corrige a direção para dark theme fiel à referência.

### Decisão técnica

O rebrand será implementado como uma evolução da camada visual já existente do produto, preservando a arquitetura estática atual:

- `gitide_server/static/index.html` continua carregando a estrutura principal da aplicação.
- `gitide_server/static/style.css` permanece como base histórica de estilos.
- `gitide_server/static/rebrand.css` permanece como camada final de override visual e será a principal superfície de implementação.
- `tokens.json` será atualizado para registrar tokens compatíveis com o novo sistema dark technical console.

A correção será aplicada no final de `rebrand.css` para garantir precedência sobre a camada light adicionada anteriormente, sem reescrever a estrutura completa do arquivo. A abordagem evita reescrita de HTML/JS e centraliza a mudança em CSS e tokens, reduzindo risco funcional.

### Componentes impactados

- Shell da aplicação.
- Topbar e marca.
- Sidebar e navegação lateral.
- Painéis principais dos módulos.
- Cards, cabeçalhos e seções.
- Botões, inputs, selects, textareas e estados de foco.
- Modais, abas, listas e itens selecionados.
- Tabelas, linhas, divisórias, áreas de terminal, editor, blocos de código e logs.

### Dados, APIs e integrações

Não há alteração prevista em banco de dados, APIs, endpoints, integrações, permissões ou contratos de backend. A mudança é visual.

### Segurança e permissões

Não há alteração de autenticação, tokens, permissões ou URLs de remoto. A regra de preservação de PATs continua aplicável.

### Riscos técnicos

- Como a aplicação possui estilos legados e muitas classes, alguns seletores podem exigir ajustes visuais posteriores por QA.
- A fonte exata da referência pode não estar instalada/disponível no ambiente do usuário; a implementação deve usar fallback seguro.
- A referência visual é mais compacta e orientada a dados do que a estrutura atual do GitIDE; a correção deve aproximar a estética sem quebrar layout ou funcionalidade existente.

## 2. Fluxos Técnicos

1. Atualizar o REQ `REQ-3091` para registrar a correção dark technical console.
2. Revisar e atualizar Design vivo, DRI, Task List e Task Details com `TASK-REQ-3091-002`.
3. Atualizar `tokens.json` para voltar o tema ativo para dark e registrar a paleta dark da referência.
4. Atualizar `index.html` apenas para versionar o CSS quando necessário.
5. Aplicar uma camada final em `rebrand.css` para sobrescrever o tema claro anterior com dark technical console.
6. Validar por leitura dos arquivos modificados, status Git e comando técnico aplicável quando liberado pelo Act IA.
7. Marcar `TASK-REQ-3091-002` como concluída somente após verificação.

## 3. Estratégia de Validação

- Revisar arquivos alterados via endpoint de leitura.
- Executar `git status` para auditar alterações.
- Executar teste/validação disponível do projeto quando o painel Act IA permitir.
- Confirmar que não houve alteração intencional de lógica JavaScript, backend, banco de dados ou endpoints.
- Registrar limitações visuais que dependam de inspeção manual no navegador.
