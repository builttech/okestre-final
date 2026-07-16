# RF-0002-04 — Implementar responsividade, touch/pinch e grid dinâmico

## Identificação

- ID: `RF-0002-04`
- REQ pai: `REQ-0002`
- Título: Implementar responsividade, touch/pinch e grid dinâmico
- Projeto: `act-ide-teste`

## Objetivo

Adaptar o stage ao container visível, suportar gestos touch/pinch e substituir o grid fixo por grid dinâmico alinhado ao World Space.

## Contexto funcional

Um Canvas Infinito não deve depender de um stage fisicamente gigante. O stage deve acompanhar o viewport da aplicação, enquanto o grid deve ser renderizado apenas na região visível e acompanhar pan/zoom.

## História do usuário

Como usuário, quero que o canvas se adapte ao tamanho da janela, preserve minha visualização e permita navegar por toque em dispositivos compatíveis.

## Descrição funcional

O sistema deve observar o tamanho do container do canvas, ajustar dimensões do stage, preservar o viewport, aplicar touch pan com um dedo em área vazia, aplicar pinch com dois dedos e recalcular o grid visível conforme viewport e escala.

## Fluxo funcional

1. Sistema mede o container do canvas.
2. Sistema atualiza `stage.width` e `stage.height`.
3. Sistema preserva `viewport.x`, `viewport.y` e `viewport.scale`.
4. Usuário usa touch pan ou pinch.
5. Sistema recalcula viewport pelo ponto médio do gesto.
6. Sistema redesenha grid dinâmico baseado na área visível.

## Regras de negócio

- Stage deve acompanhar o container visível.
- Resize não deve reposicionar objetos.
- Grid deve ser alinhado ao World Space.
- Grid deve se mover junto com o viewport.
- Grid deve ajustar densidade conforme escala.
- Pan touch com um dedo deve funcionar em área vazia.
- Pinch com dois dedos deve aplicar zoom relativo ao ponto médio.
- Movimento nativo da página deve ser bloqueado dentro do canvas durante gestos.

## Validações funcionais

- Redimensionar janela não reseta zoom/pan.
- Grid não apresenta saltos durante pan.
- Touch não move objetos quando a intenção é pan de viewport.

## Dados necessários

- Tamanho do container.
- Estado do viewport.
- Pontos ativos de toque.
- Bounding box visível em World Space.

## Permissões

Não aplicável.

## Integrações

- Container `.konva-stage-scroll`.
- Stage Konva.
- Grid layer.
- Eventos touch/pointer.

## Critérios de aceite

- Stage redimensiona com o container.
- Grid acompanha pan e zoom em World Space.
- Pinch altera zoom pelo centro do gesto.
- Pan touch em área vazia move viewport.
- Resize preserva viewport.

## Fora do escopo

- Experiência mobile completa de edição.
- Orientação tablet avançada.
- Minimap.

## Dependências

- RF-0002-01.
- RF-0002-02.
- RF-0002-03.

## Riscos

- Navegadores móveis variam no suporte a eventos touch/pointer.

## Rastreabilidade

- REQ: `REQ-0002`
- Discovery: seções 5, 8, 9 e 10.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Responsividade e touch definidos.
- [x] Critérios de aceite definidos.
