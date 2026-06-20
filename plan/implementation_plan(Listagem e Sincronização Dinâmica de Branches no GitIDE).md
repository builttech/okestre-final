# Listagem e Sincronização Dinâmica de Branches no GitIDE

Este plano visa substituir a entrada de texto manual de branch por um seletor dinâmico (`select`) que lista todas as branches locais e remotas do repositório, permitindo a alternação automática de branch ao selecionar e a execução de deploys (push) e sincronizações (pull) na branch correta. Além disso, ajusta a estilização e posicionamento do menu de ações da branch para garantir que ele abra no local correto e se integre ao tema escuro.

## User Review Required

> [!IMPORTANT]
> A alternância no seletor de branch agora executará um checkout automático no repositório local. Qualquer alteração não salva ou conflito no checkout será reportado no console do Git.

## Proposed Changes

### Frontend Components

---

#### [MODIFY] [index.html](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/index.html)
- Substituir o input `#git-branch-input` por um elemento `<select id="git-branch-input" class="select-input">` para possibilitar a seleção de branches de uma lista dinâmica.
- Incrementar a versão dos arquivos importados `style.css` e `app.js` para `?v=3` para evitar cache do navegador.

---

#### [MODIFY] [style.css](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/style.css)
- Atualizar `.inline-form select` para ter `flex: 1` e acompanhar o alinhamento da linha de botões.
- Refatorar a classe `.dropdown-menu` e `.dropdown-item` para utilizar fundo escuro semi-transparente, borda sutil, z-index aprimorado e cores adequadas ao tema de glassmorfismo escuro.

---

#### [MODIFY] [app.js](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/app.js)
- Implementar a função `loadGitBranches(currentBranch)` para buscar as branches em `/api/projects/{project_id}/git/branches` e alimentar o select `#git-branch-input`, agrupando-as em `<optgroup>` de "Branches Locais" e "Branches Remotas".
- Adicionar evento `change` no `#git-branch-input` para disparar checkout automático (através do endpoint `POST /api/projects/{project_id}/git/branches`) ao selecionar uma branch diferente.
- Chamar `loadGitBranches()` dentro do fluxo de `loadGitStatus()` para garantir sincronismo das opções exibidas com a branch ativa.

## Verification Plan

### Manual Verification
1. Acessar a aba Git no dashboard do GitIDE.
2. Confirmar que o campo de branch agora é um seletor dropdown contendo as branches locais e remotas.
3. Selecionar uma branch diferente no seletor e verificar no console do Git e na interface se o checkout foi executado com sucesso e o status foi atualizado.
4. Clicar no botão de ações da branch ativa no status (canto superior esquerdo do painel) e verificar se o menu de ações abre de forma alinhada, com o design escuro correto.
5. Executar um deploy (Push) ou pull (Sincronizar) e atestar a correta execução.
