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
