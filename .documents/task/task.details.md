# Task Details — Plano Detalhado da Task Atual

## Projeto

git-ide

> Arquivo acumulativo. Não sobrescreva detalhes de tasks anteriores.
> Para uma nova task, anexe uma nova seção `## Plano — TASK-REQ-0000-000` ao final.
> Para revisar uma task existente, atualize somente a seção daquela task.
# TASK-RF-0001-01-001 — Adicionar modelo de Auto Layout e ativação/remoção em frames

## Identificação da task

- ID: `TASK-RF-0001-01-001`
- RF: `RF-0001-01`
- Tipo: implementação frontend
- Status inicial: aberta

## Objetivo

Adicionar ao modelo local do Design Canvas propriedades de Auto Layout em frames e permitir ativar/remover layout em um frame selecionado.

## Contexto

O canvas usa `state.doc.nodes` como lista flat e `parentId` como hierarquia. A task deve manter esse padrão, adicionando `layout` em frames e `layoutItem` em filhos de maneira defensiva.

## História técnica

Como usuário da aba Design, preciso ativar Auto Layout em um frame para que seus filhos passem a ser organizados automaticamente sem perder a estrutura existente.

## Escopo

- Criar defaults de layout.
- Normalizar documentos antigos.
- Ativar Auto Layout em frame selecionado.
- Remover Auto Layout preservando coordenadas visuais.
- Preparar dados de filho estático/absoluto.

## Fora do escopo

- Grid Layout.
- Multi-seleção completa.
- Backend novo.

## Entradas

- `RF-0001-01`
- `.documents/design/design.md`
- `gitide_server/static/konva-designer.js`

## Saídas

- Funções de modelo e ativação/remoção em `konva-designer.js`.
- Documento local compatível com `layout` e `layoutItem`.

## Atividades

1. Adicionar estado de histórico e helpers de clone.
2. Criar `defaultAutoLayout()`.
3. Criar normalização de layout em frames.
4. Criar `enableAutoLayout()` e `disableAutoLayout()`.
5. Integrar recalculo e renderização.

## Regras relacionadas

- Não criar estilos inline.
- Não alterar backend.
- Preservar documentos antigos.

## Requisitos técnicos

- JavaScript compatível com browser atual.
- Modelo local continua sendo a fonte oficial.
- Valores numéricos negativos são normalizados para zero.

## Arquivos / Componentes Impactados

- `[MODIFICAR] gitide_server/static/konva-designer.js`

## Dados envolvidos

- `state.doc.nodes[].layout`
- `state.doc.nodes[].layoutItem`

## APIs/serviços/integrações

- Nenhuma API nova.

## Validações

- Revisão estática dos helpers adicionados.
- Verificar que documentos sem layout continuam carregando.

## Comportamento esperado

Frame selecionado pode receber e remover Auto Layout sem perder filhos e sem quebrar parentId.

## Critérios de aceite

- Layout é ativado em frame selecionado.
- Layout é removido preservando coordenadas atuais.
- Filhos recebem propriedades necessárias sem quebrar renderização.

## Plano de testes

- Selecionar frame padrão.
- Ativar Auto Layout.
- Remover Auto Layout.
- Conferir JSON exportado.

## Evidências

- Implementação aplicada nos arquivos aprovados.
- Revisão técnica por leitura executada nos trechos alterados em `gitide_server/static/konva-designer.js`, `gitide_server/static/konva-designer.html` e `gitide_server/static/rebrand.css`.
- Validação sintática executável solicitada com `node --check gitide_server/static/konva-designer.js`, mas o runtime local retornou `/bin/sh: 1: node: not found`.
- Conforme regra de validação em VM, a ausência de Node local não foi tratada como falha do código.
- Validação alternativa realizada por leitura técnica: fechamento de funções, objetos, arrays, templates, handlers, integração com inspector, persistência e ausência de erro sintático evidente.
- Task marcada como concluída após validação técnica alternativa documentada.

## Dependências

- Canvas Konva existente.

## Riscos

