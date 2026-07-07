# Task Details — Plano Detalhado da Task Atual

## Projeto

git-ide

> Arquivo acumulativo. Não sobrescreva detalhes de tasks anteriores.
> Para uma nova task, anexe uma nova seção `## Plano — TASK-REQ-0000-000` ao final.
> Para revisar uma task existente, atualize somente a seção daquela task.

## Plano — TASK-REQ-0000-001

**Tarefa:** Título curto da task.

### Objetivo

Descreva o objetivo técnico da task atual.

### Arquivo afetado

`[MODIFICAR] caminho/do/arquivo.ext`

### Fora desta task

- Não implementar escopo fora da task selecionada.

### Validação prevista

- Validar por leitura, teste ou comando aplicável.

Para autorizar, responda: **"Aprovado executar TASK-REQ-0000-001"**.

## Plano — TASK-REQ-3091-001

**Tarefa:** Aplicar rebrand visual baseado em design_rebrand.md.

### Objetivo

Implementar o rebrand visual Dayact IA-like definido em `design_rebrand.md`, convertendo a interface do GitIDE para uma estética clara, minimalista, técnica, monocromática e geométrica sem alterar comportamento funcional.

### Arquivo afetado

`[NOVO] .documents/spec/req-3091_rebrand_visual_dayact_ia.md`

`[MODIFICAR] .documents/design/design.md`

`[MODIFICAR] .documents/dri/dri.md`

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] tokens.json`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar o REQ oficial com as seções obrigatórias.
2. Atualizar Design vivo e DRI vivo com a estratégia visual.
3. Atualizar a Task List com item rastreável.
4. Atualizar este plano detalhado preservando seções anteriores.
5. Alterar `tokens.json` para refletir a paleta, tipografia e radius do novo rebrand.
6. Ajustar `index.html` apenas em título, marca textual e versão do CSS quando necessário.
7. Aplicar camada de override em `rebrand.css` para o tema claro Dayact-like.
8. Validar arquivos modificados e estado Git.
9. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se a fonte Switzer não estiver disponível como asset local, usar `Switzer` como primeira família CSS com fallback para `Inter` e system fonts.
- Se algum estilo legado tiver seletor mais específico, acrescentar override no final de `rebrand.css`, preservando a estrutura existente.
- Se não houver comando de build dedicado, validar por leitura dos arquivos alterados e `git status`.

### Fora desta task

- Não alterar lógica JavaScript.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não adicionar arquivos binários de fonte.
- Não criar estilos inline novos.
- Não fazer deploy.
- Não executar mudanças Git destrutivas.

### Validação prevista

- Ler trechos alterados de `tokens.json`, `index.html`, `rebrand.css`, `task.md` e documentos Harness.
- Executar `git status` para auditar alterações.
- Executar validação técnica disponível do projeto quando aplicável.
- Reportar limitações de validação visual que dependam de navegador.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-002

**Tarefa:** Ajustar rebrand para dark theme fiel à referência visual.

### Objetivo

Corrigir a implementação anterior do rebrand, substituindo a leitura light por uma estética dark technical console fiel à referência enviada pelo usuário: fundo quase preto, painéis retangulares, bordas finas, tipografia técnica/monospace, labels compactos, acentos verdes/vermelhos pontuais e ausência de glassmorphism colorido.

### Arquivo afetado

`[MODIFICAR] .documents/spec/req-3091_rebrand_visual_dayact_ia.md`

`[MODIFICAR] .documents/design/design.md`

`[MODIFICAR] .documents/dri/dri.md`

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] tokens.json`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Revisar o REQ `REQ-3091` para registrar a correção dark technical console.
2. Atualizar Design vivo e DRI vivo com a nova referência visual.
3. Adicionar a task `TASK-REQ-3091-002` na Task List.
4. Anexar este plano detalhado preservando seções anteriores.
5. Ajustar `tokens.json` para tema ativo dark e paleta técnica escura.
6. Atualizar a versão do CSS em `index.html` para bust de cache.
7. Adicionar camada final em `rebrand.css` para sobrescrever o override claro anterior.
8. Validar arquivos modificados e estado Git.
9. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se a fonte exata da referência não estiver disponível como asset local, usar pilha técnica com `Fira Code`, `SFMono-Regular`, `Consolas`, monospace.
- Se algum estilo legado tiver seletor mais específico, acrescentar override no final de `rebrand.css`, preservando a estrutura existente.
- Se o comando de teste continuar bloqueado pelo painel Act IA, validar por leitura dos arquivos alterados e `git status`.

