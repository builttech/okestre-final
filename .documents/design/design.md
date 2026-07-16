# Design — Planejamento Técnico do Projeto

## Projeto

act-ide-teste

## 1. Identificação

- Design vivo do projeto Act IA/GitIDE.
- Feature atual: Auto Layout Flexível na Aba Design.
- REQ principal: `REQ-0001`.
- RFs vinculados: `RF-0001-01`, `RF-0001-02`, `RF-0001-03`, `RF-0001-04`.
- Fonte de discovery: `.discovery/saida/Feat_ Auto Layout Flexível na Aba Design.md`.

## 2. Visão técnica geral

O projeto é uma aplicação web local baseada em Python/FastAPI com frontend estático em `gitide_server/static`. A tela `/design-canvas` é uma experiência independente de design visual baseada em Konva.js, composta principalmente por:

- `gitide_server/static/konva-designer.html`
- `gitide_server/static/konva-designer.js`
- `gitide_server/static/rebrand.css`

O Design Canvas mantém um documento local em memória e em `localStorage`, com páginas e nós visuais. Os nós são renderizados em uma camada Konva e a hierarquia visual é derivada de `parentId`.

A feature de Auto Layout será implementada inteiramente no frontend desta tela, sem backend novo, adicionando propriedades de layout ao modelo local e um motor Flex Layout próprio para calcular posições e dimensões dos filhos.

## 3. Stack e módulos impactados

### Frontend estático

- HTML: `konva-designer.html`
- JavaScript: `konva-designer.js`
- CSS: `rebrand.css`
- Bibliotecas carregadas pela tela: Konva.js e Lucide Icons

### Backend

- Não há mudança de backend para esta feature.
- APIs existentes não serão alteradas.

### Persistência

- Persistência local existente por `localStorage`.
- Export JSON existente continua refletindo `state.doc`.

## 4. Arquitetura funcional

O Design Canvas funciona com:

- `state.doc.pages`: lista de páginas do arquivo visual.
- `state.doc.activePageId`: página ativa.
- `state.doc.nodes`: lista flat de nós visuais.
- `node.parentId`: vínculo hierárquico entre filho e frame.
- `contentLayer`: camada Konva de renderização dos nós.
- `uiLayer`: camada Konva de feedback visual, transformer, labels e metadados.
- Inspector da aba Design: painel direito com controles da seleção.

A nova feature adiciona:

- `node.layout`: configuração de Auto Layout em frames.
- `node.layoutItem`: configuração do filho quando está dentro de um container com Auto Layout.
- `state.history.undo` e `state.history.redo`: snapshots locais para undo/redo.
- Funções de cálculo e aplicação de layout antes/depois de renderizações relevantes.

## 5. Modelo de dados conceitual

### Frame com Auto Layout

```json
{
  "id": "frame-1",
  "type": "frame",
  "parentId": null,
  "x": 420,
  "y": 120,
  "width": 640,
  "height": 360,
  "layout": {
    "enabled": true,
    "direction": "row",
    "wrap": false,
    "alignItems": "start",
    "justifyContent": "start",
    "alignContent": "start",
    "rowGap": 12,
    "columnGap": 12,
    "paddingTop": 24,
    "paddingRight": 24,
    "paddingBottom": 24,
    "paddingLeft": 24,
    "widthMode": "fixed",
    "heightMode": "fixed"
  }
}
```

### Filho de Auto Layout

```json
{
  "id": "rect-1",
  "type": "rect",
  "parentId": "frame-1",
  "layoutItem": {
    "position": "static",
    "order": 0,
    "zIndex": 0
  }
}
```

## 6. Motor Flex Layout para Konva

Como Konva não executa CSS Flexbox, o cálculo será feito pelo JavaScript da tela.

### Pipeline técnico

1. Normalizar documento carregado.
2. Identificar frames com `layout.enabled`.
3. Ordenar containers por profundidade, calculando filhos antes dos pais quando houver layout aninhado.
4. Coletar filhos do frame via `parentId`.
5. Separar filhos estáticos e absolutos.
6. Medir largura e altura de cada filho a partir do modelo.
7. Formar linhas/colunas conforme direção e wrap.
8. Aplicar `justifyContent` no eixo principal.
9. Aplicar `alignItems` no eixo transversal.
10. Aplicar `alignContent` quando houver múltiplas linhas.
11. Ajustar `width`/`height` do frame quando eixo estiver em modo `hug`.
12. Atualizar `x`/`y` dos filhos no modelo e nos nós Konva existentes.
13. Redesenhar camadas afetadas.