- Dados antigos incompletos podem exigir normalização defensiva.

## Pendências

- Validação visual final no navegador.

## Definition of Ready

- RF e Design documentados.
- Plano aprovado no pacote Harness.

## Definition of Done

- Código implementado.
- Revisão sintática feita.
- Task marcada concluída somente após verificação.

## Rastreabilidade

- REQ: `REQ-0001`
- RF: `RF-0001-01`

## Impacto em outros artefatos

- Base para tasks RF-0001-02, RF-0001-03 e RF-0001-04.

## Histórico

- 2026-07-16: Task criada para Auto Layout.

## Checklist de qualidade

- [x] Objetivo registrado.
- [x] Escopo definido.
- [x] Critérios de aceite definidos.

# TASK-RF-0001-02-001 — Implementar motor Flex Layout para frames no Konva

## Identificação da task

- ID: `TASK-RF-0001-02-001`
- RF: `RF-0001-02`
- Tipo: implementação frontend
- Status inicial: aberta

## Objetivo

Implementar motor Flex Layout próprio para calcular posições e dimensões de filhos de frames no canvas Konva.

## Contexto

Konva não executa CSS Flexbox. A engine deve calcular coordenadas no modelo local e sincronizar nós Konva.

## História técnica

Como usuário, preciso que filhos de um frame mudem de posição automaticamente quando altero direção, gap, padding, wrap, alinhamento ou sizing.

## Escopo

- Calcular direção row/row-reverse/column/column-reverse.
- Aplicar wrap.
- Aplicar justify, align e alignContent.
- Aplicar rowGap/columnGap.
- Aplicar padding por lado.
- Aplicar sizing fixed/hug.
- Ignorar filhos absolutos.
- Suportar layout aninhado por ordem de profundidade.

## Fora do escopo

- CSS Grid.
- Margens negativas.
- Medição avançada de texto com auto-resize.

## Entradas

- `RF-0001-02`
- `state.doc.nodes`
- `contentLayer`

## Saídas

- Funções de cálculo e aplicação de layout em `konva-designer.js`.

## Atividades

1. Criar medição de itens.
2. Criar agrupamento em linhas/colunas.
3. Criar distribuição no eixo principal.
4. Criar alinhamento transversal.
5. Criar cálculo de hug.
6. Sincronizar dados e nós Konva.

## Regras relacionadas

- O modelo local é fonte oficial.
- Layout deve ser determinístico.
- Filhos absolutos não entram no fluxo.

## Requisitos técnicos

- Evitar recalcular documentos inteiros quando possível.
- Redesenhar camadas afetadas.
- Proteger contra loops em layouts aninhados.

## Arquivos / Componentes Impactados

- `[MODIFICAR] gitide_server/static/konva-designer.js`

## Dados envolvidos

- `layout.direction`
- `layout.wrap`
- `layout.alignItems`
- `layout.justifyContent`
- `layout.alignContent`
- `layout.rowGap`
- `layout.columnGap`
- `layout.padding*`
- `layout.widthMode`
- `layout.heightMode`

## APIs/serviços/integrações

- Nenhuma API nova.

## Validações

- Revisão de fechamento de funções, arrays, objetos e strings.
- Validação visual em canvas quando disponível.

## Comportamento esperado

Frames com Auto Layout reorganizam filhos automaticamente conforme controles.

## Critérios de aceite

- Direções e reversos funcionam.
- Wrap funciona.
- Align/justify alteram resultado visual.
- Gaps e padding são aplicados.
- Hug ajusta largura/altura.

## Plano de testes

- Criar frame com múltiplos filhos.
- Ativar layout.
- Alternar direções.
- Alterar gap/padding.
- Ativar wrap.
- Alternar hug/fixed.

## Evidências

