# REQ-3090 — Higienização de branches Git locais e remotas

## 1.1 Identificação e Metadados Básicos

| Campo | Valor |
|---|---|
| ID | REQ-3090 |
| Título/Resumo | Higienização de branches Git locais e remotas obsoletas |
| Tipo | Operação técnica de versionamento |
| Módulo | Git / Controle de versão |
| Prioridade | Alta |
| Status | Aprovado para execução |
| Solicitante | Usuário |
| Responsável atual | Agente IA |
| Release/Iteração | Operação pontual |
| Esforço estimado | Baixo |

## 1.2 Contexto

O projeto `git-ide` possui branches locais e/ou remotas que o usuário solicitou remover explicitamente. A operação deve eliminar referências locais e remotas das branches informadas, preservando o restante do repositório e sem alterar código-fonte da aplicação.

Branches alvo:

- `dev`
- `backup/dev-local-before-origin-sync-20260626`
- `homolog`
- `backup/homolog-before-dev-merge-20260626`

## 1.3 Objetivo Funcional

Permitir que o workspace Git do projeto fique higienizado, removendo branches obsoletas ou de backup que não devem mais existir localmente nem no remoto `origin`.

## 1.4 Descrição do Requisito

O agente deve verificar as branches existentes no repositório local e remoto e executar a exclusão das branches solicitadas pelo usuário, tanto localmente quanto no remoto, quando elas existirem e quando a operação for permitida pelo Git.

A operação deve evitar remoção acidental de outras branches e não deve trocar, mesclar, criar, renomear ou publicar branches não relacionadas.

## 1.5 História de Usuário

Como mantenedor do projeto, quero remover branches locais e remotas obsoletas para manter o histórico de branches limpo e evitar confusão operacional durante sincronizações e deploys.

## 1.6 Regras de Negócio

- Somente as branches explicitamente listadas pelo usuário podem ser removidas.
- A branch ativa não deve ser removida enquanto estiver em checkout.
- A exclusão local deve ser tentada de forma segura quando possível.
- Se uma branch local não puder ser removida com exclusão segura por não estar totalmente mesclada, pode ser aplicada exclusão forçada apenas para as branches alvo aprovadas.
- A exclusão remota deve ocorrer no remoto `origin` usando a referência exata da branch alvo.
- Branch inexistente local ou remotamente deve ser reportada, não tratada como alteração de escopo.

## 1.7 Restrições e Premissas

- O repositório local do projeto está corretamente inicializado com Git.
- O remoto principal é `origin`.
- O usuário aprovou explicitamente a operação no formato `Aprovado executar TASK-REQ-3090-001`.
- A operação depende das permissões Git configuradas no ambiente local para remover branches remotas.
- Não serão alterados arquivos de código da aplicação durante a exclusão de branches.

## 1.8 Fora do Escopo

- Criar novas branches.
- Realizar merge, rebase, cherry-pick ou sincronização de conteúdo.
- Alterar URLs de remoto, tokens ou credenciais Git.
- Deletar tags.
- Modificar arquivos de aplicação fora da documentação Harness necessária.
- Fazer deploy.

## 1.9 Critérios de Aceite

- [ ] As branches alvo inexistentes são identificadas sem interromper indevidamente a operação.
- [ ] As branches alvo existentes localmente são removidas do repositório local.
- [ ] As branches alvo existentes no remoto `origin` são removidas do remoto.
- [ ] Nenhuma branch fora da lista aprovada é removida.
- [ ] O estado final é validado por listagem de branches e status Git.
- [ ] A task correspondente é marcada como concluída apenas após execução e verificação.

## 1.10 Rastreabilidade Funcional

| Origem | Artefato |
|---|---|
| Solicitação do usuário | Remover branches `dev`, `backup/dev-local-before-origin-sync-20260626`, `homolog` e `backup/homolog-before-dev-merge-20260626` local e remotamente |
| Task técnica | TASK-REQ-3090-001 |
| Design | Revisão do design vivo sem alteração arquitetural |
| DRI | Não aplicável, sem impacto de interface |
