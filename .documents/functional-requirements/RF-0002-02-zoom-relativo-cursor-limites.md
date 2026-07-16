# RF-0002-02 — Implementar zoom relativo ao cursor com limites e atalhos

## Identificação

- ID: `RF-0002-02`
- REQ pai: `REQ-0002`
- Título: Implementar zoom relativo ao cursor com limites e atalhos
- Projeto: `act-ide-teste`

## Objetivo

Permitir zoom in/out no Design Canvas mantendo o ponto sob o cursor ou ponto focal visualmente estável, com limites mínimo/máximo e atalhos de teclado/interface.

## Contexto funcional

Ferramentas profissionais de design aplicam zoom relativo ao ponteiro para evitar que o conteúdo escape do foco do usuário. O Konva recomenda calcular o ponto antes da escala e reposicionar o stage após a escala.

## História do usuário

Como usuário do canvas, quero aproximar e afastar o conteúdo no ponto onde estou olhando para explorar detalhes sem perder o foco.

## Descrição funcional

O sistema deve tratar `Ctrl/Cmd + Wheel`, botões de zoom e atalhos `+`, `-`, `0`, `1`, `2`, aplicando zoom multiplicativo, respeitando escala mínima/máxima e atualizando indicador textual de zoom.

## Fluxo funcional

1. Usuário posiciona cursor sobre o canvas.
2. Usuário usa `Ctrl/Cmd + Wheel` ou comando de zoom.
3. Sistema calcula ponto focal em Screen Space.
4. Sistema converte ponto focal para World Space.
5. Sistema aplica nova escala limitada.
6. Sistema recalcula deslocamento do viewport.
7. Sistema atualiza indicador percentual e redesenha camadas.

## Regras de negócio

- `Ctrl + Wheel` deve fazer zoom no Windows/Linux.
- `Command + Wheel` deve fazer zoom no macOS.
- `+` deve aproximar.
- `-` deve afastar.
- `0` deve restaurar `100%`.
- `1` deve ajustar todos os objetos.
- `2` deve ajustar a seleção.
- Zoom deve respeitar escala mínima 5% e máxima 6400%.
- Atalhos não devem disparar em campos editáveis.

## Validações funcionais

- Ao atingir limite de zoom, eventos adicionais não devem alterar viewport.
- Indicador de zoom deve refletir o valor real limitado.
- Zoom por botão deve usar centro do viewport como ponto focal.

## Dados necessários

- `state.viewport.scale`
- `state.viewport.minScale`
- `state.viewport.maxScale`
- Posição do ponteiro no stage/container.

## Permissões

Não aplicável.

## Integrações

- Toolbar do Design Canvas.
- Stage Konva.
- Persistência local de viewport.

## Critérios de aceite

- Zoom pelo wheel com modificador funciona.
- Zoom permanece centralizado no cursor.
- Botões e atalhos atualizam escala.
- Limites mínimo/máximo são respeitados.
- O usuário consegue restaurar 100%, ajustar todos e ajustar seleção.

## Fora do escopo

- Animação complexa entre níveis de zoom.
- Curvas físicas de inércia.

## Dependências

- RF-0002-01.

## Riscos

- Navegadores tratam pinch de trackpad como wheel com `ctrlKey`; normalização deve ser defensiva.

## Rastreabilidade

- REQ: `REQ-0002`
- Discovery: seções 2, 4, 11 e 12.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Regras de zoom definidas.
- [x] Critérios de aceite definidos.
