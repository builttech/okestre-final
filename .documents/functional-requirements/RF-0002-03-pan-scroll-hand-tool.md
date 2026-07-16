# RF-0002-03 — Implementar pan, scroll e Hand Tool

## Identificação

- ID: `RF-0002-03`
- REQ pai: `REQ-0002`
- Título: Implementar pan, scroll e Hand Tool
- Projeto: `act-ide-teste`

## Objetivo

Permitir movimentação fluida do viewport nos quatro eixos por wheel, trackpad, botão central, ferramenta Hand e `Space + Drag`, sem mover objetos nem alterar seleção.

## Contexto funcional

O canvas atual depende de scroll físico do container. A nova experiência deve mover o viewport por transformação, preservando o documento e evitando conflitos com drag de objetos.

## História do usuário

Como usuário do canvas, quero arrastar a visualização livremente para navegar por áreas distantes sem mover frames ou elementos selecionados.

## Descrição funcional

O sistema deve interpretar wheel sem modificadores como pan vertical, `Shift + Wheel` como pan horizontal, gestos de trackpad como pan nos eixos `deltaX/deltaY`, botão central + arraste como pan, ferramenta Hand como pan fixo e `Space + Drag` como pan temporário.

## Fluxo funcional

1. Usuário inicia interação de pan.
2. Sistema identifica o modo de pan.
3. Sistema preserva seleção e desativa drag de objeto durante o pan.
4. Sistema atualiza `viewport.x` e `viewport.y`.
5. Sistema redesenha grid, conteúdo e overlays.
6. Sistema encerra pan em `pointerup` ou perda de ponteiro.

## Regras de negócio

- `Wheel` sem modificador move o viewport verticalmente.
- `Shift + Wheel` move o viewport horizontalmente.
- Trackpad usa `deltaX` e `deltaY` quando disponíveis.
- Botão central + arraste move o viewport.
- `Space + botão principal + arraste` move o viewport.
- Ferramenta Hand fixa move o viewport com botão principal.
- Objetos não devem ser movidos durante pan.
- A seleção atual deve ser preservada durante pan.
- Cursor deve comunicar `grab` e `grabbing`.

## Validações funcionais

- Pan funciona mesmo sem objetos visíveis.
- Pan não possui limites rígidos de deslocamento.
- `pointerup` fora do stage encerra pan.

## Dados necessários

- `state.viewport.x`
- `state.viewport.y`
- `state.viewport.isPanning`
- `state.viewport.spacePressed`
- `state.tool`

## Permissões

Não aplicável.

## Integrações

- Stage/container Konva.
- Toolbar de ferramentas.
- Eventos de teclado e pointer.

## Critérios de aceite

- Wheel vertical move o viewport verticalmente.
- Shift+Wheel move o viewport horizontalmente.
- Botão central + drag executa pan.
- Space+Drag executa pan sem mover objetos.
- Hand Tool executa pan fixo.
- Seleção e objetos permanecem intactos durante pan.

## Fora do escopo

- Inércia avançada de trackpad.
- Auto-pan durante drag de objetos como comportamento completo obrigatório da primeira entrega.

## Dependências

- RF-0002-01.

## Riscos

- Conflito entre pan temporário e shortcuts de inputs.

## Rastreabilidade

- REQ: `REQ-0002`
- Discovery: seções 3, 4 e 12.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Regras de pan definidas.
- [x] Critérios de aceite definidos.
