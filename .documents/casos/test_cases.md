# Casos de Teste

## Suítes — Auto Layout Flexível e Canvas Infinito no Design Canvas

- Projeto: `act-ide-teste`
- ID do projeto: `22`
- Tela principal: `/design-canvas`
- Atualizado em: `2026-07-16T00:00:00Z`

## Fontes REQ/RF analisadas

- `.documents/requirements/REQ-0001-auto-layout-flexivel-aba-design.md`
- `.documents/functional-requirements/RF-0001-01-modelar-ativar-auto-layout-frames.md`
- `.documents/functional-requirements/RF-0001-02-calcular-flex-layout-konva.md`
- `.documents/functional-requirements/RF-0001-03-controles-auto-layout-aba-design.md`
- `.documents/functional-requirements/RF-0001-04-persistir-historico-auto-layout.md`
- `.documents/requirements/REQ-0002-navegacao-zoom-pan-canvas-infinito.md`
- `.documents/functional-requirements/RF-0002-01-modelo-viewport-coordenadas-canvas-infinito.md`
- `.documents/functional-requirements/RF-0002-02-zoom-relativo-cursor-limites.md`
- `.documents/functional-requirements/RF-0002-03-pan-scroll-hand-tool.md`
- `.documents/functional-requirements/RF-0002-04-responsividade-touch-grid-dinamico.md`
- `.documents/functional-requirements/RF-0002-05-persistencia-performance-acessibilidade.md`

## Observação

A raiz direta do workspace não contém arquivos `REQ-*` ou `RF-*`. A suíte foi gerada a partir dos documentos oficiais Harness localizados em `.documents/requirements/` e `.documents/functional-requirements/`.

## Casos de Teste

### TC-001 — Exibir seção Auto Layout ao selecionar frame sem layout ativo

- **Origem:** REQ-0001, RF-0001-01, RF-0001-03
- **Pré-condições:** Aplicação aberta em `/design-canvas`; existe pelo menos um frame sem `layout.enabled=true`.
- **Passos:** 1. Abrir `/design-canvas`; 2. Selecionar um frame; 3. Manter a aba Design ativa; 4. Observar a seção Auto Layout no painel direito.
- **Resultado esperado:** A seção Auto Layout aparece visível e exibe ação para ativar o layout do frame selecionado.

### TC-002 — Ativar Auto Layout em frame selecionado

- **Origem:** REQ-0001, RF-0001-01
- **Pré-condições:** Frame selecionado sem Auto Layout ativo; CTA Ativar visível.
- **Passos:** 1. Clicar em Ativar; 2. Observar o painel direito; 3. Observar os filhos no canvas; 4. Inspecionar o JSON quando disponível.
- **Resultado esperado:** O frame recebe `layout.enabled=true`, filhos são normalizados com `layoutItem` e o canvas recalcula a posição dos filhos.

### TC-003 — Criar defaults seguros ao ativar Auto Layout

- **Origem:** REQ-0001, RF-0001-01
- **Pré-condições:** Frame selecionado sem propriedade `layout`.
- **Passos:** 1. Ativar Auto Layout; 2. Verificar valores iniciais nos controles; 3. Conferir JSON exportado ou estado serializado.
- **Resultado esperado:** O layout criado contém `enabled=true`, `direction=row`, `wrap=false`, `alignItems=start`, `justifyContent=start`, `alignContent=start`, gaps e paddings não negativos, `widthMode=fixed` e `heightMode=fixed`.

### TC-004 — Remover Auto Layout preservando aparência visual

- **Origem:** REQ-0001, RF-0001-01
- **Pré-condições:** Frame com Auto Layout ativo e filhos visíveis organizados.
- **Passos:** 1. Selecionar o frame; 2. Anotar visualmente as posições dos filhos; 3. Clicar em Remover; 4. Observar as posições dos filhos.
- **Resultado esperado:** O Auto Layout é desativado ou removido e as posições visuais atuais dos filhos permanecem preservadas.

### TC-005 — Impedir ativação de Auto Layout em elemento não-frame

- **Origem:** REQ-0001, RF-0001-01, RF-0001-03
- **Pré-condições:** Existe pelo menos um elemento não-frame no canvas.
- **Passos:** 1. Selecionar um elemento não-frame; 2. Observar a seção Auto Layout; 3. Procurar ação de ativação de layout de container.
- **Resultado esperado:** O sistema não permite ativar Auto Layout de container em elemento não-frame e exibe mensagem informativa ou controles de item quando aplicável.

### TC-006 — Estado sem seleção não deve mostrar controles editáveis de Auto Layout

- **Origem:** RF-0001-01, RF-0001-03
- **Pré-condições:** Tela `/design-canvas` aberta.
- **Passos:** 1. Clicar em área vazia do canvas para limpar seleção; 2. Observar o painel direito.
- **Resultado esperado:** O inspector fica vazio ou informativo, sem controles editáveis de Auto Layout.

