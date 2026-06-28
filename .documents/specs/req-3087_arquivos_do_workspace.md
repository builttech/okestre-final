# REQ-3087 — Arquivos do Workspace

## 1. Specify — Especificação

### 1.1 Identificação e Metadados Básicos

**ID Único:** REQ-3087

**Título / Resumo:** Arquivos do Workspace

**Tipo:** Requisito funcional

**Módulo:** Workspace / Explorador de Arquivos / Editor

**Prioridade:** P2

**Status:** Especificado

**Solicitante:** Augusto Nascimento

**Responsável atual:** Equipe técnica GitIDE

**Release / Iteração:** A definir

**Esforço estimado:** A definir após decomposição automática/operacional pelo GitIDE

---

### 1.2 Contexto

O GitIDE precisa permitir que o usuário visualize, navegue e interaja com os arquivos do projeto ativo de forma segura, rastreável e integrada ao fluxo de desenvolvimento assistido por IA. A funcionalidade de **Arquivos do Workspace** é base para a experiência principal do produto, pois permite localizar arquivos, compreender a estrutura do projeto, abrir conteúdos, apoiar análises do agente IA e realizar alterações controladas quando autorizadas.

O projeto também exige um modelo operacional seguro: agentes de IA e usuários devem manipular arquivos por endpoints próprios do GitIDE, com validação de caminho, snapshots quando aplicável, rastreabilidade e status Git. O terminal integrado não deve substituir os endpoints de arquivo para leitura, criação, alteração ou exclusão direta, principalmente em fluxos conduzidos por agentes.

Este requisito define o comportamento funcional esperado para a área de arquivos do workspace, separando claramente o que o sistema deve fazer, quais regras devem ser respeitadas e quais validações demonstram que o requisito foi atendido.

---

### 1.3 Objetivo Funcional

Permitir que o usuário gerencie os arquivos do projeto ativo diretamente pelo GitIDE, com navegação clara, leitura segura, abertura de arquivos textuais, edição controlada, criação de novos arquivos em caminhos válidos, atualização da árvore de arquivos e integração com o status Git.

A funcionalidade deve garantir que todo acesso a arquivos permaneça dentro da raiz do projeto ativo, evitando path traversal, manipulação de diretórios bloqueados, exposição indevida de credenciais e alterações sem rastreabilidade.

---

### 1.4 Comportamento Esperado

O sistema deve disponibilizar uma área de **Arquivos do Workspace** que apresente os arquivos e diretórios permitidos do projeto ativo. A interface deve permitir ao usuário selecionar um arquivo, visualizar seu conteúdo quando suportado, editar o conteúdo quando aplicável e salvar a alteração por meio do endpoint de escrita do GitIDE.

O backend deve validar todo caminho recebido como relativo à raiz do projeto. Caminhos absolutos indevidos, referências com `..`, tentativas de acesso a diretórios bloqueados ou qualquer tentativa de escapar do workspace devem ser rejeitados.

Arquivos binários, muito grandes ou não suportados para edição textual devem receber tratamento específico, com mensagem clara ao usuário e sem tentativa de renderização insegura.

Sempre que uma alteração for feita em arquivo existente ou novo arquivo for criado, o sistema deve manter rastreabilidade por snapshot, histórico interno, status Git ou mecanismo equivalente disponível no GitIDE.

---

### 1.5 Histórias de Usuário

**HU-3087-001 — Navegação de arquivos**

Como usuário do GitIDE, eu quero visualizar a estrutura de arquivos do projeto ativo para entender rapidamente como o workspace está organizado.

**HU-3087-002 — Leitura de arquivo**

Como usuário do GitIDE, eu quero abrir arquivos textuais do projeto para consultar código, documentação, configuração e especificações sem sair da interface.

**HU-3087-003 — Edição controlada**

Como usuário do GitIDE, eu quero editar e salvar arquivos permitidos para realizar ajustes rastreáveis no workspace.

