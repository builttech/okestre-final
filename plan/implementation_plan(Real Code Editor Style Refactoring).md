# Real Code Editor Style Refactoring

Refatorar o editor de arquivos do GitIDE para o padrão de um editor de código real, incluindo um painel lateral de numeração de linhas (gutter) sincronizado e rolagem horizontal (sem quebra de linha automática), proporcionando uma experiência de desenvolvimento premium similar ao VS Code ou Monaco.

## User Review Required

> [!IMPORTANT]
> A quebra de linha automática (word wrap) será desativada por padrão no editor para garantir o alinhamento perfeito com a numeração de linhas, adicionando suporte a rolagem horizontal automática.

## Proposed Changes

### Frontend Components

---

#### [MODIFY] [index.html](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/index.html)
- Modificar o contêiner `#file-editor-textarea` dentro da div `.editor-body-wrapper` para ser envolto por uma div `.editor-container`.
- Adicionar o elemento `.editor-gutter` com ID `editor-gutter` à esquerda da textarea para renderizar os números de linha.

---

#### [MODIFY] [style.css](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/style.css)
- Implementar as classes `.editor-container` e `.editor-gutter`.
- Atualizar a estilização de `#file-editor-textarea` para:
  - Remover bordas internas e fundo (que passam a ser controlados pelo contêiner pai).
  - Adicionar `white-space: pre;` e `overflow-x: auto;` para rolagem horizontal.
  - Sincronizar exatamente a fonte, altura de linha (`line-height`) e padding com o painel de numeração.

---

#### [MODIFY] [app.js](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/app.js)
- Implementar a função `updateLineNumbers()` para calcular e exibir dinamicamente os números das linhas baseado no conteúdo da textarea.
- Adicionar sincronismo de rolagem vertical (`scrollTop`) entre a textarea e o painel de números.
- Integrar a atualização dos números de linha nos fluxos de abertura de arquivos, digitação (evento `input`), desfazer alterações (rollback) e salvamento de arquivos.

## Verification Plan

### Manual Verification
1. Abrir qualquer arquivo do workspace no editor de código.
2. Verificar se a barra lateral esquerda de números de linha é exibida corretamente.
3. Rolar o arquivo verticalmente e atestar o sincronismo perfeito da numeração com as linhas de código.
4. Digitar novos conteúdos e quebras de linha, atestando o incremento automático e correto dos números.
5. Carregar um arquivo com linhas longas e verificar a presença de rolagem horizontal mantendo o comportamento de editor real.