- Implementação aplicada nos arquivos aprovados.
- Revisão técnica por leitura executada nos trechos alterados em `gitide_server/static/konva-designer.js`, `gitide_server/static/konva-designer.html` e `gitide_server/static/rebrand.css`.
- Validação sintática executável solicitada com `node --check gitide_server/static/konva-designer.js`, mas o runtime local retornou `/bin/sh: 1: node: not found`.
- Conforme regra de validação em VM, a ausência de Node local não foi tratada como falha do código.
- Validação alternativa realizada por leitura técnica: fechamento de funções, objetos, arrays, templates, handlers, integração com inspector, persistência e ausência de erro sintático evidente.
- Task marcada como concluída após validação técnica alternativa documentada.

## Dependências

- TASK-RF-0001-01-001.

## Riscos

- Diferenças sutis em relação ao CSS Flexbox real.

## Pendências

- Validação visual final.

## Definition of Ready

- Modelo de layout definido.

## Definition of Done

- Engine implementada e revisada.

## Rastreabilidade

- REQ: `REQ-0001`
- RF: `RF-0001-02`

## Impacto em outros artefatos

- Habilita controles da aba Design.

## Histórico

- 2026-07-16: Task criada para Auto Layout.

## Checklist de qualidade

- [x] Escopo funcional definido.
- [x] Critérios de aceite definidos.

# TASK-RF-0001-03-001 — Criar controles de Auto Layout no inspector da aba Design

## Identificação da task

- ID: `TASK-RF-0001-03-001`
- RF: `RF-0001-03`
- Tipo: implementação frontend
- Status inicial: aberta

## Objetivo

Adicionar seção de Auto Layout ao inspector da aba Design com controles para frames e filhos.

## Contexto

A interface atual possui inspector com campos de posição, tamanho, fill, stroke, texto e ações. A seção Auto Layout deve ser adicionada sem remover controles existentes.

## História técnica

Como usuário, quero configurar Auto Layout pelo painel direito sem editar JSON manualmente.

## Escopo

- Inserir markup sem inline styles.
- Criar renderização de estado da seção.
- Criar eventos para inputs, selects e botões.
- Estilizar controles no `rebrand.css`.

## Fora do escopo

- Tooltips ricos.
- Drag de gap diretamente no canvas.

## Entradas

- `RF-0001-03`
- `DRI RI-0001`

## Saídas

- HTML com seção Auto Layout.
- JS com renderização/handlers.
- CSS escopado.

## Atividades

1. Atualizar `konva-designer.html`.
2. Adicionar renderização dinâmica dos controles.
3. Adicionar handlers `data-layout-*`.
4. Atualizar CSS.
5. Atualizar ícones.

## Regras relacionadas

- Não usar inline styles.
- Manter identidade dark/premium/glass.

## Requisitos técnicos

- Inputs numéricos com `min=0`.
- Buttons com `type=button`.
- Estados ativos claros.

## Arquivos / Componentes Impactados

- `[MODIFICAR] gitide_server/static/konva-designer.html`
- `[MODIFICAR] gitide_server/static/konva-designer.js`
- `[MODIFICAR] gitide_server/static/rebrand.css`

## Dados envolvidos

- Seleção atual.
- `layout`.
- `layoutItem`.

## APIs/serviços/integrações

- Nenhuma API nova.

## Validações

- Revisão de HTML e CSS.
- Verificar ausência de inline styles novos.

## Comportamento esperado

A seção aparece no inspector e atualiza o canvas em tempo real.

## Critérios de aceite

- Frame sem layout mostra CTA.
- Frame com layout mostra controles completos.
- Filho em Auto Layout mostra toggle estático/absoluto.
- Estilos seguem o tema.

## Plano de testes

- Selecionar frame.
- Ativar layout.
- Alterar controles.
- Selecionar filho.
- Alternar posição estática/absoluta.

## Evidências

- Implementação aplicada nos arquivos aprovados.
- Revisão técnica por leitura executada nos trechos alterados em `gitide_server/static/konva-designer.js`, `gitide_server/static/konva-designer.html` e `gitide_server/static/rebrand.css`.
- Validação sintática executável solicitada com `node --check gitide_server/static/konva-designer.js`, mas o runtime local retornou `/bin/sh: 1: node: not found`.
- Conforme regra de validação em VM, a ausência de Node local não foi tratada como falha do código.
- Validação alternativa realizada por leitura técnica: fechamento de funções, objetos, arrays, templates, handlers, integração com inspector, persistência e ausência de erro sintático evidente.
- Task marcada como concluída após validação técnica alternativa documentada.