### TC-007 — Ativar Auto Layout em frame raiz

- **Origem:** RF-0001-01
- **Pré-condições:** Existe um frame raiz na página.
- **Passos:** 1. Selecionar o frame raiz; 2. Ativar Auto Layout; 3. Verificar organização dos filhos; 4. Verificar hierarquia do frame.
- **Resultado esperado:** O Auto Layout é ativado no frame raiz, os filhos são organizados e o frame mantém sua posição hierárquica de raiz.

### TC-008 — Ativar Auto Layout em frame filho

- **Origem:** REQ-0001, RF-0001-01
- **Pré-condições:** Existe um frame dentro de outro frame.
- **Passos:** 1. Selecionar o frame filho; 2. Ativar Auto Layout; 3. Alterar gap ou direção; 4. Observar o frame filho e o frame pai.
- **Resultado esperado:** O frame filho organiza seus próprios filhos sem perder `parentId` e sem quebrar o frame pai.

### TC-009 — Normalizar documento antigo sem propriedades de layout

- **Origem:** RF-0001-01, RF-0001-04
- **Pré-condições:** Documento salvo anteriormente não contém `layout` ou `layoutItem` nos nós.
- **Passos:** 1. Abrir `/design-canvas` com documento antigo; 2. Selecionar frames e elementos existentes; 3. Ativar Auto Layout em um frame antigo.
- **Resultado esperado:** O documento antigo carrega sem erro e a ativação cria propriedades ausentes de forma defensiva.

### TC-010 — Normalizar valores numéricos negativos para zero

- **Origem:** REQ-0001, RF-0001-01, RF-0001-03
- **Pré-condições:** Frame com Auto Layout ativo; controles de gap e padding disponíveis.
- **Passos:** 1. Tentar informar valor negativo em `rowGap`; 2. Tentar informar valor negativo em `columnGap`; 3. Tentar informar valor negativo nos paddings; 4. Observar valores aplicados.
- **Resultado esperado:** Valores negativos são impedidos ou normalizados para zero sem quebrar o cálculo.

### TC-011 — Organizar filhos em direção horizontal row

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e pelo menos três filhos estáticos.
- **Passos:** 1. Definir direção `row`; 2. Aplicar gap visível; 3. Observar a posição dos filhos.
- **Resultado esperado:** Os filhos são organizados da esquerda para a direita, respeitando padding e gap.

### TC-012 — Organizar filhos em direção row-reverse

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e múltiplos filhos estáticos.
- **Passos:** 1. Definir direção `row-reverse`; 2. Observar a ordem visual dos filhos.
- **Resultado esperado:** Os filhos são organizados visualmente da direita para a esquerda.

### TC-013 — Organizar filhos em direção column

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e múltiplos filhos estáticos.
- **Passos:** 1. Definir direção `column`; 2. Observar o posicionamento dos filhos.
- **Resultado esperado:** Os filhos são empilhados de cima para baixo, respeitando padding e `rowGap`.

### TC-014 — Organizar filhos em direção column-reverse

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e múltiplos filhos estáticos.
- **Passos:** 1. Definir direção `column-reverse`; 2. Observar a ordem visual dos filhos.
- **Resultado esperado:** Os filhos são organizados visualmente de baixo para cima.

### TC-015 — Aplicar wrap em layout horizontal

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame estreito em `row`; soma das larguras dos filhos excede o espaço interno.
- **Passos:** 1. Ativar wrap; 2. Observar quebra dos filhos; 3. Alterar a largura do frame para menor e maior.
- **Resultado esperado:** Filhos excedentes quebram para nova linha quando não couberem e retornam quando houver espaço suficiente.

### TC-016 — Aplicar wrap em layout vertical

- **Origem:** RF-0001-02
- **Pré-condições:** Frame baixo em `column`; soma das alturas dos filhos excede o espaço interno.
- **Passos:** 1. Definir `direction=column`; 2. Ativar wrap; 3. Observar distribuição em colunas adicionais.
- **Resultado esperado:** Filhos excedentes quebram para nova coluna quando não couberem verticalmente.

### TC-017 — Aplicar justifyContent start

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com espaço interno maior que a soma dos filhos.
- **Passos:** 1. Definir `justifyContent=start`; 2. Observar o início do eixo principal.
- **Resultado esperado:** O grupo de filhos fica alinhado ao início do eixo principal, após o padding inicial.

### TC-018 — Aplicar justifyContent center

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com Auto Layout e espaço livre no eixo principal.
- **Passos:** 1. Definir `justifyContent=center`; 2. Observar o espaço antes e depois do grupo de filhos.
- **Resultado esperado:** O grupo de filhos fica centralizado no eixo principal.

### TC-019 — Aplicar justifyContent end

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com Auto Layout e espaço livre no eixo principal.
- **Passos:** 1. Definir `justifyContent=end`; 2. Observar o grupo de filhos.
- **Resultado esperado:** O grupo de filhos fica alinhado ao final do eixo principal, antes do padding final.