### Fora desta task

- Não alterar lógica JavaScript.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não adicionar arquivos binários de fonte.
- Não criar estilos inline novos.
- Não fazer deploy.
- Não executar mudanças Git destrutivas.

### Validação prevista

- Ler trechos alterados de `tokens.json`, `index.html`, `rebrand.css`, `task.md` e documentos Harness.
- Executar `git status` para auditar alterações.
- Executar validação técnica disponível do projeto quando aplicável/liberada.
- Reportar limitações de validação visual que dependam de navegador.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-003

**Tarefa:** Aplicar corner brackets nos quatro cantos de todos os cards.

### Objetivo

Ajustar o detalhe visual de moldura técnica do rebrand dark para que o elemento de canto usado na referência apareça nos quatro cantos dos cards, painéis e modais principais, em vez de aparecer apenas no canto superior esquerdo.

### Arquivo afetado

`[MODIFICAR] .documents/dri/dri.md`

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar o DRI com a regra visual dos quatro corner brackets.
4. Atualizar `index.html` para bust de cache do CSS.
5. Adicionar camada final em `rebrand.css` com pseudo-elemento único desenhando os quatro cantos via backgrounds lineares.
6. Validar por leitura dos trechos alterados e `git status`.
7. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum card tiver pseudo-elemento próprio conflitante, sobrescrever o `::before` no final de `rebrand.css` com maior especificidade.
- Se um componente não aceitar pseudo-elemento por estrutura específica, incluí-lo explicitamente na lista de seletores de cards/painéis.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não fazer deploy.

### Validação prevista

- Ler o bloco CSS final aplicado.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.
- Reportar que a validação visual final depende de inspeção no navegador.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-004

**Tarefa:** Reduzir opacidade das bordas comuns sem alterar corner brackets.

### Objetivo

Diminuir a intensidade visual das bordas comuns do dark technical console para que fiquem menos brancas, preservando integralmente a cor, posição, tamanho e desenho dos corner brackets adicionados na task anterior.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Alterar somente as variáveis de borda comum no bloco dark console de `rebrand.css`.
4. Não alterar a variável usada pelos corner brackets (`--console-text-soft`) nem o bloco `Four-corner technical brackets`.
5. Atualizar `index.html` para bust de cache do CSS.
6. Validar por leitura dos trechos alterados e `git status`.
7. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se alguma borda continuar muito clara por usar valor fixo fora das variáveis, reportar para ajuste posterior em seletor específico.

### Fora desta task

- Não alterar corner brackets.
- Não alterar HTML estrutural.
- Não alterar JavaScript.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não fazer deploy.

### Validação prevista

- Confirmar que `--console-line`, `--console-line-strong` e `--console-line-soft` foram suavizadas.
- Confirmar que o bloco `Four-corner technical brackets` continua usando `--console-text-soft`.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-B9983968-001

**Tarefa:** Restaurar ícones Lucide da sidebar com stroke 0.75px.

### Objetivo

Corrigir a anotação `QA-B9983968`, restaurando a exibição dos ícones Lucide na navegação da sidebar, inclusive no estado colapsado, mantendo o rebrand dark technical console e aplicando `stroke-width: 0.75px` aos SVGs.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Adicionar override final em `rebrand.css` para desfazer o `display: none` aplicado aos ícones da sidebar.
4. Definir os ícones Lucide com tamanho compacto, `currentColor` e `stroke-width: 0.75px`.
5. Atualizar `index.html` para bust de cache do CSS.
6. Validar por leitura dos trechos alterados e `git status`.
7. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum ícone for renderizado como `<i data-lucide>` antes do bootstrap Lucide, manter também seletor para `i` sem interferir no SVG final.
- Se o estado colapsado tiver regras específicas mais fortes, usar escopo `.sidebar-collapsed .sidebar .nav-item svg` no override final.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar corner brackets.
- Não fazer deploy.

### Validação prevista

- Confirmar que o bloco anterior que escondia `.nav-item i` e `.nav-item svg` foi sobrescrito no final do CSS.
- Confirmar que os SVGs Lucide usam `stroke-width: 0.75px`.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-12681E16-001