**HU-3087-004 — Apoio ao agente IA**

Como agente de IA conectado ao GitIDE, eu preciso ler apenas arquivos necessários e autorizados por meio dos endpoints do GitIDE para analisar contexto e propor alterações com segurança.

---

### 1.6 Escopo Funcional

#### Dentro do Escopo

- Listar arquivos e diretórios do projeto ativo.
- Exibir estrutura em árvore, lista hierárquica ou formato equivalente.
- Ignorar diretórios pesados, sensíveis ou desnecessários.
- Abrir arquivos textuais suportados para leitura.
- Editar e salvar arquivos quando permitido.
- Criar novos arquivos em caminhos válidos dentro do projeto.
- Atualizar a árvore após criação, alteração ou remoção autorizada.
- Exibir mensagens claras para erro de leitura, arquivo inexistente, permissão negada ou tipo não suportado.
- Integrar com status Git para indicar arquivos novos, modificados, removidos ou limpos quando disponível.
- Garantir que todas as operações ocorram dentro do projeto ativo.
- Usar endpoints próprios do GitIDE para leitura e escrita.
- Impedir manipulação de arquivos por comandos shell em fluxos conduzidos por agente IA.

#### Fora do Escopo

- Substituir completamente um editor de código profissional.
- Usar terminal como mecanismo padrão para leitura, escrita, criação, cópia, movimentação ou exclusão de arquivos.
- Editar arquivos binários diretamente em editor textual.
- Acessar caminhos absolutos fora do workspace.
- Manipular arquivos dentro de `.git`.
- Executar scripts automaticamente ao abrir ou salvar arquivos.
- Resolver conflitos Git automaticamente sem aprovação explícita.
- Sincronizar arquivos em tempo real com serviços externos.

---

### 1.7 Regras de Negócio

**RN-3087-001 — Restrição ao projeto ativo**

Todas as operações de arquivo devem ocorrer dentro do diretório raiz do projeto ativo selecionado no GitIDE.

**RN-3087-002 — Bloqueio de path traversal**

O sistema deve rejeitar caminhos que contenham `..`, caminhos absolutos indevidos, normalização que escape da raiz do workspace ou separadores usados para acessar área não autorizada.

**RN-3087-003 — Diretórios ignorados**

A listagem deve ignorar diretórios pesados, sensíveis ou desnecessários para navegação, incluindo pelo menos:

- `.git`
- `node_modules`
- `.venv`
- `venv`
- `__pycache__`
- `.pytest_cache`
- `dist`
- `build`
- `.next`
- `.turbo`

**RN-3087-004 — Arquivos binários ou não textuais**

Arquivos binários ou não textuais não devem ser carregados no editor textual. O sistema deve informar que o tipo de arquivo não é suportado para edição direta.

**RN-3087-005 — Preservação e rastreabilidade de alterações**

Ao editar um arquivo existente, o sistema deve preservar o conteúdo atualizado de forma rastreável, usando snapshots, registro interno, status Git ou mecanismo equivalente disponível no GitIDE.

**RN-3087-006 — Feedback obrigatório**

Toda ação de leitura, criação, salvamento, atualização de árvore ou erro deve apresentar feedback visual ao usuário.

**RN-3087-007 — Segurança de credenciais**

O sistema não deve expor tokens, senhas, chaves de API ou URLs autenticadas de forma desnecessária na interface, logs, mensagens de erro, histórico ou respostas do agente.

**RN-3087-008 — Integração com Git**

Sempre que possível, o sistema deve refletir se o arquivo está novo, modificado, removido ou limpo conforme o status Git do projeto.

**RN-3087-009 — Agente IA e endpoints autorizados**

O agente IA deve usar endpoints de arquivo do GitIDE para leitura e escrita. O agente não deve usar terminal para ler ou modificar arquivos com comandos como `cat`, `echo`, `sed`, `tee`, `touch`, `rm`, `cp`, `mv` ou equivalentes.