### TC-020 — Aplicar justifyContent space-between

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com pelo menos três filhos e espaço livre no eixo principal.
- **Passos:** 1. Definir `justifyContent=space-between`; 2. Comparar espaços entre filhos e bordas internas.
- **Resultado esperado:** Primeiro e último filhos ficam próximos aos limites internos, e o espaço extra é distribuído entre os filhos.

### TC-021 — Aplicar justifyContent space-around

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com pelo menos três filhos.
- **Passos:** 1. Definir `justifyContent=space-around`; 2. Observar espaços antes, entre e depois dos filhos.
- **Resultado esperado:** Cada filho recebe espaço ao redor, com comportamento visual compatível com `space-around`.

### TC-022 — Aplicar justifyContent space-evenly

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com pelo menos três filhos.
- **Passos:** 1. Definir `justifyContent=space-evenly`; 2. Observar a distribuição dos espaços.
- **Resultado esperado:** Os espaços antes, entre e depois dos filhos são distribuídos de maneira uniforme.

### TC-023 — Aplicar alignItems start

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com filhos de tamanhos diferentes e Auto Layout ativo.
- **Passos:** 1. Definir `alignItems=start`; 2. Observar o eixo transversal.
- **Resultado esperado:** Os filhos ficam alinhados ao início do eixo transversal.

### TC-024 — Aplicar alignItems center

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com filhos de tamanhos diferentes e espaço transversal livre.
- **Passos:** 1. Definir `alignItems=center`; 2. Observar o eixo transversal.
- **Resultado esperado:** Os filhos ficam centralizados no eixo transversal da linha ou coluna.

### TC-025 — Aplicar alignItems end

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com filhos de tamanhos diferentes e Auto Layout ativo.
- **Passos:** 1. Definir `alignItems=end`; 2. Observar o eixo transversal.
- **Resultado esperado:** Os filhos ficam alinhados ao final do eixo transversal.

### TC-026 — Aplicar alignContent com múltiplas linhas

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com `wrap=true`, múltiplas linhas ou colunas e espaço transversal livre.
- **Passos:** 1. Definir `alignContent=start`; 2. Alterar para `center` e `end`; 3. Alterar para `space-between`, `space-around` e `space-evenly`.
- **Resultado esperado:** O conjunto de linhas ou colunas muda de posição ou distribuição no eixo transversal conforme o valor selecionado.

### TC-027 — Aplicar rowGap e columnGap

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo, múltiplos filhos e, preferencialmente, wrap ativo.
- **Passos:** 1. Alterar `rowGap`; 2. Observar espaçamento entre linhas; 3. Alterar `columnGap`; 4. Observar espaçamento entre colunas ou itens horizontais.
- **Resultado esperado:** `rowGap` e `columnGap` alteram os espaçamentos correspondentes conforme direção e wrap.

### TC-028 — Aplicar padding por lado

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e filhos visíveis.
- **Passos:** 1. Alterar `paddingTop`; 2. Alterar `paddingRight`; 3. Alterar `paddingBottom`; 4. Alterar `paddingLeft`; 5. Observar deslocamento e limites internos.
- **Resultado esperado:** Cada padding move ou limita o fluxo dos filhos no lado correspondente sem sair do frame.

### TC-029 — Manter largura fixa com widthMode fixed

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo.
- **Passos:** 1. Definir `widthMode=fixed`; 2. Alterar gaps, padding ou quantidade de filhos; 3. Observar largura do frame.
- **Resultado esperado:** A largura do frame permanece a largura definida pelo usuário, salvo alteração manual explícita.

### TC-030 — Ajustar largura com widthMode hug

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e filhos estáticos.
- **Passos:** 1. Definir `widthMode=hug`; 2. Aumentar `columnGap` ou padding horizontal; 3. Adicionar ou remover filho quando possível.
- **Resultado esperado:** A largura do frame se ajusta ao conteúdo, considerando filhos, gaps e padding horizontal.

### TC-031 — Manter altura fixa com heightMode fixed

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo.
- **Passos:** 1. Definir `heightMode=fixed`; 2. Alterar gaps, padding ou quantidade de filhos; 3. Observar altura do frame.
- **Resultado esperado:** A altura do frame permanece fixa, salvo alteração manual explícita.

### TC-032 — Ajustar altura com heightMode hug

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e filhos estáticos.
- **Passos:** 1. Definir `heightMode=hug`; 2. Aumentar `rowGap` ou padding vertical; 3. Adicionar ou remover filho quando possível.
- **Resultado esperado:** A altura do frame se ajusta ao conteúdo, considerando filhos, gaps e padding vertical.

### TC-033 — Excluir filho absoluto do cálculo de fluxo