**Tarefa:** Aplicar espaçamento interno no card Security Rules.

### Objetivo

Corrigir a anotação `QA-12681E16`, aplicando espaçamento interno adequado ao card da aba Security Rules em Settings, mantendo o rebrand dark technical console, os corner brackets e a estrutura funcional existente.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Adicionar override final em `rebrand.css` para o quinto painel de Settings, correspondente ao card Security Rules.
4. Aplicar padding interno consistente com o rebrand dark.
5. Atualizar `index.html` para bust de cache do CSS.
6. Validar por leitura dos trechos alterados e `git status`.
7. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se o seletor com `nth-of-type(5)` não cobrir o estado ativo em todos os cenários, adicionar seletor complementar para `.settings-tab-panel:nth-of-type(5) > .settings-card.card`.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar corner brackets.
- Não fazer deploy.

### Validação prevista

- Confirmar que o card Security Rules recebe padding interno.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-005

**Tarefa:** Padronizar padding e header dos cards de Settings.

### Objetivo

Padronizar todos os cards de Settings para manter consistência visual no rebrand dark technical console: `settings-card.card` deve usar `padding: 8px` em todos os lados, e o `card-header`/headers equivalentes devem ficar colados ao topo e às laterais do card, sem espaço entre o header e a borda externa.

### Arquivo afetado

`[MODIFICAR] .documents/dri/dri.md`

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar o DRI com a regra global de padding/header dos cards de Settings.
4. Substituir o ajuste pontual de `QA-12681E16` por uma regra global em `rebrand.css`.
5. Definir `settings-card.card` com `padding: 8px`.
6. Definir headers diretos do card com margem negativa horizontal/top para encostar no topo e laterais.
7. Atualizar `index.html` para bust de cache do CSS.
8. Validar por leitura dos trechos alterados e `git status`.
9. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum card de Settings usar header equivalente fora de `.card-header`, manter cobertura para `.panel-header` e `.panel-header-simple`.
- Se algum conteúdo interno ficar excessivamente colado abaixo do header, ajustar apenas seletor de conteúdo interno em etapa posterior, sem reabrir padding global do card.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar corner brackets.
- Não fazer deploy.

### Validação prevista

- Confirmar que `settings-card.card` usa `padding: 8px`.
- Confirmar que headers diretos dos cards de Settings usam margem negativa `-8px -8px 0` para encostar no topo e laterais.
- Confirmar que o ajuste pontual `padding: 32px` do card Security Rules foi substituído.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-006

**Tarefa:** Uniformizar botões primário, secundário e terciário em todas as páginas.

### Objetivo

Padronizar a hierarquia visual dos botões primário, secundário e terciário em todos os módulos do workspace, mantendo o rebrand dark technical console, tipografia mono, uppercase, cantos retos, estados consistentes e acentos operacionais discretos.

### Arquivo afetado

`[MODIFICAR] .documents/spec/req-3091_rebrand_visual_dayact_ia.md`