**RN-3087-010 — Aprovação antes de alteração**

Qualquer alteração de arquivo proposta por agente IA deve ser precedida de análise, plano, aprovação explícita do usuário, execução controlada e verificação.

---

### 1.8 Fluxos Funcionais

#### Fluxo 1 — Listar arquivos do workspace

1. O usuário seleciona ou abre um projeto no GitIDE.
2. O sistema identifica o projeto ativo.
3. O usuário acessa a área de arquivos do workspace.
4. O frontend solicita ao backend a listagem de arquivos permitidos.
5. O backend valida o projeto e ignora diretórios bloqueados.
6. O backend retorna caminhos relativos e metadados básicos.
7. A interface exibe a árvore ou lista de arquivos.
8. O usuário pode selecionar um arquivo para abertura.

#### Fluxo 2 — Abrir arquivo textual

1. O usuário seleciona um arquivo na árvore do workspace.
2. O sistema envia o caminho relativo ao endpoint de leitura.
3. O backend valida se o caminho pertence ao projeto ativo.
4. O backend lê o arquivo se ele for suportado.
5. A interface exibe o conteúdo em painel de leitura ou editor.
6. O nome e caminho relativo do arquivo ativo são exibidos.

#### Fluxo 3 — Editar e salvar arquivo

1. O usuário abre um arquivo editável.
2. O usuário altera o conteúdo no editor.
3. A interface marca que há alteração pendente.
4. O usuário aciona salvar.
5. O backend valida o caminho e grava o conteúdo pelo endpoint de escrita.
6. O sistema confirma o salvamento.
7. A árvore e o status visual são atualizados quando aplicável.
8. O status Git pode indicar o arquivo como modificado ou novo.

#### Fluxo 4 — Criar novo arquivo

1. O usuário solicita criação de novo arquivo.
2. O sistema recebe nome e caminho relativo de destino.
3. O backend valida extensão, caminho e diretório permitido.
4. O arquivo é criado com conteúdo inicial quando aplicável.
5. A árvore é atualizada.
6. O arquivo recém-criado fica disponível para abertura ou edição.

#### Fluxo 5 — Caminho inválido ou tentativa de acesso externo

1. Uma requisição tenta usar `..`, caminho absoluto indevido ou diretório bloqueado.
2. O backend rejeita a operação.
3. Nenhum arquivo é lido, criado ou alterado.
4. A interface informa que o caminho é inválido ou não permitido.

#### Fluxo 6 — Arquivo não suportado

1. O usuário seleciona arquivo binário ou não textual.
2. O sistema identifica que não é seguro abrir no editor textual.
3. A interface informa que o arquivo não é suportado.
4. Nenhuma modificação é feita.

---

### 1.9 Critérios de Aceite

- [ ] Dado que existe um projeto ativo, quando o usuário abre a área de arquivos, então o sistema lista apenas arquivos e diretórios permitidos do workspace.
- [ ] Dado que o projeto contém diretórios ignorados, quando a árvore é carregada, então esses diretórios não aparecem na listagem principal.
- [ ] Dado que o usuário seleciona um arquivo textual válido, quando solicita abertura, então o conteúdo é exibido no editor ou painel de leitura.
- [ ] Dado que o usuário seleciona um arquivo inexistente, quando o sistema tenta abrir, então uma mensagem de erro clara é exibida.
- [ ] Dado que o usuário seleciona arquivo binário ou não textual, quando tenta abrir no editor, então o sistema informa que o tipo não é suportado.
- [ ] Dado que o usuário edita um arquivo permitido, quando salva, então o conteúdo atualizado é gravado no workspace por endpoint do GitIDE.
- [ ] Dado que um arquivo é criado ou salvo, quando o status Git é atualizado, então o arquivo aparece como novo ou modificado quando aplicável.
- [ ] Dado que o usuário informa caminho inválido com `..`, quando tenta criar, abrir ou salvar arquivo, então o backend bloqueia a operação.
- [ ] Dado que o usuário cria arquivo em caminho válido, quando a operação termina, então a árvore é atualizada e o arquivo aparece na lista.
- [ ] Dado que ocorre erro de permissão ou leitura, quando a operação falha, então o sistema mostra mensagem compreensível sem expor credenciais.
- [ ] Dado que o agente IA precisa analisar um arquivo, quando autorizado pela tarefa, então a leitura ocorre pelo endpoint de arquivos do GitIDE.
- [ ] Dado que o agente IA precisa modificar arquivo, quando não há aprovação explícita, então nenhuma alteração é realizada.
- [ ] Dado que o agente IA executa uma alteração aprovada, quando a execução termina, então o status Git ou mecanismo equivalente permite auditar o arquivo afetado.