- **Origem:** REQ-0001, RF-0001-02, RF-0001-03
- **Pré-condições:** Frame com Auto Layout ativo e pelo menos um filho selecionável.
- **Passos:** 1. Selecionar um filho dentro do frame; 2. Alterar participação para Absoluto; 3. Alterar direção, gap ou padding do frame; 4. Observar o filho absoluto.
- **Resultado esperado:** O filho absoluto permanece fora do fluxo automático e não afeta o posicionamento dos filhos estáticos.

### TC-034 — Retornar filho absoluto para fluxo estático

- **Origem:** RF-0001-02, RF-0001-03
- **Pré-condições:** Filho dentro de frame com Auto Layout está marcado como absoluto.
- **Passos:** 1. Selecionar o filho absoluto; 2. Alterar participação para Estático; 3. Observar o frame.
- **Resultado esperado:** O filho volta a participar do fluxo e passa a ser reposicionado pelo motor de layout.

### TC-035 — Recalcular Auto Layout aninhado

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame pai com Auto Layout e frame filho também com Auto Layout, ambos com filhos.
- **Passos:** 1. Alterar layout do frame filho; 2. Observar dimensões ou posições do frame filho; 3. Observar se frame pai recalcula corretamente.
- **Resultado esperado:** O layout do frame filho é calculado antes do ancestral, e o frame pai reflete o resultado sem loop ou quebra visual.

### TC-036 — Atualizar nós Konva após recalcular layout

- **Origem:** REQ-0001, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo.
- **Passos:** 1. Alterar direção ou gap pelo inspector; 2. Observar elementos no canvas; 3. Observar árvore de layers e seleção.
- **Resultado esperado:** Os dados do modelo e os nós Konva são sincronizados sem exigir reload.

### TC-037 — Exibir controles completos para frame com Auto Layout ativo

- **Origem:** RF-0001-03
- **Pré-condições:** Frame selecionado com Auto Layout ativo.
- **Passos:** 1. Selecionar o frame; 2. Observar a seção Auto Layout.
- **Resultado esperado:** A seção exibe controles de direção, wrap, align, justify, alignContent, gaps, padding, widthMode, heightMode e botão remover.

### TC-038 — Exibir CTA de ativação para frame sem Auto Layout

- **Origem:** RF-0001-03
- **Pré-condições:** Frame selecionado sem Auto Layout ativo.
- **Passos:** 1. Selecionar o frame; 2. Observar a seção Auto Layout.
- **Resultado esperado:** A seção exibe CTA de ativação e microcopy explicando a organização automática.

### TC-039 — Exibir toggle estático/absoluto para filho dentro de Auto Layout

- **Origem:** RF-0001-03
- **Pré-condições:** Frame com Auto Layout ativo e filho selecionável.
- **Passos:** 1. Selecionar um filho dentro do frame; 2. Observar a seção Auto Layout.
- **Resultado esperado:** A seção exibe controle de participação no fluxo com opções Estático e Absoluto e não exibe controles de container para o filho.

### TC-040 — Refletir valores atuais do modelo nos controles

- **Origem:** RF-0001-03
- **Pré-condições:** Frame com Auto Layout ativo e valores personalizados salvos.
- **Passos:** 1. Selecionar o frame; 2. Comparar controles do inspector com valores do JSON exportado.
- **Resultado esperado:** Os controles mostram exatamente os valores atuais de `layout` do frame selecionado.

### TC-041 — Atualizar canvas imediatamente ao alterar controles

- **Origem:** RF-0001-03, RF-0001-02
- **Pré-condições:** Frame com Auto Layout ativo e controles visíveis.
- **Passos:** 1. Alterar direção; 2. Alterar gap; 3. Alterar padding; 4. Alterar align ou justify.
- **Resultado esperado:** Cada alteração atualiza imediatamente o modelo e recalcula o canvas.

### TC-042 — Validar estados ativos e acessibilidade básica dos controles

- **Origem:** RF-0001-03
- **Pré-condições:** Seção Auto Layout visível.
- **Passos:** 1. Alterar direção usando botões segmentados; 2. Verificar estado visual ativo; 3. Verificar `type=button`; 4. Verificar `min=0` em campos numéricos.
- **Resultado esperado:** O estado ativo fica claro visualmente, botões não submetem formulários indevidamente e campos numéricos respeitam validação mínima.

### TC-043 — Persistir Auto Layout em localStorage após alteração

- **Origem:** REQ-0001, RF-0001-04
- **Pré-condições:** Frame com Auto Layout ativo.
- **Passos:** 1. Alterar direção, gaps e padding; 2. Aguardar persistência local; 3. Recarregar a página; 4. Selecionar novamente o frame.
- **Resultado esperado:** As configurações de Auto Layout permanecem salvas após reload.

### TC-044 — Exportar JSON incluindo layout e layoutItem