`[MODIFICAR] .documents/dri/dri.md`

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] tokens.json`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Atualizar REQ e DRI com a regra global de botões.
2. Registrar a task na Task List.
3. Anexar este plano detalhado preservando seções anteriores.
4. Atualizar tokens de botão primário, secundário e terciário em `tokens.json`.
5. Aplicar override final em `rebrand.css` cobrindo classes globais e variações usadas nos módulos.
6. Preservar `.btn-danger` como semântico de perigo.
7. Atualizar `index.html` para bust de cache do CSS.
8. Validar por leitura dos trechos alterados e `git status`.
9. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum módulo usar classe específica de botão não coberta, reportar para ajuste posterior ou incluir seletor complementar mantendo o padrão aprovado.
- Se um botão de ação crítica usar `.btn-danger`, preservar a semântica visual vermelha.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não fazer deploy.
- Não alterar corner brackets.

### Validação prevista

- Confirmar tokens de primário, secundário e terciário.
- Confirmar o bloco CSS final de hierarquia global de botões.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-007

**Tarefa:** Corrigir sidebar após padronização global de botões.

### Objetivo

Corrigir a quebra visual da sidebar causada pela regra global de botões aplicada sobre elementos `button.nav-item`, restaurando o comportamento de navegação lateral sem desfazer a hierarquia global de botões nas páginas.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Adicionar override final em `rebrand.css` para `.sidebar-nav .nav-item`, removendo a herança visual de botão global.
4. Restaurar layout normal da navegação com alinhamento à esquerda, largura total, ícone, label e brackets estáveis.
5. Preservar estado colapsado da sidebar com ícones visíveis e labels/brackets ocultos.
6. Atualizar `index.html` para bust de cache do CSS.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum seletor legado ainda afetar a sidebar, reforçar escopo com `.app-container .sidebar .sidebar-nav .nav-item` no final do CSS.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não desfazer a padronização global de botões fora da sidebar.
- Não fazer deploy.

### Validação prevista

- Confirmar que `.sidebar .nav-item` volta a usar layout de navegação, não layout de botão global.
- Confirmar que o estado colapsado mantém apenas ícones visíveis.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-B9CD0F01-001

**Tarefa:** Rebrand do sidebar interno de Settings.

### Objetivo

Corrigir a anotação `QA-B9CD0F01`, substituindo o visual antigo do sidebar interno de Settings por uma aparência compatível com o rebrand dark technical console, removendo radius grande, glass/shadow antigo e botões arredondados.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Adicionar override final em `rebrand.css` para `.settings-dashboard-layout.gitide-settings-tabs-ready`, `.settings-tabs-sidebar`, `.settings-tabs-title` e `.settings-tab-button`.
4. Remover visual antigo do sidebar interno: radius grande, background glass, sombras e botões arredondados.
5. Aplicar layout dark technical console: borda fina, radius zero, tipografia mono uppercase, botões retangulares, hover/active discretos e ícones Lucide com stroke `0.75px`.
6. Atualizar `index.html` para bust de cache do CSS.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se `settings-tabs.css` tiver especificidade superior em algum ponto, reforçar o escopo com `.app-container .settings-dashboard-layout.gitide-settings-tabs-ready` no override final.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar a sidebar principal do app.
- Não fazer deploy.

### Validação prevista

- Confirmar que o sidebar interno de Settings usa fundo/painel dark, radius zero e sem sombra antiga.
- Confirmar que botões de Settings usam visual retangular dark console com estados hover/active.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-B9CD0F01-002

**Tarefa:** Adicionar corner brackets ao sidebar interno de Settings.

### Objetivo

Adicionar os corner brackets técnicos nos quatro cantos do sidebar interno de Settings, usando o mesmo padrão visual dos cards do rebrand dark technical console.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Adicionar `position: relative` no sidebar interno de Settings.
4. Criar pseudo-elemento `::before` em `.settings-tabs-sidebar` desenhando os quatro corner brackets via backgrounds lineares.
5. Usar `var(--console-text-soft)` para manter consistência com os cards.
6. Atualizar `index.html` para bust de cache do CSS.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se o pseudo-elemento conflitar com outro estilo futuro, reforçar o seletor no final do CSS e manter `pointer-events: none`.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar a sidebar principal do app.
- Não alterar os corner brackets já existentes dos cards.
- Não fazer deploy.

### Validação prevista

- Confirmar que `.settings-tabs-sidebar::before` desenha os quatro cantos.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-6D40FE91-001

**Tarefa:** Rebrand do popover de workspace/conta.

### Objetivo

Corrigir a anotação `QA-6D40FE91`, refinando o popover de workspace/conta para o novo layout dark technical console, removendo glassmorphism antigo, radius grande e sombra pesada, sem alterar o comportamento JavaScript existente.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Adicionar override final em `rebrand.css` para popover, trigger, itens, divisores, modo rápido, submenu e opções de workspace.
4. Remover radius grande, blur/glass antigo e sombras pesadas.
5. Aplicar fundo dark técnico, bordas finas, radius zero, tipografia mono uppercase, hover/active discreto e ícones Lucide com `stroke-width: 0.75px`.
6. Adicionar corner brackets ao popover principal e ao submenu de organização.
7. Atualizar `index.html` para bust de cache do CSS.
8. Validar por leitura dos trechos alterados e `git status`.
9. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum estilo de `workspace-switcher-refactor.css` prevalecer, reforçar escopo com `.app-container .workspace-switcher.workspace-account-menu` no final do CSS.
- Se o submenu lateral precisar de ajuste posterior, preservar esta task como rebrand base do popover e abrir QA específico.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar a sidebar principal do app.
- Não fazer deploy.

### Validação prevista

- Confirmar que o popover principal usa visual dark technical console.
- Confirmar que popover e submenu têm corner brackets.
- Confirmar que os itens internos usam botões retangulares e estados hover/active discretos.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-0CD44BEE-001

**Tarefa:** Encurtar labels do menu principal da sidebar.

### Objetivo

Corrigir a anotação `QA-0CD44BEE`, reduzindo os textos visíveis dos itens do menu principal da sidebar para labels mais curtos, preservando tooltips completos, ícones, `data-tab` e comportamento de navegação atual.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Alterar apenas o conteúdo textual de `.nav-label` nos botões da sidebar principal.
4. Manter atributos `title` originais para tooltip/acessibilidade.
5. Manter `data-tab`, ícones Lucide, classes e estrutura HTML existentes.
6. Validar por leitura do trecho alterado e `git status`.
7. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum label for renderizado por JavaScript em etapa posterior, ajustar apenas a fonte responsável pelo texto, preservando o mesmo mapeamento aprovado.

### Fora desta task

- Não alterar CSS.
- Não alterar JavaScript.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar ícones.
- Não alterar `data-tab`.
- Não fazer deploy.

### Validação prevista

- Confirmar que os labels visíveis da sidebar foram encurtados conforme `QA-0CD44BEE`.
- Confirmar que os atributos `title` completos foram preservados.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-67617C17-001

**Tarefa:** Rebrand do card de autenticação Git PAT.

### Objetivo

Corrigir a anotação `QA-67617C17`, atualizando o card de autenticação Git PAT para o padrão dark technical console, removendo aparência antiga dos elementos internos e preservando IDs, fluxo JavaScript e segurança do token.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar `index.html` para bust de cache do CSS.
4. Adicionar override final em `rebrand.css` para `.git-credentials-card.card`, header, body, textos, input, container do comando gerado e botão de cópia.
5. Aplicar fundo dark técnico, borda fina, radius zero, header colado ao topo/laterais, espaçamento interno consistente e estados de foco coerentes.
6. Preservar corner brackets existentes do card.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum inline style prevalecer, reforçar o override final em `rebrand.css` com escopo `.app-container #tab-git .git-credentials-card`.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar IDs ligados ao token ou ao comando gerado.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não registrar, expor ou manipular o valor do token.
- Não fazer deploy.