---

### 1.10 Rastreabilidade Funcional

**Links Ascendentes:**

- TAP: `.documents/project-charter.md`
- Produto: GitIDE
- Módulo: Workspace / Arquivos

**Requisitos relacionados:**

- REQ-3088 — Terminal Integrado
- Requisitos futuros de Git/status do workspace
- Requisitos futuros de agente IA e edição assistida
- Requisitos futuros de documentação e SDD

**Casos de teste funcionais sugeridos:**

- CT-3087-001 — Listar arquivos em projeto válido.
- CT-3087-002 — Ignorar diretórios bloqueados.
- CT-3087-003 — Abrir arquivo textual.
- CT-3087-004 — Bloquear arquivo inexistente.
- CT-3087-005 — Bloquear path traversal.
- CT-3087-006 — Salvar arquivo editado por endpoint.
- CT-3087-007 — Criar novo arquivo válido.
- CT-3087-008 — Validar status Git após alteração.
- CT-3087-009 — Impedir manipulação de arquivo pelo agente via terminal.

---

## 2. Design — Planejamento

### 2.1 Arquitetura Proposta

A funcionalidade deve utilizar a arquitetura existente do GitIDE, com frontend em HTML/CSS/JavaScript e backend responsável por validar projeto, caminhos e operações de arquivo. O frontend não deve acessar o sistema de arquivos diretamente; toda operação deve passar pelos endpoints de projetos/arquivos.

O backend deve atuar como camada de segurança, normalizando caminhos relativos, impedindo acesso fora da raiz do projeto, filtrando diretórios ignorados e retornando respostas estruturadas para sucesso, erro e validação.

O agente IA deve seguir o mesmo contrato técnico do usuário: leitura por endpoint, escrita por endpoint após aprovação, e validação posterior por status Git ou leitura do arquivo alterado.

---

### 2.2 Componentes Impactados

- Cadastro e seleção de projetos/workspaces.
- Endpoint de listagem de arquivos.
- Endpoint de leitura de arquivos.
- Endpoint de escrita/criação de arquivos.
- Interface de árvore/lista de arquivos.
- Editor ou painel de conteúdo.
- Sistema de snapshots/backup local, quando disponível.
- Módulo de status Git.
- Agente IA conectado ao GitIDE.
- Camada de segurança de caminhos e diretórios bloqueados.

---

### 2.3 Fluxo Técnico de Alto Nível

1. O frontend obtém o `project_id` ativo.
2. O frontend chama o endpoint de listagem de arquivos.
3. O backend resolve o projeto e valida sua raiz.
4. O backend percorre diretórios permitidos, aplicando filtros de ignorados.
5. O frontend renderiza os arquivos retornados.
6. Ao abrir arquivo, o frontend chama o endpoint de leitura com `filepath` relativo.
7. O backend valida e retorna conteúdo paginado quando necessário.
8. Ao salvar, o frontend envia `filepath` e `content` ao endpoint de escrita.
9. O backend cria snapshot quando aplicável e grava o conteúdo.
10. O frontend atualiza estado visual e pode solicitar status Git.