- **Origem:** RF-0001-04
- **Pré-condições:** Documento contém frame com Auto Layout e filhos.
- **Passos:** 1. Abrir painel ou ação de export JSON; 2. Inspecionar o JSON exportado.
- **Resultado esperado:** O JSON contém propriedades `layout` no frame e `layoutItem` nos filhos pertinentes.

### TC-045 — Desfazer ativação de Auto Layout com undo

- **Origem:** RF-0001-04
- **Pré-condições:** Frame sem Auto Layout ativo selecionado.
- **Passos:** 1. Ativar Auto Layout; 2. Pressionar `Ctrl/Cmd+Z`; 3. Observar o frame e a seção Auto Layout.
- **Resultado esperado:** O estado anterior é restaurado, removendo o Auto Layout recém-ativado.

### TC-046 — Desfazer alteração de propriedade de layout

- **Origem:** RF-0001-04
- **Pré-condições:** Frame com Auto Layout ativo.
- **Passos:** 1. Alterar `direction`, gap ou padding; 2. Pressionar `Ctrl/Cmd+Z`; 3. Observar controles e canvas.
- **Resultado esperado:** A propriedade volta ao valor anterior e o canvas é redesenhado de acordo com o snapshot restaurado.

### TC-047 — Refazer alteração de Auto Layout com redo

- **Origem:** RF-0001-04
- **Pré-condições:** Existe uma alteração de Auto Layout desfeita por undo.
- **Passos:** 1. Pressionar `Ctrl/Cmd+Shift+Z` ou `Ctrl/Cmd+Y`; 2. Observar controles e canvas.
- **Resultado esperado:** O estado desfeito é reaplicado, restaurando layout, posições, dimensões e propriedades.

### TC-048 — Undo/redo deve restaurar parentId, posições e dimensões

- **Origem:** RF-0001-04
- **Pré-condições:** Frame com filhos e Auto Layout ativo.
- **Passos:** 1. Alterar layout e mover ou redimensionar elementos quando possível; 2. Usar undo; 3. Usar redo; 4. Inspecionar hierarquia, posições e dimensões.
- **Resultado esperado:** Snapshots restauram `parentId`, `x`, `y`, `width`, `height`, `layout` e `layoutItem` corretamente.

### TC-049 — Documento antigo sem layout permanece válido após reload

- **Origem:** RF-0001-04
- **Pré-condições:** Documento salvo sem propriedades de Auto Layout.
- **Passos:** 1. Carregar documento antigo; 2. Recarregar a tela; 3. Selecionar frames e elementos.
- **Resultado esperado:** O documento antigo permanece utilizável, sem erro de carregamento, renderização ou inspector.

### TC-050 — Não criar backend, API nova ou persistência remota

- **Origem:** REQ-0001, RF-0001-04
- **Pré-condições:** Implementação disponível no workspace.
- **Passos:** 1. Revisar comportamento da feature no navegador; 2. Verificar se alterações persistem localmente; 3. Verificar se não há dependência de endpoint novo para salvar Auto Layout.
- **Resultado esperado:** A feature opera no frontend, persiste localmente e não exige backend novo, banco de dados ou contrato de API novo.

### TC-051 — Garantir ausência de Grid Layout na feature

- **Origem:** REQ-0001, RF-0001-02, RF-0001-03
- **Pré-condições:** Seção Auto Layout disponível.
- **Passos:** 1. Abrir a seção Auto Layout; 2. Procurar controles de Grid Layout, CSS Grid, áreas nomeadas, fracionários ou células.
- **Resultado esperado:** A interface e o comportamento oferecem apenas recursos de Auto Layout/Flex Layout; não há controles ou persistência de Grid Layout.

### TC-052 — Não permitir estilos inline novos na seção Auto Layout

- **Origem:** REQ-0001, RF-0001-03
- **Pré-condições:** Código da seção Auto Layout implementado.
- **Passos:** 1. Inspecionar o HTML relacionado à seção Auto Layout; 2. Inspecionar o CSS em `rebrand.css`.
- **Resultado esperado:** A seção usa classes CSS e regras em stylesheet, sem depender de atributos `style="..."` novos.

### TC-053 — Manter fluxo do canvas sem regressão ao ativar Auto Layout

- **Origem:** REQ-0001, RF-0001-02, RF-0001-03
- **Pré-condições:** Canvas com elementos existentes.
- **Passos:** 1. Criar ou selecionar elementos comuns do canvas; 2. Selecionar frame e ativar Auto Layout; 3. Alternar abas Design, Protótipo e Inspecionar; 4. Selecionar outros elementos.
- **Resultado esperado:** Seleção, árvore de layers, inspector e abas continuam funcionando sem travar ou perder estado.

### TC-054 — Normalizar dimensões mínimas para evitar zero