### Validação prevista

- Confirmar que `.git-credentials-card` usa visual dark technical console.
- Confirmar que input e comando gerado usam estilo técnico consistente.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-02D8DF27-001

**Tarefa:** Rebrand dos inputs e botões do card de operações Git.

### Objetivo

Corrigir a anotação `QA-02D8DF27`, atualizando inputs, botões e espaçamentos internos do card `Ações e Deploy Automático` para o padrão dark technical console, preservando IDs, estrutura HTML e comportamento JavaScript do fluxo Git.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar `index.html` para bust de cache do CSS.
4. Adicionar override final em `rebrand.css` para `.git-operations-card.card`, header, body, campos, input de commit, botão IA, branch atual, ações principais e ações avançadas.
5. Aplicar fundo dark técnico, borda fina, radius zero, header colado ao topo/laterais, espaçamento interno consistente, input técnico e botões retangulares.
6. Preservar semântica de perigo para `Abort merge`.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum inline style ou seletor legado prevalecer, reforçar o override final com escopo `.app-container #tab-git .git-operations-card`.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar IDs ligados às ações Git.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não executar comandos Git.
- Não fazer deploy.

### Validação prevista

- Confirmar que `.git-operations-card` usa visual dark technical console.
- Confirmar que input, botão IA, branch atual e botões Git usam estilo técnico consistente.
- Confirmar que `index.html` aponta para a nova versão de `rebrand.css`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-REQ-3091-008

**Tarefa:** Corrigir base do dark theme para Black 950 #050505.

### Objetivo

