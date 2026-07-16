# RF-0001-04 — Persistir layout, histórico e estados operacionais

## Identificação

- ID: `RF-0001-04`
- REQ pai: `REQ-0001`
- Título: Persistir layout, histórico e estados operacionais
- Projeto: `act-ide-teste`

## Objetivo

Garantir que configurações de Auto Layout sejam preservadas no documento local do Design Canvas e que operações relevantes possam ser desfeitas/refeitas por snapshots locais.

## Contexto funcional

O canvas atual persiste o documento em `localStorage`, mas não possui histórico formal de undo/redo. A feature precisa registrar alterações de layout sem backend novo, mantendo compatibilidade com documentos existentes.

## História do usuário

Como usuário da aba Design, quero salvar, recarregar, desfazer e refazer alterações de Auto Layout para trabalhar com segurança.

## Descrição funcional

O sistema deve normalizar documentos antigos, salvar `layout` e `layoutItem` em `state.doc.nodes`, criar snapshots antes de alterações relevantes e fornecer undo/redo básico para operações do canvas, incluindo Auto Layout.

## Fluxo funcional

1. Sistema carrega documento local.
2. Sistema normaliza propriedades ausentes.
3. Usuário altera layout ou propriedades do canvas.
4. Sistema registra snapshot antes da alteração relevante.
5. Sistema recalcula e persiste documento.
6. Usuário aciona undo/redo por atalhos.
7. Sistema restaura snapshot, redesenha canvas e inspector.

## Regras de negócio

- Persistência local continua usando `localStorage`.
- Histórico deve ser limitado para evitar crescimento excessivo de memória.
- Undo/redo deve restaurar posições, dimensões, layout, layoutItem e parentId.
- Uma alteração contínua por campo pode ser tratada como snapshot simples nesta primeira versão.
- Documentos antigos sem `layout` permanecem válidos.

## Validações funcionais

- Recarregar a tela preserva Auto Layout.
- Undo restaura estado anterior de layout.
- Redo reaplica estado desfeito.
- JSON exportado inclui propriedades de layout.

## Dados necessários

- `state.doc`
- `state.history.undo`
- `state.history.redo`
- `layout`
- `layoutItem`

## Permissões

Não aplicável.

## Integrações

- `persistDoc()`.
- `renderCanvas()`.
- Atalhos de teclado no Design Canvas.

## Critérios de aceite

- Auto Layout permanece após salvar/recarregar.
- Undo/redo funcionam para ativar, remover e alterar propriedades de Auto Layout.
- Export JSON inclui as propriedades de layout.
- Histórico não exige backend novo.

## Fora do escopo

- Histórico colaborativo.
- Auditoria remota.
- Persistência em banco de dados.

## Dependências

- RF-0001-01.
- RF-0001-02.
- RF-0001-03.

## Riscos

- Histórico por snapshot completo pode não ser ideal para documentos grandes, mas é aceitável para a primeira entrega.

## Rastreabilidade

- REQ: `REQ-0001`
- Discovery: seções 22 e 23.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Persistência definida.
- [x] Critérios de aceite definidos.