## Dependências

- TASK-RF-0001-01-001.
- TASK-RF-0001-02-001.

## Riscos

- Painel direito estreito exige UI compacta.

## Pendências

- Validação visual final.

## Definition of Ready

- DRI documentado.

## Definition of Done

- UI implementada e revisada.

## Rastreabilidade

- REQ: `REQ-0001`
- RF: `RF-0001-03`
- RI: `RI-0001`

## Impacto em outros artefatos

- Atualiza Design Canvas.

## Histórico

- 2026-07-16: Task criada para Auto Layout.

## Checklist de qualidade

- [x] Interface definida.
- [x] Arquivos impactados definidos.

# TASK-RF-0001-04-001 — Implementar persistência, undo/redo e validação da feature Auto Layout

## Identificação da task

- ID: `TASK-RF-0001-04-001`
- RF: `RF-0001-04`
- Tipo: implementação frontend e QA
- Status inicial: aberta

## Objetivo

Garantir persistência local, undo/redo por snapshot e validação técnica da feature Auto Layout.

## Contexto

O canvas já salva em localStorage, mas não possui histórico formal. A feature precisa registrar snapshots locais para operações de layout.

## História técnica

Como usuário, preciso salvar, recarregar, desfazer e refazer alterações de Auto Layout com segurança.

## Escopo

- Implementar histórico undo/redo local.
- Integrar snapshots com operações de layout e edição do inspector.
- Persistir `layout` e `layoutItem`.
- Validar sintaxe e estrutura dos arquivos alterados.
- Marcar tasks concluídas após verificação.

## Fora do escopo

- Histórico colaborativo.
- Persistência remota.
- Auditoria backend.

## Entradas

- `RF-0001-04`
- `state.doc`

## Saídas

- Undo/redo básico no Design Canvas.
- Persistência local compatível.
- Evidências de validação.

## Atividades

1. Criar `pushHistory`, `undoHistory` e `redoHistory`.
2. Integrar atalhos de teclado.
3. Integrar persistência com recalculo.
4. Executar validação técnica possível.
5. Atualizar Task List após validação.

## Regras relacionadas

- Não considerar ausência de runtime local como falha de código.
- Revisar sintaxe antes de concluir.

## Requisitos técnicos

- Snapshot limitado em memória.
- Restauração deve redesenhar canvas, inspector e JSON preview.

## Arquivos / Componentes Impactados

- `[MODIFICAR] gitide_server/static/konva-designer.js`
- `[MODIFICAR] .documents/task/task.md`
- `[MODIFICAR] .documents/task/task.details.md`
- `[MODIFICAR] .documents/estimativa/estimativas.json`
- `[MODIFICAR] .documents/estimativa.json`
- `[MODIFICAR] .documents/estimativa.md`

## Dados envolvidos

- `state.history.undo`
- `state.history.redo`
- `state.doc`

## APIs/serviços/integrações

- Nenhuma API nova.

## Validações

- `node --check gitide_server/static/konva-designer.js`, se disponível/aprovado.
- Revisão técnica por leitura se runtime não estiver disponível.
- Conferência dos artefatos Harness.

## Comportamento esperado

Auto Layout persiste após reload e undo/redo restaura estados do documento.

## Critérios de aceite

- Salvar/recarregar preserva Auto Layout.
- Undo desfaz alteração de layout.
- Redo reaplica alteração.
- Task só é marcada concluída após verificação.

## Plano de testes

- Ativar Auto Layout.
- Alterar direção/gap/padding.
- Usar undo/redo.
- Exportar JSON.
- Recarregar a tela.

## Evidências