- **Origem:** RF-0001-02
- **Pré-condições:** Frame com filho de dimensão muito pequena, ausente ou zero por documento antigo.
- **Passos:** 1. Carregar documento com item de largura ou altura ausente/zero; 2. Ativar Auto Layout no frame pai; 3. Observar cálculo e renderização.
- **Resultado esperado:** O motor evita dimensões zero que quebrem cálculo ou renderização e usa valores mínimos seguros.

### TC-055 — Atualizar árvore de layers após mudanças de layout

- **Origem:** RF-0001-02, RF-0001-03
- **Pré-condições:** Árvore de layers visível e frame com Auto Layout ativo.
- **Passos:** 1. Alterar direção ou reordenar filhos quando possível; 2. Observar árvore de layers; 3. Selecionar itens pela árvore após a alteração.
- **Resultado esperado:** A árvore permanece sincronizada com os nós e permite seleção correta após mudanças de layout.

### TC-056 — Validar que frame bloqueado não permite edição indevida

- **Origem:** RF-0001-01
- **Pré-condições:** Existe suporte a frame bloqueado ou estado equivalente no documento.
- **Passos:** 1. Selecionar frame bloqueado; 2. Observar controles de Auto Layout; 3. Tentar alterar propriedades se controles estiverem visíveis.
- **Resultado esperado:** Controles permanecem desabilitados ou a edição é impedida para o frame bloqueado, conforme regra funcional.

### TC-057 — Validar primeira entrega com seleção única

- **Origem:** REQ-0001
- **Pré-condições:** Canvas aberto com múltiplos elementos.
- **Passos:** 1. Tentar selecionar múltiplos elementos se a UI permitir; 2. Procurar ação de criar Auto Layout a partir de seleção múltipla.
- **Resultado esperado:** A feature não exige criação por multi-seleção completa; seleção única de frame continua sendo o fluxo suportado.

### TC-058 — Validar limitação de manipulação direta de gap no canvas

- **Origem:** REQ-0001, RF-0001-03
- **Pré-condições:** Frame com Auto Layout ativo.
- **Passos:** 1. Procurar handles específicos de gap no canvas; 2. Tentar alterar gap diretamente arrastando no canvas; 3. Alterar gap pelo inspector.
- **Resultado esperado:** Manipulação direta de gap no canvas não é exigida; gap deve ser alterável pelo inspector.

## Suíte — Navegação, Zoom e Pan em Canvas Infinito

### TC-059 — Inicializar viewport do Canvas Infinito com escala 100%

- **Origem:** REQ-0002, RF-0002-01
- **Pré-condições:** Documento aberto em `/design-canvas` sem viewport salvo para a página ativa.
- **Passos:** 1. Abrir `/design-canvas`; 2. Observar o indicador de zoom; 3. Inspecionar visualmente o canvas inicial.
- **Resultado esperado:** O viewport inicia com `scale=1`, indicador `100%`, `x/y` normalizados e objetos preservados em World Space.

### TC-060 — Converter Screen Space para World Space após pan e zoom

- **Origem:** RF-0002-01
- **Pré-condições:** Canvas aberto com viewport alterado por pan e zoom.
- **Passos:** 1. Aplicar zoom; 2. Aplicar pan; 3. Criar um novo objeto no ponto visível do cursor; 4. Verificar a posição visual e o JSON.
- **Resultado esperado:** O objeto é criado no ponto visual correto e suas coordenadas persistidas correspondem ao World Space calculado.

### TC-061 — Pan e zoom não alteram coordenadas persistidas dos objetos

- **Origem:** REQ-0002, RF-0002-01
- **Pré-condições:** Existe pelo menos um frame no canvas com coordenadas conhecidas.
- **Passos:** 1. Anotar `x/y` do frame no JSON; 2. Aplicar pan; 3. Aplicar zoom; 4. Conferir novamente `x/y` no JSON.
- **Resultado esperado:** As coordenadas `x/y` do frame permanecem iguais após pan e zoom.

### TC-062 — Aplicar zoom relativo ao cursor com Ctrl ou Command + Wheel

- **Origem:** REQ-0002, RF-0002-02
- **Pré-condições:** Canvas aberto; cursor posicionado sobre um ponto visível do canvas.
- **Passos:** 1. Posicionar cursor sobre um objeto; 2. Usar `Ctrl+Wheel` ou `Command+Wheel`; 3. Observar o ponto sob o cursor.
- **Resultado esperado:** O zoom aproxima ou afasta mantendo o ponto sob o cursor visualmente estável.

### TC-063 — Respeitar limite mínimo de zoom

- **Origem:** RF-0002-02
- **Pré-condições:** Canvas aberto.
- **Passos:** 1. Aplicar zoom out repetidamente; 2. Observar indicador de zoom e canvas.
- **Resultado esperado:** A escala não fica abaixo de 5% e o viewport não apresenta salto visual ao atingir o limite.

### TC-064 — Respeitar limite máximo de zoom