---

### 2.4 APIs / Endpoints

#### GET `/api/projects/{project_id}/files`

Lista arquivos e diretórios permitidos do projeto ativo.

**Resposta esperada:**

```json
{
  "status": "success",
  "files": [
    {
      "path": "gitide_server/main.py",
      "size": 44204,
      "last_modified": "2026-06-26T22:29:40"
    }
  ]
}
```

#### GET `/api/projects/{project_id}/files/read?filepath={path}`

Lê o conteúdo de arquivo textual do projeto.

**Regras técnicas:**

- `filepath` deve ser relativo à raiz do projeto.
- Deve suportar paginação por linhas quando necessário.
- Deve rejeitar caminhos inválidos ou fora do workspace.
- Deve retornar erro controlado para arquivo inexistente ou não suportado.

#### POST `/api/projects/{project_id}/files/write`

Cria ou atualiza arquivo textual dentro do projeto.

**Payload esperado:**

```json
{
  "filepath": "caminho/relativo/arquivo.md",
  "content": "conteúdo atualizado"
}
```

**Regras técnicas:**

- Validar caminho relativo.
- Bloquear path traversal.
- Criar snapshot quando suportado.
- Preservar codificação textual quando possível.
- Retornar status claro de criação ou atualização.

#### PATCH `/api/projects/{project_id}/files/patch`

Aplica alteração cirúrgica por substituição de trecho exato quando a mudança puder ser representada como patch.

**Regras técnicas:**

- Exigir trecho alvo exato.
- Evitar substituições ambíguas sem confirmação.
- Gerar snapshot quando suportado.
- Ser preferido para pequenas alterações em arquivos grandes.

---

### 2.5 Dados, Banco e Integrações

**Banco de dados:** Não há dependência direta obrigatória para este requisito.

**Git:** Recomendado para exibir arquivos novos, modificados, removidos ou limpos.

**Agente IA:** Deve operar exclusivamente por endpoints de leitura/escrita/patch para manipulação de arquivos, com aprovação prévia antes de alterações.

**Documentação / SDD:** Arquivos Markdown em `.documents/specs` devem ser tratados como artefatos versionáveis e manipulados pelos mesmos contratos de segurança.

**Terminal Integrado:** Pode ser usado para validações operacionais aprovadas, como testes, builds ou `git status`, mas não como mecanismo de manipulação direta de arquivos.

---

### 2.6 Permissões e Segurança

- Validar `project_id` antes de qualquer operação.
- Normalizar caminho antes de acessar o arquivo.
- Rejeitar acesso a diretórios bloqueados.
- Rejeitar path traversal.
- Evitar exposição de credenciais em mensagens e logs.
- Usar snapshots ou backup local antes de sobrescrever arquivos, quando disponível.
- Exigir aprovação explícita para alterações realizadas por agente IA.
- Registrar evidências de validação após alteração.

---

### 2.7 Riscos Técnicos

- Projetos grandes podem tornar a listagem lenta sem filtros adequados.
- Falhas de validação de caminho podem permitir acesso fora do workspace.
- Arquivos grandes podem afetar performance do editor.
- Alterações simultâneas por ferramenta externa e GitIDE podem causar sobrescrita.
- Arquivos sensíveis, como `.env`, exigem tratamento cuidadoso para evitar exposição indevida.
- Divergência entre status Git visual e estado real pode confundir o usuário se não houver atualização adequada.

---

### 2.8 Estratégia de Validação

- Validar listagem de projeto com diretórios ignorados.
- Validar leitura de arquivos Markdown, Python, JavaScript, CSS e HTML.
- Validar bloqueio de `../arquivo` e caminhos absolutos fora do projeto.
- Validar criação de arquivo em diretório permitido.
- Validar salvamento de arquivo textual simples.
- Validar que status Git reflete arquivo novo ou modificado.
- Validar que arquivo binário não é aberto como texto.
- Validar que mensagens de erro não expõem credenciais.