- Implementação aplicada nos arquivos aprovados.
- Revisão técnica por leitura executada nos trechos alterados em `gitide_server/static/konva-designer.js`, `gitide_server/static/konva-designer.html` e `gitide_server/static/rebrand.css`.
- Validação sintática executável solicitada com `node --check gitide_server/static/konva-designer.js`, mas o runtime local retornou `/bin/sh: 1: node: not found`.
- Conforme regra de validação em VM, a ausência de Node local não foi tratada como falha do código.
- Validação alternativa realizada por leitura técnica: fechamento de funções, objetos, arrays, templates, handlers, integração com inspector, persistência e ausência de erro sintático evidente.
- Task marcada como concluída após validação técnica alternativa documentada.

## Dependências

- TASK-RF-0001-01-001.
- TASK-RF-0001-02-001.
- TASK-RF-0001-03-001.

## Riscos

- Snapshot completo pode crescer em documentos grandes.

## Pendências

- Validação visual final pelo usuário.

## Definition of Ready

- Tasks anteriores concluídas.

## Definition of Done

- Histórico implementado.
- Validação registrada.
- Tasks concluídas em `task.md`.

## Rastreabilidade

- REQ: `REQ-0001`
- RF: `RF-0001-04`

## Impacto em outros artefatos

- Fecha o pacote Auto Layout.

## Histórico

- 2026-07-16: Task criada para Auto Layout.

## Checklist de qualidade

- [x] Persistência definida.
- [x] Validação prevista.

# TASK-QA-QA-C118E4B1-001 — Garantir exibição da seção Auto Layout ao selecionar frame no Design Canvas

## Identificação da task

- ID: `TASK-QA-QA-C118E4B1-001`
- Origem: QA aberto `QA-C118E4B1`
- Tipo: correção funcional de frontend
- Status inicial: aberta

## QA de origem

- Título: Auto layout
- URL/tela afetada: `http://127.0.0.1:8000/design-canvas`
- Categoria: `functional`
- Severidade: `medium`
- Status da anotação: `open`
- Seletor alvo: `html > body.konva-designer-page > main.konva-designer-shell > aside.konva-designer-right:nth-of-type(2)`
- Evidência textual capturada: painel direito mostra `DESIGN`, `PROTÓTIPO`, `INSPECIONAR`, campos de `FRAME`, `X`, `Y`, `W`, `H`, `FILL`, `STROKE`, `RADIUS`, `OPACITY`, `TEXTO`, `FONT SIZE`, `WEIGHT`, `DUPLICAR`, `EXCLUIR`, mas não mostra `Auto Layout`.
- Screenshot associado: `QA-C118E4B1.jpg`.

## Problema observado

Após implementação da feature, o usuário selecionou um frame no Design Canvas e a seção Auto Layout não apareceu no inspector da aba Design. O HTML contém o container `#konva-auto-layout-panel`, mas o painel pode permanecer vazio/oculto caso a renderização não rode no ciclo esperado ou o navegador ainda esteja carregando um bundle antigo.

## Comportamento esperado

Ao selecionar qualquer frame no Design Canvas, a aba Design deve exibir uma seção visível `Auto Layout`. Para frame sem layout ativo, deve aparecer um CTA `Ativar`. Para frame com layout ativo, devem aparecer os controles completos.

## Escopo

- Garantir fallback visível no HTML para a seção Auto Layout.
- Reforçar a renderização defensiva do inspector quando um frame está selecionado.
- Aplicar cache busting em CSS/JS da rota `/design-canvas`.
- Manter a implementação funcional já existente de Auto Layout sem reescrever a engine.

## Fora do escopo

- Reimplementar o motor Flex Layout.
- Alterar backend.
- Alterar contratos de persistência.
- Implementar Grid Layout.

## Entradas

- `.documents/qa/annotations.json`
- `gitide_server/static/konva-designer.html`
- `gitide_server/static/konva-designer.js`

## Saídas esperadas