### Direções suportadas

- `row`
- `row-reverse`
- `column`
- `column-reverse`

### Distribuição principal

- `start`
- `center`
- `end`
- `space-between`
- `space-around`
- `space-evenly`

### Alinhamento transversal

- `start`
- `center`
- `end`

### Dimensionamento

- `fixed`: mantém dimensão atual.
- `hug`: ajusta dimensão com base em filhos, gaps e padding.

## 7. Estratégia de interface

A aba Design receberá uma seção `Auto Layout` dentro do inspector. A seção terá:

- Estado informativo sem seleção ou seleção incompatível.
- Botão de ativar Auto Layout para frames sem layout.
- Botão de remover Auto Layout para frames com layout.
- Controles segmentados de direção.
- Toggle de wrap.
- Selects para alinhamento, distribuição e alinhamento de linhas.
- Campos numéricos para gap de linha/coluna.
- Campos numéricos para padding top/right/bottom/left.
- Selects para sizing de largura/altura.
- Toggle estático/absoluto para filhos de containers com Auto Layout.

Todos os estilos devem ser feitos em `rebrand.css`, sem inline style.

## 8. Estratégia de histórico e persistência

A persistência continua em `localStorage`. Antes de alterações relevantes, o sistema registra snapshot completo de `state.doc` em `state.history.undo`, limitado por tamanho máximo. Redo é limpo ao criar nova alteração.

Atalhos previstos:

- `Ctrl/Cmd + Z`: undo.
- `Ctrl/Cmd + Shift + Z` ou `Ctrl/Cmd + Y`: redo.

## 9. Integrações e APIs

Não há novas APIs. A feature opera sobre o documento local da tela.

## 10. Logs, auditoria e segurança

Não há log backend novo. A rastreabilidade da implementação fica nos documentos Harness e no controle Git do workspace. A feature não manipula credenciais.

## 11. QA e validação

Validações previstas:

- Revisão sintática de `konva-designer.js`.
- Revisão de HTML para ausência de estilos inline novos.
- Revisão de CSS escopado.
- Validação manual em `/design-canvas`:
  - selecionar frame;
  - ativar Auto Layout;
  - mudar direção;
  - alterar wrap, gaps, padding, align e justify;
  - alternar fixed/hug;
  - alternar filho estático/absoluto;
  - salvar/recarregar;
  - usar undo/redo.

## 12. Decisões técnicas

- A feature será implementada no frontend da rota `/design-canvas`.
- A primeira versão usa seleção única, compatível com o canvas atual.
- Multi-seleção e criação de frame a partir de seleção múltipla ficam como evolução futura caso a infraestrutura de multi-seleção não esteja presente.
- O motor Flex Layout será próprio, determinístico e baseado no modelo local.
- Grid Layout está explicitamente fora do escopo.

## 13. Riscos técnicos

- Layout aninhado exige cuidado para evitar loops e cálculo fora de ordem.
- Snapshot completo é simples e seguro, mas pode ser pesado em documentos grandes.
- A engine Flex própria pode exigir refinamentos para equivalência total a CSS Flexbox/Penpot.
- Validação executável depende da disponibilidade de runtime local ou VM/Ops Infra.

## 14. Rastreabilidade

- TAP: `.documents/project-charter.md`
- REQ: `.documents/requirements/REQ-0001-auto-layout-flexivel-aba-design.md`
- RFs:
  - `.documents/functional-requirements/RF-0001-01-modelar-ativar-auto-layout-frames.md`
  - `.documents/functional-requirements/RF-0001-02-calcular-flex-layout-konva.md`
  - `.documents/functional-requirements/RF-0001-03-controles-auto-layout-aba-design.md`
  - `.documents/functional-requirements/RF-0001-04-persistir-historico-auto-layout.md`
- DRI: `.documents/dri/dri.md`
- Tasks: `.documents/task/task.md`

## 15. Próximos passos

- Atualizar DRI da interface Auto Layout.
- Criar tasks por RF.
- Executar implementação aprovada.
- Validar tecnicamente e registrar evidências.