Corrigir a base cromática do dark theme para usar o token Black 950 `#050505` como fundo principal, removendo usos anteriores de `#030303` em canvas/base/input e alinhando `tokens.json` e `rebrand.css` ao feedback visual do usuário.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] .documents/spec/req-3091_rebrand_visual_dayact_ia.md`

`[MODIFICAR] .documents/dri/dri.md`

`[MODIFICAR] tokens.json`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task REQ na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar o REQ-3091 para declarar Black 950 `#050505` como base obrigatória do dark theme.
4. Atualizar o DRI para trocar `Background #030303 / #050505` por `Background #050505`.
5. Atualizar `tokens.json` em `theme/dark.color.background` para `#050505`.
6. Atualizar `rebrand.css` para `--console-bg: #050505` e substituir usos críticos de `#030303` por `#050505`.
7. Atualizar `index.html` para bust de cache do CSS.
8. Validar por leitura dos trechos alterados e `git status`.
9. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se alguma superfície ficar visualmente sem hierarquia após a correção do fundo base, preservar painéis em `--console-panel`/`--console-panel-2` e ajustar apenas os fundos de canvas/input/base, sem reabrir o escopo de layout.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML além do cache bust.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não alterar acentos verdes/vermelhos.
- Não alterar corner brackets.
- Não fazer deploy.

### Validação prevista

- Confirmar que `tokens.json` usa `#050505` como background dark.
- Confirmar que `rebrand.css` usa `--console-bg: #050505`.
- Confirmar que `index.html` aponta para `rebrand.css?v=57`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-24C4E55D-001

**Tarefa:** Rebrand da navegação superior do Harness.

### Objetivo

Corrigir a anotação `QA-24C4E55D`, refinando a navegação superior do módulo Harness para o padrão dark technical console, removendo radius alto, background antigo e tabs arredondadas.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar `index.html` para bust de cache do CSS.
4. Adicionar override final em `rebrand.css` para `.harness-header`, `.harness-top-nav`, `.harness-top-tab`, estados hover/active e ícones.
5. Aplicar fundo Black 950, bordas finas, radius zero, botões retangulares, tipografia mono uppercase e active com acento verde discreto.
6. Preservar estrutura HTML, `data-harness-panel` e comportamento JavaScript.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum seletor legado prevalecer, reforçar o override final com escopo `.app-container #tab-sdd .harness-shell`.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar conteúdo textual dos tabs.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não fazer deploy.

### Validação prevista

- Confirmar que `.harness-top-nav` usa visual dark technical console.
- Confirmar que `.harness-top-tab` usa tabs retangulares e estados hover/active consistentes.
- Confirmar que `index.html` aponta para `rebrand.css?v=58`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.

## Plano — TASK-QA-2773B6E8-001

**Tarefa:** Rebrand da lista de especificações do Harness.

### Objetivo

Corrigir a anotação `QA-2773B6E8`, refinando a lista lateral de especificações do Harness para o padrão dark technical console, removendo radius antigo e melhorando a hierarquia visual dos títulos e metadados.

### Arquivo afetado

`[MODIFICAR] .documents/task/task.md`

`[MODIFICAR] .documents/task/task.details.md`

`[MODIFICAR] gitide_server/static/rebrand.css`

`[MODIFICAR] gitide_server/static/index.html`

### Formato previsto da chamada

1. Registrar a task QA na Task List.
2. Anexar este plano detalhado preservando seções anteriores.
3. Atualizar `index.html` para bust de cache do CSS.
4. Adicionar override final em `rebrand.css` para `#sdd-specs-list`, `.specs-list`, `.spec-item`, estados hover/active, `.spec-item-title`, `.spec-item-meta` e `.specs-empty-state`.
5. Aplicar itens retangulares, fundo técnico, borda fina, tipografia mono uppercase, metadados compactos e active com acento verde discreto.
6. Preservar renderização JavaScript, clique, seleção e conteúdo textual.
7. Validar por leitura dos trechos alterados e `git status`.
8. Marcar a task como concluída em `task.md` somente após execução e verificação.

### Fallback previsto

- Se algum seletor legado prevalecer, reforçar o override final com escopo `.app-container #tab-sdd #sdd-specs-list`.

### Fora desta task

- Não alterar JavaScript.
- Não alterar estrutura HTML.
- Não alterar conteúdo textual das specs.
- Não alterar backend, banco de dados, endpoints, permissões ou autenticação.
- Não fazer deploy.

### Validação prevista

- Confirmar que `#sdd-specs-list` e `.spec-item` usam visual dark technical console.
- Confirmar que hover/active foram padronizados com tabs retangulares e acento verde discreto.
- Confirmar que `index.html` aponta para `rebrand.css?v=59`.
- Executar `git status` para auditar alterações.

Para autorizar a execução de todas as tasks planejadas, responda: **"Aprovado executar o pacote Harness"**.