- Seção Auto Layout aparece no painel direito quando o inspector está visível.
- Frame selecionado exibe CTA de ativação quando `layout.enabled` não está ativo.
- Cache busting força o navegador a buscar novo JS/CSS.

## Atividades executáveis

1. Adicionar conteúdo fallback dentro de `#konva-auto-layout-panel`.
2. Atualizar versão dos assets no HTML.
3. Tornar `renderInspector()` mais defensivo para não abortar antes de renderizar Auto Layout.
4. Revisar sintaxe dos trechos alterados.
5. Marcar a task como concluída somente após verificação técnica.

## Requisitos técnicos

- Não usar estilos inline novos.
- Preservar o padrão visual existente.
- Não alterar engine de layout fora do necessário.
- Evitar regressão no inspector existente.

## Arquivos / Componentes Impactados

- `[MODIFICAR] gitide_server/static/konva-designer.html`
- `[MODIFICAR] gitide_server/static/konva-designer.js`
- `[MODIFICAR] .documents/task/task.md`
- `[MODIFICAR] .documents/task/task.details.md`
- `[MODIFICAR] .documents/estimativa/estimativas.json`
- `[MODIFICAR] .documents/estimativa.json`
- `[MODIFICAR] .documents/estimativa.md`

## Validações previstas

- Revisão técnica por leitura dos trechos alterados.
- `node --check gitide_server/static/konva-designer.js`, se Node estiver disponível.
- Se Node não estiver disponível, validação alternativa por leitura conforme regra de VM.
- Validação visual final pelo usuário com `Ctrl + F5` em `/design-canvas`.

## Critérios de aceite

- A seção `Auto Layout` aparece ao selecionar um frame.
- O CTA `Ativar` aparece para frame sem Auto Layout ativo.
- A seção não depende de conteúdo vazio que possa ficar escondido por CSS.
- O navegador recebe nova versão de asset por cache busting.

## Evidências

- `gitide_server/static/konva-designer.html` atualizado com fallback visível dentro de `#konva-auto-layout-panel`.
- Cache busting aplicado para `/static/rebrand.css?v=83` e `/static/konva-designer.js?v=3`.
- `gitide_server/static/konva-designer.js` atualizado com `getInspectorData(node)` e renderização defensiva do inspector antes de `renderAutoLayoutPanel(data)`.
- Revisão técnica por leitura realizada nos trechos alterados de HTML e JS.
- `node --check` não foi repetido porque o ambiente local já retornou `/bin/sh: 1: node: not found`; aplicada validação alternativa por leitura conforme regra de VM.
- Task marcada como concluída após validação técnica alternativa.


## Histórico

- 2026-07-16: Task criada a partir do QA aberto `QA-C118E4B1`.

## Checklist de qualidade

- [x] QA de origem registrado.
- [x] Evidência textual registrada.
- [x] Escopo delimitado.
- [x] Critérios de aceite definidos.

# TASK-RF-0002-01-001 — Implementar estado de viewport e conversões Screen/World

## Identificação da task

- ID: `TASK-RF-0002-01-001`
- RF: `RF-0002-01`
- Tipo: implementação frontend
- Status final: concluída

## Objetivo

Adicionar estado central de viewport e funções de conversão entre Screen Space e World Space no Design Canvas.

## Escopo executado

- Criado `VIEWPORT_STORAGE_KEY`.
- Adicionado `state.viewport` com `x`, `y`, `scale`, `minScale`, `maxScale`, estados de pan/zoom e touch.
- Criadas funções `normalizeViewport`, `screenToWorld`, `worldToScreen`, `getViewportCenterScreen`, `getPointerScreenPosition` e `getPointer` em World Space.
- Stage inicializado pelo tamanho visível do container.
- Criação de nós passou a usar coordenada global calculada pelo viewport.

## Arquivos impactados

- `gitide_server/static/konva-designer.js`
- `.documents/design/design.md`
- `.documents/task/task.md`
- `.documents/task/task.details.md`

## Evidências

- Revisão técnica por leitura nos trechos de inicialização do stage e helpers de viewport.
- Verificado que pan/zoom não alteram `state.doc.nodes` diretamente.
- Verificado que `getPointer()` converte ponto de tela para World Space.

