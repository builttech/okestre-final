# Design — Planejamento Técnico do Projeto

## Projeto

git-ide

## 1. Arquitetura Proposta

### Referência

- REQ relacionado: `REQ-3091 — Rebrand visual Dayact IA-like da ferramenta`.
- Fonte visual: `design_rebrand.md`.

### Decisão técnica

O rebrand será implementado como uma evolução da camada visual já existente do produto, preservando a arquitetura estática atual:

- `gitide_server/static/index.html` continua carregando a estrutura principal da aplicação.
- `gitide_server/static/style.css` permanece como base histórica de estilos.
- `gitide_server/static/rebrand.css` permanece como camada final de override visual e será a principal superfície de implementação.
- `tokens.json` será atualizado para registrar os tokens compatíveis com o novo sistema visual.

A abordagem evita reescrita de HTML/JS e centraliza a mudança em CSS e tokens, reduzindo risco funcional.

### Componentes impactados

- Shell da aplicação.
- Topbar e marca.
- Sidebar e navegação lateral.
- Painéis principais dos módulos.
- Cards, cabeçalhos e seções.
- Botões, inputs, selects, textareas e estados de foco.
- Modais, abas, listas e itens selecionados.
- Áreas de terminal, editor, blocos de código e logs.

### Dados, APIs e integrações

Não há alteração prevista em banco de dados, APIs, endpoints, integrações, permissões ou contratos de backend. A mudança é visual.

### Segurança e permissões

Não há alteração de autenticação, tokens, permissões ou URLs de remoto. A regra de preservação de PATs continua aplicável.

### Riscos técnicos

- Como a aplicação possui estilos legados e muitas classes, alguns seletores podem exigir ajustes visuais posteriores por QA.
- A fonte `Switzer` pode não estar instalada/disponível no ambiente do usuário; a implementação deve usar fallback seguro.
- A mudança de tema escuro para claro pode revelar pontos específicos com contraste insuficiente em módulos menos usados.

## 2. Fluxos Técnicos

1. Criar o REQ `REQ-3091` com base na solicitação e em `design_rebrand.md`.
2. Revisar e atualizar Design vivo, DRI, Task List e Task Details.
3. Atualizar tokens do design system para refletir a paleta clara Dayact-like.
4. Atualizar `index.html` apenas em título/brand copy e versão do CSS quando necessário.
5. Aplicar overrides em `rebrand.css` para transformar o tema visual atual em claro, minimalista, monocromático e geométrico.
6. Validar por leitura dos arquivos modificados, status Git e comando técnico aplicável.
7. Marcar a task concluída somente após verificação.

## 3. Estratégia de Validação

- Revisar arquivos alterados via endpoint de leitura.
- Executar `git status` para auditar alterações.
- Executar teste/validação disponível no projeto quando aplicável e aprovado pelo pacote Harness.
- Confirmar que não houve alteração intencional de lógica JavaScript, backend, banco de dados ou endpoints.
- Registrar limitações visuais que dependam de inspeção manual no navegador.
