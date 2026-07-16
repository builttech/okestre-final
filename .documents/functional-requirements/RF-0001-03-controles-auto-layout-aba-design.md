# RF-0001-03 — Disponibilizar controles de Auto Layout na aba Design

## Identificação

- ID: `RF-0001-03`
- REQ pai: `REQ-0001`
- Título: Disponibilizar controles de Auto Layout na aba Design
- Projeto: `act-ide-teste`

## Objetivo

Adicionar à aba Design do Design Canvas uma seção de Auto Layout com controles para ativar, remover e configurar layout flexível em frames.

## Contexto funcional

A aba Design já possui inspector de posição, tamanho e aparência. A feature exige uma nova seção visual que siga o padrão dark/premium/glass da interface e não use estilos inline.

## História do usuário

Como usuário do Design Canvas, quero configurar Auto Layout pelo painel direito para ajustar organização dos elementos sem editar JSON manualmente.

## Descrição funcional

A seção Auto Layout deve aparecer no inspector quando houver seleção. Para frames, deve permitir ativar/remover layout e editar direção, wrap, alinhamentos, distribuição, gaps, padding e sizing. Para elementos filhos de um frame com Auto Layout, deve permitir alternar participação estática ou absoluta.

## Fluxo funcional

1. Usuário seleciona elemento.
2. Sistema renderiza estado da seção Auto Layout.
3. Se for frame, controles de container ficam disponíveis.
4. Se não for frame, sistema mostra estado informativo ou controles de filho quando aplicável.
5. Alterações nos campos atualizam o modelo e recalculam o canvas.

## Regras de negócio

- Controles de container aparecem para frame selecionado.
- Botão de ativação aparece quando o frame não possui Auto Layout ativo.
- Botão de remoção aparece quando o frame possui Auto Layout ativo.
- Campos numéricos devem usar mínimo zero.
- Estados ativos devem ter feedback visual claro.
- A seção deve manter acessibilidade básica por labels, buttons e aria quando aplicável.

## Validações funcionais

- Sem seleção: seção oculta junto ao inspector.
- Frame sem Auto Layout: exibir CTA de ativação.
- Frame com Auto Layout: exibir controles completos.
- Filho dentro de Auto Layout: exibir toggle estático/absoluto.

## Dados necessários

- Seleção atual `state.selectedId`.
- Nó selecionado em `state.doc.nodes`.
- Propriedades `layout` e `layoutItem`.

## Permissões

Não aplicável.

## Integrações

- Inspector existente em `konva-designer.html`.
- Eventos de input/change em `konva-designer.js`.
- Estilos em `rebrand.css`.

## Critérios de aceite

- A seção Auto Layout aparece na aba Design.
- Frame selecionado permite ativar/remover Auto Layout.
- Controles refletem valores atuais do modelo.
- Alterações nos controles atualizam imediatamente o canvas.
- Estilos seguem a identidade visual existente.

## Fora do escopo

- Tooltips ricos avançados.
- Manipulação de gap diretamente no canvas.
- Atalhos de teclado específicos de Auto Layout.

## Dependências

- RF-0001-01.
- RF-0001-02.

## Riscos

- A largura do painel direito pode limitar a quantidade de controles; a UI deve usar grupos compactos.

## Rastreabilidade

- REQ: `REQ-0001`
- Discovery: seções 2, 4 a 10, 18 e 20.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Interface e estados definidos.
- [x] Critérios de aceite definidos.