## Validação

- Validação por leitura técnica, conforme orientação de VM sem depender de Node local.
- Não foi identificado erro evidente de sintaxe em funções, objetos, strings ou chaves dos trechos alterados.

## Critérios de aceite

- [x] Estado de viewport existe e é normalizado.
- [x] Conversões Screen/World foram implementadas.
- [x] Objetos continuam em World Space.

# TASK-RF-0002-02-001 — Implementar zoom relativo ao cursor, botões e atalhos de zoom

## Identificação da task

- ID: `TASK-RF-0002-02-001`
- RF: `RF-0002-02`
- Tipo: implementação frontend
- Status final: concluída

## Objetivo

Implementar zoom relativo ao cursor, limites, botões, atalhos e ações de recuperação visual.

## Escopo executado

- Criadas funções `zoomAtScreenPoint`, `zoomByFactor`, `resetZoom`, `fitAllObjects`, `fitSelection`, `centerContent` e `focusBounds`.
- Implementado `Ctrl/Cmd + Wheel` para zoom no ponto do cursor.
- Implementados botões `+`, `-`, `100%`, ajustar todos, ajustar seleção e centralizar.
- Implementados atalhos `+`, `-`, `0`, `1` e `2`.
- Indicadores `#konva-zoom-label` e `#konva-right-zoom` atualizam pelo viewport real.

## Arquivos impactados

- `gitide_server/static/konva-designer.html`
- `gitide_server/static/konva-designer.js`
- `gitide_server/static/rebrand.css`

## Evidências

- HTML revisado com novos controles da toolbar.
- JS revisado com cálculo focal de zoom e limites `0.05` a `64`.
- CSS revisado para botão textual `100%` e estados de botão.

## Validação

- Validação por leitura técnica de handlers, atalhos e fechamento dos templates/strings.
- Não foi executado `node --check` porque a instrução do projeto orienta validação por leitura em VM quando runtime local não existe.

## Critérios de aceite

- [x] Zoom relativo ao cursor implementado.
- [x] Botões e atalhos implementados.
- [x] Indicador de zoom atualizado.
- [x] Limites mínimo/máximo respeitados pela função de clamp.

# TASK-RF-0002-03-001 — Implementar pan por wheel, trackpad, botão central, Hand e Space Drag

## Identificação da task

- ID: `TASK-RF-0002-03-001`
- RF: `RF-0002-03`
- Tipo: implementação frontend
- Status final: concluída

## Objetivo

Adicionar pan do viewport por wheel, trackpad, botão central, Hand Tool e `Space + Drag` sem mover objetos.

## Escopo executado

- Criadas funções `startViewportPan`, `moveViewportPan`, `endViewportPan`, `panBy` e `handleViewportWheel`.
- Implementado wheel vertical e Shift+Wheel horizontal.
- Implementado pan por `deltaX/deltaY` para trackpad.
- Implementado botão central + drag.
- Implementada ferramenta Hand com cursor `grab/grabbing`.
- Implementado `Space + Drag` temporário.
- Adicionado estado `panJustEnded` para evitar que o clique final do pan limpe a seleção.
- Corrigido conflito em `wireNode` para impedir que a ferramenta `hand` tente criar objeto.

## Arquivos impactados

- `gitide_server/static/konva-designer.html`
- `gitide_server/static/konva-designer.js`
- `gitide_server/static/rebrand.css`

## Evidências

- Revisado `wireNode` para bloquear drag de objeto durante Hand/Space/pan.
- Revisado handler do stage para preservar seleção após pan.
- Verificado que pan não chama `pushHistory()`.

## Validação

- Validação por leitura técnica de fluxo de pointer/wheel/keyboard.
- Não foi identificado erro evidente de sintaxe nos handlers adicionados.

## Critérios de aceite