---

## 3. Task List — Tarefas

A lista abaixo representa a decomposição operacional rastreável do requisito **REQ-3087 — Arquivos do Workspace**. Cada tarefa deve ser executada individualmente pelo GitIDE ou por agente/programador autorizado, mantendo separação entre requisito funcional, planejamento técnico e implementação.

- [ ] TASK-REQ-3087-001: Revisar a implementação atual do endpoint de listagem de arquivos do workspace.
- [ ] TASK-REQ-3087-002: Validar que a listagem de arquivos opera sempre dentro da raiz do projeto ativo.
- [ ] TASK-REQ-3087-003: Confirmar e padronizar a lista de diretórios ignorados pelo backend.
- [ ] TASK-REQ-3087-004: Revisar a proteção contra path traversal nos endpoints de listagem, leitura, escrita e patch.
- [ ] TASK-REQ-3087-005: Validar leitura paginada de arquivos grandes ou com muitas linhas.
- [ ] TASK-REQ-3087-006: Validar tratamento de arquivos binários ou não textuais.
- [ ] TASK-REQ-3087-007: Revisar o fluxo de abertura de arquivos textuais na interface.
- [ ] TASK-REQ-3087-008: Revisar o fluxo de edição e salvamento por endpoint de escrita do GitIDE.
- [ ] TASK-REQ-3087-009: Revisar o uso do endpoint de patch para alterações cirúrgicas em arquivos grandes.
- [ ] TASK-REQ-3087-010: Garantir que alterações em arquivos gerem snapshot, backup local ou rastreabilidade equivalente quando suportado.
- [ ] TASK-REQ-3087-011: Integrar ou validar indicadores de status Git para arquivos novos, modificados, removidos ou limpos.
- [ ] TASK-REQ-3087-012: Melhorar mensagens de erro para arquivo inexistente, permissão negada, caminho inválido e tipo não suportado.
- [ ] TASK-REQ-3087-013: Validar que mensagens e logs não exponham tokens, senhas, chaves de API ou URLs autenticadas.
- [ ] TASK-REQ-3087-014: Confirmar que agentes IA usam endpoints autorizados para ler, escrever ou aplicar patch em arquivos.
- [ ] TASK-REQ-3087-015: Bloquear uso do terminal como mecanismo de manipulação direta de arquivos em fluxos conduzidos por agente IA.
- [ ] TASK-REQ-3087-016: Validar atualização da árvore de arquivos após criação, alteração ou remoção autorizada.
- [ ] TASK-REQ-3087-017: Validar comportamento da interface em projetos com muitos arquivos e diretórios ignorados.
- [ ] TASK-REQ-3087-018: Criar ou atualizar testes automatizados para listagem, leitura, escrita, patch e bloqueios de segurança.
- [ ] TASK-REQ-3087-019: Executar validações técnicas aprovadas e registrar evidências de resultado.
- [ ] TASK-REQ-3087-020: Atualizar rastreabilidade com commits, pull requests, validações e observações de entrega após execução das tarefas.

As tarefas acima não substituem os critérios de aceite da etapa **Specify**. Cada item deve ser tratado como unidade de execução técnica, com plano próprio, aprovação explícita e verificação antes de ser marcado como concluído.

---

## 4. Execute — Implementação

Esta etapa não deve ser preenchida antecipadamente.

Ela deve ser usada somente quando uma tarefa específica do REQ-3087 for selecionada para execução por agente ou programador, seguindo o ciclo:

**Percepção → Planejamento → Aprovação → Execução → Verificação**

A execução deve ser mínima, rastreável, aprovada pelo usuário e validada por testes, build, leitura do arquivo alterado, status Git ou outro mecanismo aplicável.
