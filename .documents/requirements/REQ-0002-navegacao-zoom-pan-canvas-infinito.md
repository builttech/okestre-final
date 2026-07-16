# REQ-0002 — Navegação, Zoom e Pan em Canvas Infinito

## Identificação

- ID: `REQ-0002`
- Título: Navegação, Zoom e Pan em Canvas Infinito
- Projeto: `act-ide-teste`
- Origem: `.discovery/saida/implementation_of_navigation_zoom_and_pan_in_infinite_canvas.md`
- Tela principal: `/design-canvas`

## Objetivo

Evoluir a navegação do Design Canvas em Konva.js para oferecer viewport virtualmente infinito, zoom relativo ao cursor, pan fluido nos quatro eixos e suporte a mouse, trackpad, teclado e touch, preservando coordenadas globais dos objetos e a experiência visual existente.

## Contexto de negócio

A tela de Design Canvas deve se aproximar de ferramentas profissionais de design, permitindo explorar áreas amplas sem depender de um `Stage` fisicamente gigante. O usuário precisa navegar, aproximar, afastar, centralizar conteúdo e recuperar visualizações perdidas de forma previsível, mantendo frames, objetos, Auto Layout, seleção e transformadores sincronizados.

## Escopo macro

- Separar conceitualmente Screen Space, World Space e Viewport Transform.
- Substituir dependência de rolagem física do container por transformação do viewport.
- Permitir zoom por `Ctrl/Cmd + Wheel`, botões e atalhos de teclado.
- Manter zoom centralizado no cursor ou ponto focal de gesto.
- Permitir pan por wheel, trackpad, botão central, ferramenta Hand e `Space + Drag`.
- Permitir navegação visualmente ilimitada nos quatro eixos.
- Adicionar controles de zoom, reset, ajustar todos, ajustar seleção e centralizar conteúdo.
- Atualizar grid para acompanhar World Space e viewport visível.
- Persistir estado de viewport por página em `localStorage` sem gravar como conteúdo colaborativo.
- Preservar coordenadas persistidas dos objetos durante pan/zoom.
- Garantir que seleção, transformer, labels e overlays acompanhem a transformação.

## RFs vinculados

- `RF-0002-01` — Modelar viewport e coordenadas do Canvas Infinito.
- `RF-0002-02` — Implementar zoom relativo ao cursor com limites e atalhos.
- `RF-0002-03` — Implementar pan, scroll e Hand Tool.
- `RF-0002-04` — Implementar responsividade, touch/pinch e grid dinâmico.
- `RF-0002-05` — Persistir viewport, preservar performance e acessibilidade.

## Regras gerais

- Pan e zoom não podem alterar `x`, `y`, `width`, `height`, `rotation`, `parentId`, hierarquia ou ordem de camadas dos objetos.
- Objetos continuam armazenados em World Space.
- O viewport deve possuir `x`, `y`, `scale`, escala mínima e escala máxima.
- Escala mínima inicial: `0.05` ou 5%.
- Escala máxima inicial: `64` ou 6400%.
- Zoom deve ser multiplicativo, evitando saltos lineares excessivos.
- Ao atingir limite mínimo ou máximo, o viewport não deve saltar.
- O comportamento nativo de zoom/scroll do navegador deve ser bloqueado apenas dentro da área do canvas.
- Atalhos não devem disparar quando o usuário estiver em input, textarea, select, contenteditable ou editor de texto.
- Viewport não deve entrar no histórico undo/redo de edição de objetos.

## Fontes de dados

- Documento local do canvas salvo em `localStorage`.
- Estado em memória `state.doc`.
- Novo estado de viewport em memória.
- Persistência local de viewport por página.

## Dados necessários

- `state.viewport.x`
- `state.viewport.y`
- `state.viewport.scale`
- `state.viewport.minScale`
- `state.viewport.maxScale`
- `state.viewport.interactionMode`
- `state.viewport.isPanning`
- `state.viewport.spacePressed`
- `state.viewport.lastPointerPosition`
- `state.viewport.touchGesture`

## Critérios de aceite macro

- `Ctrl + Wheel` executa zoom no Windows/Linux.
- `Command + Wheel` executa zoom no macOS.
- Zoom permanece centralizado no cursor.
- `Wheel` navega verticalmente dentro do canvas.
- `Shift + Wheel` navega horizontalmente dentro do canvas.
- Trackpad suporta pan horizontal e vertical.
- Botão central + arraste executa pan.
- `Space + Drag` executa pan sem mover objetos.
- Ferramenta Hand permite pan fixo.
- `+`, `-`, `0`, `1` e `2` executam os atalhos documentados.
- Gestos pinch funcionam em dispositivos touch quando disponíveis.
- Redimensionamento do container preserva viewport.
- O usuário consegue retornar ao conteúdo com ajustar todos/seleção/centralizar.
- Seleção e transformer permanecem sincronizados.
- Pan/zoom não modificam coordenadas persistidas dos objetos.

## Dependências

- `gitide_server/static/konva-designer.html`.
- `gitide_server/static/konva-designer.js`.
- `gitide_server/static/rebrand.css`.
- Konva.js carregado pela tela.
- Estado local do Design Canvas.

## Premissas

- A feature será implementada em JavaScript puro na rota `/design-canvas`.
- A primeira entrega utiliza transformação do `Stage`, preservando as camadas existentes.
- Culling avançado e minimap ficam fora da primeira entrega.
- Validação executável local pode não estar disponível porque o projeto roda em VM.

## Restrições

- Não criar backend novo.
- Não criar persistência remota de viewport.
- Não usar estilos inline novos.
- Não editar `.discovery/saida`.
- Não transformar pan/zoom em alteração de documento persistido.
- Não quebrar Auto Layout existente.

## Fora do escopo

- Minimap.
- Culling/virtualização avançada de objetos fora do viewport.
- Colaboração em tempo real do viewport.
- Redefinição manual da origem global.
- Seleção por área completa caso a infraestrutura atual não suporte.
- Animações complexas de fit/zoom.

## Riscos

- Conflito entre pan e drag de objetos.
- Inconsistência entre transformer/labels e stage escalado.
- Eventos de trackpad podem variar entre navegadores e sistemas operacionais.
- Touch/pinch pode exigir validação manual em dispositivo real.
- Grid dinâmico pode afetar performance se desenhado com linhas demais.

## Rastreabilidade

- TAP: `.documents/project-charter.md`
- Discovery: `.discovery/saida/implementation_of_navigation_zoom_and_pan_in_infinite_canvas.md`
- Design: `.documents/design/design.md`
- DRI: `.documents/dri/dri.md`

## Histórico de alterações

- 2026-07-16: REQ criado a partir do discovery de navegação, zoom e pan em Canvas Infinito.

## Checklist de qualidade

- [x] Objetivo documentado.
- [x] Escopo macro definido.
- [x] RFs vinculados.
- [x] Regras gerais listadas.
- [x] Critérios de aceite macro definidos.
- [x] Fora do escopo explícito.
- [x] Rastreabilidade registrada.