- **Origem:** RF-0002-02
- **Pré-condições:** Canvas aberto.
- **Passos:** 1. Aplicar zoom in repetidamente; 2. Observar indicador de zoom e canvas.
- **Resultado esperado:** A escala não ultrapassa 6400% e o viewport não apresenta salto visual ao atingir o limite.

### TC-065 — Executar atalhos de zoom +, -, 0, 1 e 2 fora de campos editáveis

- **Origem:** RF-0002-02, RF-0002-05
- **Pré-condições:** Canvas aberto com pelo menos um objeto e uma seleção possível.
- **Passos:** 1. Pressionar `+`; 2. Pressionar `-`; 3. Pressionar `0`; 4. Pressionar `1`; 5. Selecionar um objeto e pressionar `2`.
- **Resultado esperado:** `+` aproxima, `-` afasta, `0` restaura 100%, `1` ajusta todos e `2` ajusta a seleção.

### TC-066 — Ignorar atalhos de viewport em campos editáveis

- **Origem:** RF-0002-02, RF-0002-03, RF-0002-05
- **Pré-condições:** Inspector aberto com um input, select ou textarea em foco.
- **Passos:** 1. Focar um campo editável; 2. Pressionar `+`, `-`, `0`, `1`, `2` e `Space`; 3. Observar viewport e campo.
- **Resultado esperado:** Atalhos de viewport não são executados enquanto o foco está em campo editável.

### TC-067 — Mover viewport verticalmente com Wheel sem modificadores

- **Origem:** RF-0002-03
- **Pré-condições:** Canvas aberto com conteúdo visível.
- **Passos:** 1. Usar a roda do mouse sem `Ctrl/Command/Shift`; 2. Observar o deslocamento do canvas.
- **Resultado esperado:** O viewport se desloca verticalmente sem alterar objetos ou seleção.

### TC-068 — Mover viewport horizontalmente com Shift + Wheel

- **Origem:** RF-0002-03
- **Pré-condições:** Canvas aberto com conteúdo visível.
- **Passos:** 1. Pressionar `Shift`; 2. Usar a roda do mouse; 3. Observar o deslocamento do canvas.
- **Resultado esperado:** O viewport se desloca horizontalmente sem alterar objetos ou seleção.

### TC-069 — Mover viewport por trackpad com deltaX e deltaY

- **Origem:** RF-0002-03
- **Pré-condições:** Canvas aberto em dispositivo com trackpad.
- **Passos:** 1. Deslizar dois dedos horizontalmente; 2. Deslizar dois dedos verticalmente; 3. Observar o viewport.
- **Resultado esperado:** O viewport responde aos eixos horizontal e vertical do trackpad sem zoom indevido quando `Ctrl/Command` não estiver ativo.

### TC-070 — Executar pan com botão central do mouse

- **Origem:** REQ-0002, RF-0002-03
- **Pré-condições:** Canvas aberto com seleção opcional existente.
- **Passos:** 1. Pressionar o botão central do mouse sobre o canvas; 2. Arrastar; 3. Soltar o botão.
- **Resultado esperado:** O viewport se move durante o arraste e a seleção anterior permanece preservada.

### TC-071 — Executar pan temporário com Space + Drag

- **Origem:** REQ-0002, RF-0002-03
- **Pré-condições:** Canvas aberto com pelo menos um objeto selecionável.
- **Passos:** 1. Selecionar um objeto; 2. Pressionar `Space`; 3. Arrastar o canvas; 4. Soltar `Space`.
- **Resultado esperado:** O viewport se move, o objeto não é arrastado e a seleção permanece preservada.

### TC-072 — Executar pan fixo com Hand Tool

- **Origem:** RF-0002-03, RF-0002-05
- **Pré-condições:** Canvas aberto.
- **Passos:** 1. Clicar na ferramenta Mão; 2. Arrastar o canvas; 3. Clicar sobre um objeto; 4. Voltar para a ferramenta Selecionar.
- **Resultado esperado:** A ferramenta Mão move o viewport, usa cursor `grab/grabbing`, não cria objetos e não altera seleção.

### TC-073 — Redimensionar stage conforme o container visível

- **Origem:** RF-0002-04
- **Pré-condições:** Canvas aberto em janela redimensionável.
- **Passos:** 1. Alterar o tamanho da janela; 2. Observar a área do stage; 3. Verificar objetos após o resize.
- **Resultado esperado:** O stage acompanha o container visível, preserva viewport e não move objetos persistidos.

### TC-074 — Renderizar grid dinâmico em World Space durante pan e zoom

- **Origem:** RF-0002-04
- **Pré-condições:** Canvas aberto com grid visível.
- **Passos:** 1. Aplicar pan em múltiplas direções; 2. Aplicar zoom in/out; 3. Observar alinhamento do grid.
- **Resultado esperado:** O grid acompanha World Space, mantém alinhamento global e não apresenta saltos perceptíveis.

### TC-075 — Aplicar pinch-to-zoom em dispositivo touch

