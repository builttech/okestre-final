# RF-0002-05 — Persistir viewport, preservar performance e acessibilidade

## Identificação

- ID: `RF-0002-05`
- REQ pai: `REQ-0002`
- Título: Persistir viewport, preservar performance e acessibilidade
- Projeto: `act-ide-teste`

## Objetivo

Persistir o viewport por página no frontend local, preservar performance durante pan/zoom e oferecer alternativas de navegação e recuperação visual acessíveis.

## Contexto funcional

A navegação do viewport é preferência local do usuário e não deve ser confundida com conteúdo do documento. A experiência também precisa oferecer atalhos, indicador textual e comandos de recuperação para evitar que o usuário se perca no espaço virtual.

## História do usuário

Como usuário, quero que minha visualização do canvas seja recuperável, responsiva e acessível, sem que pan e zoom poluam o histórico de edição ou degradem a performance.

## Descrição funcional

O sistema deve salvar viewport por página em `localStorage`, atualizar transformações de forma eficiente, evitar recriação desnecessária de objetos, oferecer indicador textual de zoom, comandos de reset/fit/center e não capturar permanentemente o foco do teclado.

## Fluxo funcional

1. Usuário navega por pan/zoom.
2. Sistema atualiza viewport em memória.
3. Sistema persiste viewport localmente por página.
4. Usuário troca/reabre página.
5. Sistema restaura viewport quando disponível.
6. Usuário usa atalhos/controles para recuperar visualização.

## Regras de negócio

- Viewport deve ser persistido por página.
- Viewport não deve fazer parte do conteúdo exportado do documento, salvo decisão futura explícita.
- Pan/zoom não devem criar snapshots undo/redo de edição.
- Indicador textual de zoom deve ser atualizado em tempo real.
- Comandos de zoom devem possuir alternativa visual e por teclado.
- Atalhos devem ser ignorados em campos editáveis.
- Transformações devem preferir atualização do stage/layers, evitando reconstruir todos os nós durante pan/zoom.

## Validações funcionais

- Recarregar a tela restaura viewport por página quando houver estado salvo.
- O usuário consegue voltar a 100%, ajustar todos e ajustar seleção.
- Pan/zoom com documento grande permanece responsivo em revisão manual.

## Dados necessários

- Chave local de persistência de viewport.
- ID da página ativa.
- Estado de viewport.
- Bounding boxes de todos os objetos ou seleção.

## Permissões

Não aplicável.

## Integrações

- `localStorage`.
- Atalhos de teclado.
- Toolbar do canvas.
- Stage/camadas Konva.

## Critérios de aceite

- Viewport é salvo e restaurado por página.
- Indicador textual mostra percentual correto.
- Comandos 100%, ajustar todos, ajustar seleção e centralizar funcionam.
- Pan/zoom não geram histórico undo/redo de objetos.
- Atalhos são ignorados em campos editáveis.
- Não há estilos inline novos.

## Fora do escopo

- Sincronização do viewport entre usuários.
- Histórico auditável de navegação.
- Métricas formais de FPS.

## Dependências

- RF-0002-01.
- RF-0002-02.
- RF-0002-03.
- RF-0002-04.

## Riscos

- Persistência local pode conflitar com documentos antigos se a chave não for versionada.

## Rastreabilidade

- REQ: `REQ-0002`
- Discovery: seções 6, 9, 11 e 12.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Persistência, performance e acessibilidade definidos.
- [x] Critérios de aceite definidos.