- [x] Wheel e Shift+Wheel ligados ao viewport.
- [x] Botão central + drag ligado ao viewport.
- [x] Hand Tool e Space+Drag implementados.
- [x] Seleção preservada durante pan.

# TASK-RF-0002-04-001 — Implementar stage responsivo, touch/pinch e grid dinâmico

## Identificação da task

- ID: `TASK-RF-0002-04-001`
- RF: `RF-0002-04`
- Tipo: implementação frontend
- Status final: concluída

## Objetivo

Tornar o stage responsivo, adicionar suporte touch/pinch e substituir o grid fixo por grid dinâmico em World Space.

## Escopo executado

- Criada função `resizeStageToContainer`.
- Stage agora usa tamanho visível de `.konva-stage-scroll`.
- CSS de `#konva-stage` passou para `width: 100%` e `height: 100%`.
- `.konva-stage-scroll` passou a usar `overflow: hidden` e `touch-action: none`.
- `drawGrid()` reescrito para bounds visíveis em World Space.
- Criados helpers `getVisibleWorldBounds`, `getGridStep`, `getTouchPoint`, `touchDistance`, `touchMidpoint`, `handleTouchStart`, `handleTouchMove` e `handleTouchEnd`.

## Arquivos impactados

- `gitide_server/static/konva-designer.js`
- `gitide_server/static/rebrand.css`

## Evidências

- Revisado cálculo do grid dinâmico por bounds visíveis.
- Revisado resize do stage e preservação do viewport.
- Revisados handlers touch/pinch por leitura técnica.

## Validação

- Validação por leitura técnica.
- Touch/pinch ainda requer validação visual em dispositivo ou emulador compatível.

## Critérios de aceite

- [x] Stage responsivo implementado.
- [x] Grid dinâmico em World Space implementado.
- [x] Touch pan e pinch-to-zoom implementados em handlers.

# TASK-RF-0002-05-001 — Persistir viewport por página e validar performance/acessibilidade

## Identificação da task

- ID: `TASK-RF-0002-05-001`
- RF: `RF-0002-05`
- Tipo: implementação frontend e QA
- Status final: concluída

## Objetivo

Persistir viewport por página, manter pan/zoom fora do export JSON e do undo/redo, e validar a entrega por leitura técnica.

## Escopo executado

- Criadas funções `getViewportStorage`, `persistViewport` e `loadViewportForPage`.
- Viewport persistido por `pageId` em `localStorage` separado do documento.
- `navigatePage` e `startRenamePage` restauram viewport da página ativa.
- Atalhos ignoram campos editáveis via `isEditableTarget`.
- Casos de teste oficiais atualizados de `TC-059` a `TC-082`.
- Cache busting atualizado para `rebrand.css?v=86` e `konva-designer.js?v=7`.

## Arquivos impactados

- `gitide_server/static/konva-designer.html`
- `gitide_server/static/konva-designer.js`
- `gitide_server/static/rebrand.css`
- `.documents/casos/test_cases.json`
- `.documents/casos/test_cases.md`
- `.documents/task/task.md`
- `.documents/task/task.details.md`
- `.documents/estimativa/estimativas.json`
- `.documents/estimativa.json`
- `.documents/estimativa.md`

## Evidências

- Revisão técnica por leitura dos arquivos HTML, JS e CSS alterados.
- Revisão de fechamento do JSON oficial de casos de teste até `TC-082`.
- Confirmado que viewport usa `localStorage` separado e não entra em `exportJson()`.
- Confirmado que pan/zoom não chamam `pushHistory()`.

## Validação

- Validação por leitura técnica em ambiente de VM.
- Verificados trechos de inicialização, conversão de coordenadas, pan, zoom, touch, grid, persistência, toolbar e cache busting.
- Não foi identificado erro evidente de sintaxe em chaves, parênteses, strings ou templates dos trechos alterados.

## Critérios de aceite

- [x] Viewport persistido por página.
- [x] Atalhos ignoram campos editáveis.
- [x] Export JSON não inclui viewport local.
- [x] Casos de teste atualizados.
- [x] Validação técnica registrada.
