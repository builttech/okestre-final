# RF-0002-01 — Modelar viewport e coordenadas do Canvas Infinito

## Identificação

- ID: `RF-0002-01`
- REQ pai: `REQ-0002`
- Título: Modelar viewport e coordenadas do Canvas Infinito
- Projeto: `act-ide-teste`

## Objetivo

Criar um estado central de viewport e funções de conversão entre Screen Space e World Space para permitir navegação virtualmente infinita sem alterar as coordenadas persistidas dos objetos.

## Contexto funcional

O canvas atual usa dimensões fixas de stage e rolagem física do container. A nova navegação deve manter o stage próximo ao tamanho visível e simular o espaço infinito por `scale`, `x` e `y` do viewport.

## História do usuário

Como usuário do Design Canvas, quero navegar por um espaço de trabalho amplo sem que frames e objetos mudem suas coordenadas reais.

## Descrição funcional

O sistema deve manter um estado `viewport` com posição, escala, limites e estado de interação. Todas as operações de criação, seleção, drag, zoom e pan devem usar funções centralizadas para converter pontos de tela em coordenadas globais do documento.

## Fluxo funcional

1. Usuário abre `/design-canvas`.
2. Sistema inicializa viewport da página ativa.
3. Sistema dimensiona o stage pelo container visível.
4. Sistema aplica transformação de viewport ao stage.
5. Interações do usuário convertem pontos de tela para World Space.
6. Objetos permanecem persistidos em coordenadas globais.

## Regras de negócio

- `viewport.scale` deve iniciar em `1` quando não houver estado salvo.
- `viewport.minScale` deve ser `0.05`.
- `viewport.maxScale` deve ser `64`.
- Pan/zoom não devem entrar no histórico de undo/redo de objetos.
- Objetos devem continuar usando coordenadas globais.
- Stage deve acompanhar o tamanho do container sem mover objetos.

## Validações funcionais

- Valores inválidos de viewport devem ser normalizados.
- Conversão Screen → World deve considerar escala e deslocamento atuais.
- Conversão World → Screen deve considerar escala e deslocamento atuais.

## Dados necessários

- `state.viewport.x`
- `state.viewport.y`
- `state.viewport.scale`
- `state.viewport.minScale`
- `state.viewport.maxScale`
- `state.doc.activePageId`

## Permissões

Não aplicável. A feature opera no frontend local do canvas.

## Integrações

- Stage Konva.
- Camadas `gridLayer`, `contentLayer` e `uiLayer`.
- Persistência local existente.

## Critérios de aceite

- O stage acompanha o tamanho do container.
- Conversões Screen/World retornam coordenadas consistentes após zoom e pan.
- Criar objeto após pan/zoom posiciona o objeto no ponto visual correto.
- Mover viewport não altera coordenadas persistidas dos objetos.

## Fora do escopo

- Redefinição manual da origem global.
- Sincronização colaborativa do viewport.

## Dependências

- `gitide_server/static/konva-designer.js`.

## Riscos

- Inconsistência de coordenadas em drag/resize se algum fluxo continuar usando coordenadas do stage sem conversão.

## Rastreabilidade

- REQ: `REQ-0002`
- Discovery: seções 1, 6, 7 e 8.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Fluxo funcional definido.
- [x] Critérios de aceite definidos.
