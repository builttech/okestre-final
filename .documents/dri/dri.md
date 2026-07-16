# DRI — Documento de Requisito de Interface do Projeto

## Projeto

act-ide-teste

# RI-0001 — Auto Layout na Aba Design

## Identificação da interface

- RI: `RI-0001`
- Nome: Auto Layout na Aba Design
- Tela: `/design-canvas`
- Arquivos principais: `gitide_server/static/konva-designer.html`, `gitide_server/static/konva-designer.js`, `gitide_server/static/rebrand.css`
- RFs vinculados: `RF-0001-01`, `RF-0001-02`, `RF-0001-03`, `RF-0001-04`

## Objetivo

Adicionar uma seção de Auto Layout ao inspector da aba Design, permitindo configurar layout flexível de frames diretamente pela interface visual.

## Contexto de uso

O usuário seleciona um frame ou elemento no canvas Konva. O painel direito exibe propriedades do item selecionado. A seção Auto Layout deve aparecer como parte desse inspector, sem substituir os controles existentes de posição, tamanho e aparência.

## Arquitetura da informação

A seção Auto Layout deve conter:

1. Cabeçalho com título e ação principal.
2. Estado de compatibilidade da seleção.
3. Controles de direção.
4. Controle de wrap.
5. Controles de alinhamento e distribuição.
6. Campos de gap.
7. Campos de padding.
8. Controles de sizing do frame.
9. Controles de participação no fluxo para filhos.
10. Microcopy de ajuda curta.

## Mapa de componentes

- `section.konva-auto-layout-section`
- `.konva-auto-layout-header`
- `.konva-auto-layout-actions`
- `.konva-auto-layout-body`
- `.konva-segmented-control`
- `.konva-field-grid`
- `.konva-auto-layout-state`
- `.konva-auto-layout-hint`

## Regras de exibição

- Sem seleção: o inspector permanece no estado vazio existente.
- Seleção de frame sem Auto Layout: exibir botão `Ativar` e descrição curta.
- Seleção de frame com Auto Layout: exibir controles completos e botão `Remover`.
- Seleção de filho dentro de frame com Auto Layout: exibir controle `Fluxo` com opções `Estático` e `Absoluto`.
- Seleção incompatível fora de frame: exibir mensagem informativa curta.

## Estados

- Padrão: controles visíveis e editáveis para frame com Auto Layout.
- Hover: botões e segmentos destacam superfície.
- Ativo: segmento selecionado usa destaque visual do design system.
- Foco: campos e botões mantêm foco visível.
- Desabilitado: estado para seleção incompatível.
- Erro: campos numéricos são normalizados para zero; não há erro bloqueante.

## Fluxo de interação

1. Usuário seleciona frame.
2. Se layout estiver inativo, clica em `Ativar`.
3. Sistema cria defaults e recalcula filhos.
4. Usuário altera direção, wrap, distribuição, align, gaps, padding e sizing.
5. Canvas atualiza em tempo real.
6. Usuário pode remover layout com `Remover`.
7. Usuário pode usar undo/redo por teclado.

## Mapeamento de dados

- `data-layout-action="enable"`: ativa layout.
- `data-layout-action="disable"`: remove layout.
- `data-layout-prop`: altera propriedade de `node.layout`.
- `data-layout-item-prop`: altera propriedade de `node.layoutItem`.
- Inputs numéricos: `rowGap`, `columnGap`, `paddingTop`, `paddingRight`, `paddingBottom`, `paddingLeft`.
- Selects: `alignItems`, `justifyContent`, `alignContent`, `widthMode`, `heightMode`.

## Hierarquia visual

A seção deve seguir o estilo dark/premium/glass do painel direito:

- cartão com borda sutil;
- header compacto;
- botões segmentados;
- campos em grid de duas colunas;
- labels pequenas em uppercase;
- destaque turquesa para estados ativos.

## Microcopy

- Título: `Auto Layout`
- CTA: `Ativar`
- Remoção: `Remover`
- Ajuda frame inativo: `Organize filhos automaticamente com direção, gap e padding.`
- Ajuda filho: `Filhos absolutos ficam fora do fluxo, mas continuam dentro do frame.`

## Responsividade

A tela é desktop-first. Os controles devem quebrar em grid compacto dentro do painel direito e não exceder a largura do aside. Em painéis estreitos, campos continuam em duas colunas quando houver espaço mínimo, ou ocupam toda a largura se o CSS responsivo for acionado futuramente.

## Acessibilidade

- Botões com `type="button"`.
- Labels associadas por texto visível.
- Estados ativos com `aria-pressed` quando aplicável.
- Inputs numéricos com `min="0"`.
- Foco visível preservado pelo CSS.

## Critérios de aceite da interface

- [ ] A seção Auto Layout aparece no inspector da aba Design.
- [ ] O frame selecionado permite ativar Auto Layout.
- [ ] O frame com Auto Layout exibe controles completos.
- [ ] Os controles refletem o estado atual do frame.
- [ ] Alterações nos controles atualizam o canvas.
- [ ] O filho de Auto Layout permite alternar entre estático e absoluto.
- [ ] A interface mantém identidade dark/premium/glass.
- [ ] Não há estilos inline novos.

## Lacunas e premissas

- Multi-seleção completa ainda não é assumida como disponível.
- Tooltips avançados podem ser evoluídos depois.
- Feedback visual avançado de gap/padding no canvas pode ser incremental.

## Fora do escopo

- Grid Layout.
- Manipulação direta de gap no canvas.
- Responsividade mobile avançada.
- Persistência remota.

## Evoluções futuras

- Criar frame Auto Layout a partir de seleção múltipla.
- Indicador visual de inserção durante reordenação complexa.
- Drag direto para alterar gaps.
- Vinculação de gaps/padding com tokens de spacing.

## Rastreabilidade

- TAP: `.documents/project-charter.md`
- REQ: `REQ-0001`
- RFs: `RF-0001-01`, `RF-0001-02`, `RF-0001-03`, `RF-0001-04`
- Design: `.documents/design/design.md`

## Histórico

- 2026-07-16: RI criado para a feature Auto Layout Flexível.