- **Origem:** RF-0002-04
- **Pré-condições:** Canvas aberto em dispositivo ou emulação com suporte a touch.
- **Passos:** 1. Tocar o canvas com dois dedos; 2. Aproximar ou afastar os dedos; 3. Observar o ponto médio do gesto.
- **Resultado esperado:** O zoom é aplicado pelo ponto médio do gesto e o scroll nativo da página não interfere dentro do canvas.

### TC-076 — Executar pan touch com um dedo no canvas

- **Origem:** RF-0002-04
- **Pré-condições:** Canvas aberto em dispositivo ou emulação com suporte a touch.
- **Passos:** 1. Tocar e arrastar com um dedo sobre o canvas; 2. Observar o deslocamento do viewport.
- **Resultado esperado:** O viewport se move com o gesto de um dedo sem acionar scroll nativo da página dentro do canvas.

### TC-077 — Persistir viewport por página após reload

- **Origem:** REQ-0002, RF-0002-05
- **Pré-condições:** Canvas aberto com página ativa.
- **Passos:** 1. Aplicar pan e zoom; 2. Recarregar a página; 3. Observar o viewport restaurado.
- **Resultado esperado:** O viewport da página ativa é restaurado a partir de `localStorage`.

### TC-078 — Restaurar viewport diferente ao alternar páginas

- **Origem:** RF-0002-05
- **Pré-condições:** Documento com pelo menos duas páginas.
- **Passos:** 1. Aplicar viewport diferente na página 1; 2. Alternar para página 2 e aplicar outro viewport; 3. Retornar para página 1.
- **Resultado esperado:** Cada página restaura seu próprio `x`, `y` e `scale` salvos localmente.

### TC-079 — Não incluir viewport no export JSON do documento

- **Origem:** RF-0002-05
- **Pré-condições:** Canvas com viewport alterado por pan e zoom.
- **Passos:** 1. Aplicar pan e zoom; 2. Exportar JSON; 3. Inspecionar o conteúdo exportado.
- **Resultado esperado:** O JSON exportado contém o documento e nós, mas não transforma o viewport local em conteúdo colaborativo do documento.

### TC-080 — Pan e zoom não criam snapshots de undo/redo de objetos

- **Origem:** RF-0002-05
- **Pré-condições:** Canvas aberto com histórico de edição disponível.
- **Passos:** 1. Aplicar pan e zoom; 2. Pressionar `Ctrl/Cmd+Z`; 3. Observar documento e viewport.
- **Resultado esperado:** Undo não desfaz pan/zoom como edição de objeto; histórico de conteúdo permanece dedicado a alterações do documento.

### TC-081 — Atualizar indicador textual de zoom em tempo real

- **Origem:** RF-0002-02, RF-0002-05
- **Pré-condições:** Canvas aberto.
- **Passos:** 1. Aplicar zoom por botão; 2. Aplicar zoom por wheel; 3. Aplicar reset 100%; 4. Observar os indicadores de zoom.
- **Resultado esperado:** Os indicadores de zoom no topo e no painel direito refletem o percentual real do viewport.

### TC-082 — Preservar seleção, transformer e overlays durante pan e zoom

- **Origem:** REQ-0002, RF-0002-03, RF-0002-04
- **Pré-condições:** Existe um frame selecionado com transformer e metadados visíveis.
- **Passos:** 1. Selecionar um frame; 2. Aplicar pan; 3. Aplicar zoom; 4. Observar seleção, transformer, labels e metadados.
- **Resultado esperado:** Seleção, transformer, labels e overlays permanecem sincronizados visualmente com o objeto selecionado.

## Checklist de cobertura

- [x] Ativação e remoção de Auto Layout.
- [x] Defaults e normalização de `layout` e `layoutItem`.
- [x] Seleção vazia, frame, não-frame e filho.
- [x] Direções `row`, `row-reverse`, `column`, `column-reverse`.
- [x] Wrap horizontal e vertical.
- [x] Todos os valores de `justifyContent` documentados.
- [x] Todos os valores de `alignItems` documentados.
- [x] `alignContent` com múltiplas linhas/colunas.
- [x] `rowGap`, `columnGap` e padding por lado.
- [x] `widthMode` e `heightMode` fixed/hug.
- [x] Filhos absolutos fora do fluxo.
- [x] Auto Layout aninhado.
- [x] Persistência local, export JSON e undo/redo.
- [x] Canvas Infinito com Screen Space, World Space e Viewport Transform.
- [x] Zoom relativo ao cursor, limites, botões e atalhos.
- [x] Pan por wheel, trackpad, botão central, Hand Tool e Space + Drag.
- [x] Stage responsivo, touch/pinch e grid dinâmico.
- [x] Viewport persistido por página e fora do export JSON.
- [x] Restrições: sem Grid Layout, sem backend novo, sem estilos inline novos e sem persistência remota.
- [x] Regressão básica de canvas, seleção, layers e inspector.
