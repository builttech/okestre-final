# REQ-3089 — Harness Engineering com documentos vivos por projeto

## 1. Specify — Especificação

### 1.1 Identificação e Metadados Básicos

**ID Único:** REQ-3089

**Título / Resumo:** Harness Engineering com documentos vivos por projeto

**Tipo:** Requisito funcional

**Módulo:** Harness Engineering / Spec-Driven Development / Documentos do Projeto

**Prioridade:** P1

**Status:** Especificado — revisado após correção arquitetural

**Solicitante:** Augusto Nascimento

**Responsável atual:** Equipe técnica GitIDE

**Release / Iteração:** A definir

**Esforço estimado:** A definir após decomposição técnica final

---

### 1.2 Contexto

O Harness Engineering do GitIDE atualmente centraliza cada requisito funcional em um arquivo Markdown dentro de `.documents/specs/*.md`, contendo seções de Specify, Design, DRI, Task List e Execute no mesmo artefato.

Após revisão de arquitetura, a estrutura correta deve ser organizada por **documentos vivos do projeto**, e não por uma pasta independente para cada requisito com todos os arquivos de etapa.

Um projeto pode possuir múltiplos REQs. Portanto, a etapa **Specify** deve permitir múltiplos arquivos de requisito, enquanto **Design**, **DRI** e **Task List** devem ser documentos únicos e vivos do projeto.

A estrutura alvo é:

```text
.documents/
  spec/
    REQ-3089.md
    REQ-3090.md
    REQ-3091.md
  design/
    design.md
  dri/
    dri.md
  task/
    task.md
```

A pasta real adotada pelo projeto é `.documents`. Referências a `.document` devem ser interpretadas como `.documents`, preservando o padrão atual do GitIDE.

A etapa **Execute** permanece como fluxo operacional da interface Harness Engineering: ela deve ser montada a partir de uma task selecionada e dos documentos vivos de referência. Nesta revisão, Execute não é definido como arquivo obrigatório da estrutura base do projeto, salvo se uma evolução futura criar persistência própria.

---

### 1.3 Objetivo Funcional

Permitir que o Harness Engineering organize a documentação do projeto em arquivos Markdown separados por responsabilidade:

- múltiplos arquivos de requisitos funcionais em `.documents/spec/`, um arquivo por REQ;
- um documento vivo de design em `.documents/design/design.md`;
- um documento vivo de DRI em `.documents/dri/dri.md`;
- um documento vivo de tarefas em `.documents/task/task.md`.

O sistema deve permitir listar, criar, abrir, editar e salvar REQs individuais na etapa Specify, além de carregar e salvar os documentos vivos de Design, DRI e Task List.

O sistema também deve preservar compatibilidade gradual com specs legadas existentes em `.documents/specs/*.md`, até que uma migração explícita seja planejada.

---

### 1.4 Comportamento Esperado

Ao acessar o Harness Engineering, o sistema deve garantir ou reconhecer a estrutura documental do projeto:

```text
.documents/spec/
.documents/design/design.md
.documents/dri/dri.md
.documents/task/task.md
```

Na etapa **Specify**, a interface deve listar múltiplos REQs existentes em `.documents/spec/`. Cada REQ deve ser um arquivo Markdown próprio, como `REQ-3089.md`, `REQ-3090.md` ou nome equivalente seguro.

Ao criar um novo REQ, o sistema deve criar somente o arquivo do requisito dentro de `.documents/spec/`, sem criar uma pasta completa para aquele REQ.

Na etapa **Design**, a interface deve carregar e salvar o documento único `.documents/design/design.md`, tratado como documento vivo do projeto.

Na etapa **DRI**, a interface deve carregar e salvar o documento único `.documents/dri/dri.md`, tratado como documento vivo do projeto.

Na etapa **Task List**, a interface deve carregar e salvar o documento único `.documents/task/task.md`. As tarefas devem continuar usando checklists Markdown rastreáveis, por exemplo:

```text
- [x] TASK-REQ-3089-001: Implementar estrutura documental do Harness Engineering.
```

A etapa **Execute** deve ser preenchida somente quando uma task específica for selecionada. O conteúdo de Execute deve usar como referência o REQ selecionado em `.documents/spec/`, o documento vivo de Design, o documento vivo de DRI e a task escolhida em `.documents/task/task.md`.

---

### 1.5 Histórias de Usuário

**HU-3089-001 — Múltiplos REQs em Specify**

Como usuário do GitIDE, eu quero criar e editar múltiplos arquivos de REQ em `.documents/spec/` para organizar os requisitos funcionais do projeto de forma individual.

**HU-3089-002 — Design vivo do projeto**

Como usuário do GitIDE, eu quero manter um único `design.md` do projeto para consolidar decisões técnicas e arquitetura de forma evolutiva.

**HU-3089-003 — DRI vivo do projeto**

Como usuário do GitIDE, eu quero manter um único `dri.md` do projeto para consolidar requisitos de interface de forma evolutiva.

**HU-3089-004 — Task List viva do projeto**

Como usuário do GitIDE, eu quero manter um único `task.md` do projeto para centralizar tarefas rastreáveis de múltiplos REQs.

**HU-3089-005 — Execute derivado da task selecionada**

Como agente IA ou programador, eu quero que a etapa Execute seja montada a partir da task escolhida e dos documentos vivos de referência, evitando execução fora de escopo.

**HU-3089-006 — Compatibilidade com documentação antiga**

Como usuário do GitIDE, eu quero continuar acessando specs antigas em `.documents/specs/*.md` durante a transição para não perder documentação existente.

---

### 1.6 Escopo Funcional

#### Dentro do Escopo

- Criar ou reconhecer a pasta `.documents/spec/` para múltiplos arquivos de REQ.
- Criar ou reconhecer `.documents/design/design.md` como documento vivo único do projeto.
- Criar ou reconhecer `.documents/dri/dri.md` como documento vivo único do projeto.
- Criar ou reconhecer `.documents/task/task.md` como documento vivo único do projeto.
- Listar REQs a partir de `.documents/spec/`.
- Criar novo REQ como arquivo individual em `.documents/spec/`.
- Carregar e salvar o REQ selecionado na etapa Specify.
- Carregar e salvar `design.md` na etapa Design.
- Carregar e salvar `dri.md` na etapa DRI.
- Carregar e salvar `task.md` na etapa Task List.
- Extrair e atualizar checkboxes de tarefas a partir de `.documents/task/task.md`.
- Montar Execute a partir de uma task selecionada, do REQ selecionado e dos documentos vivos do projeto.
- Ajustar textos da interface para refletir a nova estrutura documental.
- Preservar compatibilidade gradual com `.documents/specs/*.md`.
- Preservar o padrão visual dark, premium e glassmorphic do GitIDE.

#### Fora do Escopo

- Criar uma pasta independente por REQ contendo `spec.md`, `design.md`, `dri.md`, `task.md` e `execute.md`.
- Migrar automaticamente todos os arquivos legados sem ação explícita.
- Remover suporte imediato a `.documents/specs/*.md`.
- Criar editor rico ou visual diff avançado.
- Alterar o Project Charter/TAP.
- Executar tasks técnicas sem validação de REQ, escolha explícita da task e aprovação do plano.

---

### 1.7 Regras de Negócio

**RN-3089-001 — Pasta documental raiz**

A estrutura deve ser criada dentro de `.documents/`, preservando a pasta documental padrão do GitIDE.

**RN-3089-002 — Specify com múltiplos REQs**

A pasta `.documents/spec/` pode conter múltiplos arquivos de requisito. Cada arquivo representa um REQ funcional individual.

**RN-3089-003 — Design único por projeto**

O arquivo `.documents/design/design.md` é único por projeto e deve funcionar como documento vivo de arquitetura e planejamento técnico.

**RN-3089-004 — DRI único por projeto**

O arquivo `.documents/dri/dri.md` é único por projeto e deve funcionar como documento vivo de requisitos de interface.

**RN-3089-005 — Task List única por projeto**

O arquivo `.documents/task/task.md` é único por projeto e deve concentrar tarefas rastreáveis relacionadas a um ou mais REQs.

**RN-3089-006 — Separação de responsabilidades**

Arquivos em `.documents/spec/` descrevem o que o sistema deve fazer. `design.md` descreve como o sistema será planejado tecnicamente. `dri.md` descreve interface. `task.md` descreve tarefas técnicas rastreáveis.

**RN-3089-007 — Execute derivado**

Execute não deve ser preenchido antecipadamente. Ele deve ser montado somente a partir de uma task escolhida e do contexto dos documentos vivos.

**RN-3089-008 — Compatibilidade legada**

Specs existentes em `.documents/specs/*.md` devem continuar acessíveis durante a transição.

**RN-3089-009 — Segurança de caminho**

Endpoints Harness Engineering devem rejeitar path traversal, caminhos absolutos e nomes que escapem das pastas autorizadas de `.documents/`.

**RN-3089-010 — Rastreabilidade**

A interface e os endpoints devem retornar metadados suficientes para identificar REQ, arquivo de origem, tipo documental e data de modificação.

---

### 1.8 Fluxos Funcionais

#### Fluxo 1 — Inicializar estrutura Harness Engineering

1. O usuário abre o Harness Engineering.
2. O sistema verifica se existem as pastas `.documents/spec/`, `.documents/design/`, `.documents/dri/` e `.documents/task/`.
3. Se não existirem, o sistema pode criá-las em fluxo autorizado de criação/salvamento.
4. O sistema carrega REQs disponíveis e documentos vivos existentes.

#### Fluxo 2 — Criar novo REQ

1. O usuário solicita criar novo requisito.
2. O sistema gera ou recebe um ID de requisito e título.
3. O sistema cria um arquivo seguro em `.documents/spec/`, por exemplo `REQ-3089.md`.
4. O arquivo recebe template inicial de Specify.
5. O novo REQ aparece na lista de requisitos.
6. A interface abre o REQ na etapa Specify.

#### Fluxo 3 — Selecionar REQ em Specify

1. O usuário seleciona um REQ da lista.
2. O sistema lê o arquivo correspondente em `.documents/spec/`.
3. A interface exibe o conteúdo no editor Specify.
4. O cabeçalho exibe ID, título e caminho de origem.

#### Fluxo 4 — Salvar Specify

1. O usuário edita o REQ selecionado.
2. O usuário aciona salvar na etapa Specify.
3. O backend valida caminho e grava o arquivo do REQ em `.documents/spec/`.
4. O sistema confirma o salvamento.

#### Fluxo 5 — Carregar e salvar Design

1. O usuário abre a etapa Design.
2. O sistema carrega `.documents/design/design.md`.
3. O usuário edita o documento vivo.
4. O sistema salva o mesmo arquivo após validação.

#### Fluxo 6 — Carregar e salvar DRI

1. O usuário abre a etapa DRI.
2. O sistema carrega `.documents/dri/dri.md`.
3. O usuário edita o documento vivo.
4. O sistema salva o mesmo arquivo após validação.

#### Fluxo 7 — Carregar Task List

1. O usuário abre a etapa Task List.
2. O sistema lê `.documents/task/task.md`.
3. O sistema extrai tarefas Markdown `- [ ]` ou `- [x]`.
4. A interface renderiza checklist e progresso.
5. Ao marcar ou desmarcar uma tarefa, o backend atualiza `.documents/task/task.md`.

#### Fluxo 8 — Enviar task para Execute

1. O usuário seleciona uma task como executar.
2. O sistema identifica o REQ relacionado pela nomenclatura da task quando possível.
3. O sistema monta instruções usando o REQ selecionado ou relacionado, `design.md`, `dri.md` e `task.md`.
4. A aba Execute exibe instruções para execução supervisionada.
5. A implementação só pode ocorrer após plano e aprovação explícita.

---

### 1.9 Critérios de Aceite

- [ ] Dado que o Harness Engineering é inicializado, quando a estrutura documental é necessária, então o sistema reconhece ou prepara `.documents/spec/`, `.documents/design/`, `.documents/dri/` e `.documents/task/`.
- [ ] Dado que o usuário cria um novo REQ, quando a operação termina, então existe um arquivo próprio do requisito em `.documents/spec/`.
- [ ] Dado que existem múltiplos arquivos em `.documents/spec/`, quando a lista de requisitos é carregada, então todos os REQs válidos aparecem na interface.
- [ ] Dado que o usuário seleciona um REQ, quando a etapa Specify é aberta, então o conteúdo do arquivo correspondente é exibido.
- [ ] Dado que o usuário salva Specify, quando a operação termina, então somente o arquivo do REQ selecionado é atualizado.
- [ ] Dado que o usuário abre Design, quando o documento existe, então `.documents/design/design.md` é carregado.
- [ ] Dado que o usuário salva Design, quando a operação termina, então `.documents/design/design.md` é atualizado.
- [ ] Dado que o usuário abre DRI, quando o documento existe, então `.documents/dri/dri.md` é carregado.
- [ ] Dado que o usuário salva DRI, quando a operação termina, então `.documents/dri/dri.md` é atualizado.
- [ ] Dado que o usuário abre Task List, quando o documento existe, então as tarefas são lidas de `.documents/task/task.md`.
- [ ] Dado que o usuário marca uma task, quando o backend atualiza o checklist, então o checkbox correspondente é alterado em `.documents/task/task.md`.
- [ ] Dado que o usuário escolhe uma task para Execute, quando a aba Execute é aberta, então as instruções são montadas a partir do REQ, Design, DRI e task selecionada.
- [ ] Dado que existe uma spec legada em `.documents/specs/*.md`, quando a listagem de compatibilidade é carregada, então ela continua acessível.
- [ ] Dado que uma requisição tenta usar `..`, caminho absoluto ou separador inválido, quando o backend valida o caminho, então a operação é rejeitada.
- [ ] Dado que a interface exibe textos explicativos do Harness Engineering, quando a nova estrutura estiver ativa, então ela deve refletir a estrutura com `spec/`, `design/`, `dri/` e `task/`.

---

### 1.10 Rastreabilidade Funcional

**Links Ascendentes:**

- TAP: `.documents/project-charter.md`
- Produto: GitIDE
- Módulo: Harness Engineering / Spec-Driven Development

**Requisitos relacionados:**

- REQ-3087 — Arquivos do Workspace
- REQ-3088 — Terminal Integrado
- Requisitos futuros de migração, agente IA e documentação técnica

**Casos de teste funcionais sugeridos:**

- CT-3089-001 — Inicializar/reconhecer estrutura `.documents/spec`, `.documents/design`, `.documents/dri`, `.documents/task`.
- CT-3089-002 — Criar novo REQ como arquivo em `.documents/spec/`.
- CT-3089-003 — Listar múltiplos REQs de `.documents/spec/`.
- CT-3089-004 — Abrir e salvar um REQ individual em Specify.
- CT-3089-005 — Abrir e salvar `.documents/design/design.md`.
- CT-3089-006 — Abrir e salvar `.documents/dri/dri.md`.
- CT-3089-007 — Ler e atualizar tarefas em `.documents/task/task.md`.
- CT-3089-008 — Montar Execute a partir da task selecionada e documentos vivos.
- CT-3089-009 — Bloquear path traversal.
- CT-3089-010 — Preservar acesso a specs legadas.

---

## 2. Design — Planejamento

### 2.1 Arquitetura Proposta

A funcionalidade deve evoluir o Harness Engineering para operar sobre uma estrutura documental viva por projeto:

```text
.documents/
  spec/
    REQ-xxxx.md
  design/
    design.md
  dri/
    dri.md
  task/
    task.md
```

O backend deve fornecer contratos para listar REQs, ler e salvar um REQ específico, ler e salvar documentos vivos de projeto e extrair/atualizar tarefas em `task.md`.

A compatibilidade com `.documents/specs/*.md` deve ser mantida temporariamente como modo legado.

---

### 2.2 Componentes Impactados

- Endpoints SDD/Harness Engineering em `gitide_server/main.py`.
- Listagem de requisitos no frontend.
- Estado frontend `sddState` em `gitide_server/static/app.js`.
- Abertura e salvamento de Specify, Design, DRI e Task List.
- Montagem da etapa Execute.
- Textos da interface em `gitide_server/static/index.html`.
- Estilos apenas se forem necessários para badges/indicadores, mantendo design atual.
- Testes e validações do fluxo Harness Engineering.

---

### 2.3 Estrutura de Arquivos Proposta

```text
.documents/
  project-charter.md
  spec/
    REQ-3089.md
    REQ-3090.md
  design/
    design.md
  dri/
    dri.md
  task/
    task.md
```

### 2.4 Contrato de Dados Sugerido

A listagem de REQs deve retornar arquivos encontrados em `.documents/spec/`:

```json
{
  "id": "REQ-3089",
  "filename": "REQ-3089.md",
  "title": "REQ-3089 — Harness Engineering com documentos vivos por projeto",
  "storage_type": "project_spec_file",
  "filepath": ".documents/spec/REQ-3089.md",
  "modified_at": "2026-06-28T00:00:00"
}
```

O carregamento do workspace Harness pode retornar também os documentos vivos:

```json
{
  "status": "success",
  "active_spec": {
    "filename": "REQ-3089.md",
    "content": "..."
  },
  "project_documents": {
    "design": "...",
    "dri": "...",
    "task": "..."
  }
}
```

Para specs legadas:

```json
{
  "id": "req-3087_arquivos_do_workspace.md",
  "filename": "req-3087_arquivos_do_workspace.md",
  "title": "REQ-3087 — Arquivos do Workspace",
  "storage_type": "legacy_markdown",
  "filepath": ".documents/specs/req-3087_arquivos_do_workspace.md"
}
```

---

### 2.5 APIs / Endpoints

#### GET `/api/projects/{project_id}/sdd/specs`

Deve listar REQs em `.documents/spec/` e, durante a transição, specs legadas em `.documents/specs/*.md`.

#### GET `/api/projects/{project_id}/sdd/specs/{filename}`

Deve retornar o conteúdo de um REQ individual de `.documents/spec/` ou, em modo legado, o conteúdo de `.documents/specs/*.md`.

#### POST `/api/projects/{project_id}/sdd/specs`

Deve criar ou salvar um REQ individual em `.documents/spec/`, mantendo compatibilidade controlada com o formato legado quando necessário.

#### GET `/api/projects/{project_id}/sdd/project-documents/{kind}`

Endpoint sugerido para ler documentos vivos do projeto. `kind` deve aceitar apenas `design`, `dri` e `task`.

#### POST `/api/projects/{project_id}/sdd/project-documents/{kind}`

Endpoint sugerido para salvar documentos vivos do projeto. `kind` deve aceitar apenas `design`, `dri` e `task`.

#### GET `/api/projects/{project_id}/sdd/tasks/criteria`

Endpoint sugerido para extrair tarefas de `.documents/task/task.md`.

#### POST `/api/projects/{project_id}/sdd/tasks/criteria`

Endpoint sugerido para atualizar checkboxes em `.documents/task/task.md`.

---

### 2.6 Dados, Banco e Integrações

**Banco de dados:** Não há necessidade inicial de nova tabela. Os documentos permanecem como arquivos Markdown versionáveis.

**Git:** A estrutura documental deve aparecer naturalmente no status Git como arquivos novos ou modificados.

**Agente IA:** O agente deve usar endpoints do GitIDE e respeitar REQ validado, task escolhida, plano aprovado, execução e verificação.

**Documentos Word:** Não há mudança direta no fluxo de geração de Word.

---

### 2.7 Segurança e Validações Técnicas

- Validar `project_id`.
- Validar nomes de REQ contra `..`, `/`, `\\`, caminhos absolutos e caracteres perigosos.
- Validar `kind` de documento vivo contra allowlist: `design`, `dri`, `task`.
- Resolver paths sempre dentro de `.documents/`.
- Não permitir escrita fora do workspace.
- Evitar exposição de credenciais em erros.
- Manter mensagens claras para arquivo ausente, documento inválido e REQ inexistente.

---

### 2.8 Estratégia de Compatibilidade

A implementação deve tratar `.documents/spec/REQ-xxxx.md` como novo modo principal e `.documents/specs/*.md` como modo legado.

A listagem pode mostrar ambos enquanto a migração não existir.

Migração automática de specs antigas para a nova estrutura deve ser evolução futura, não parte obrigatória desta primeira implementação.

---

### 2.9 Estratégia de Validação

- Validar criação/reconhecimento das pastas `.documents/spec`, `.documents/design`, `.documents/dri`, `.documents/task`.
- Criar novo REQ e confirmar arquivo em `.documents/spec/`.
- Criar ou carregar `design.md`, `dri.md` e `task.md`.
- Salvar cada documento no caminho correto.
- Validar extração e atualização de checkboxes em `task.md`.
- Validar listagem de specs legadas.
- Validar bloqueios de caminho inválido.
- Rodar testes ou validações aprovadas.
- Rodar `git status` após implementação aprovada para auditoria.

---

## 3. DRI — Documento de Requisito de Interface

### RI-REQ-3089-001 — Harness Engineering com documentos vivos por projeto

### 1. Identificação da Interface

| Campo | Valor |
| --- | --- |
| Código | RI-REQ-3089-001 |
| Nome da interface | Harness Engineering |
| Módulo | Spec-Driven Development / Requisitos e documentos vivos |
| RF relacionado | REQ-3089 — Harness Engineering com documentos vivos por projeto |
| SubRFs relacionados | RF-3089-001 Specify com múltiplos REQs; RF-3089-002 Design vivo; RF-3089-003 DRI vivo; RF-3089-004 Task List viva; RF-3089-005 Execute derivado |
| Tipo de interface | Página com lista de REQs, workspace por abas, editores Markdown e checklist |
| Perfil de usuário | Product owner, desenvolvedor, operador técnico e agente IA supervisionado |
| Dispositivo prioritário | Desktop responsivo |
| Objetivo da tela | Permitir gerenciar múltiplos REQs e documentos vivos do projeto no Harness Engineering. |

---

### 2. Objetivo da Interface

A interface deve comunicar que Specify trabalha com múltiplos arquivos de REQ, enquanto Design, DRI e Task List são documentos únicos e vivos do projeto. O usuário deve navegar pelas etapas com clareza sobre qual arquivo está editando.

---

### 3. Contexto de Uso

| Campo | Valor |
| --- | --- |
| Quem usa | Usuário técnico, product owner, desenvolvedor e agente IA supervisionado. |
| Quando usa | Durante criação, refinamento, planejamento e execução de requisitos funcionais. |
| Por que usa | Para organizar requisitos e documentos de engenharia com separação clara e rastreabilidade. |
| Gatilho de acesso | Clique na aba lateral Harness Engineering. |
| Resultado esperado | O usuário cria/seleciona REQs e edita documentos vivos do projeto. |

---

### 4. Arquitetura da Informação

| Ordem | Seção | Objetivo | Tipo de componente |
| --- | --- | --- | --- |
| 1 | Header Harness Engineering | Identificar área e alternar Project Charter / Functional Specs. | Header com navegação superior |
| 2 | Lista de REQs | Exibir arquivos de `.documents/spec/` e legados quando aplicável. | Sidebar/lista |
| 3 | Cabeçalho do contexto ativo | Mostrar REQ selecionado e caminhos documentais. | Header com badges |
| 4 | Aba Specify | Editar arquivo do REQ selecionado. | Textarea Markdown |
| 5 | Aba Design | Editar `.documents/design/design.md`. | Textarea Markdown |
| 6 | Aba DRI | Editar `.documents/dri/dri.md`. | Textarea Markdown |
| 7 | Aba Task List | Renderizar e atualizar `.documents/task/task.md`. | Checklist com progresso |
| 8 | Aba Execute | Montar instruções a partir da task selecionada. | Textarea Markdown |

---

### 5. Mapa de Componentes

| Componente | Tipo | Obrigatório | Editável | Comportamento esperado |
| --- | --- | --- | --- | --- |
| Lista de REQs | Lista lateral | Sim | Não | Exibe múltiplos REQs de `.documents/spec/` e legados. |
| Badge de origem | Badge | Sim | Não | Indica `.documents/spec/`, documento vivo ou legado. |
| Aba Specify | Tab | Sim | Não | Mostra editor do REQ selecionado. |
| Botão Salvar Specify | Botão | Sim | Não | Salva somente o arquivo do REQ selecionado. |
| Aba Design | Tab | Sim | Não | Mostra `design.md` único do projeto. |
| Botão Salvar Design | Botão | Sim | Não | Salva `.documents/design/design.md`. |
| Aba DRI | Tab | Sim | Não | Mostra `dri.md` único do projeto. |
| Botão Salvar DRI | Botão | Sim | Não | Salva `.documents/dri/dri.md`. |
| Aba Task List | Tab | Sim | Não | Lê tarefas de `.documents/task/task.md`. |
| Seletor executar task | Select | Sim | Sim | Envia a task escolhida para Execute. |
| Aba Execute | Tab | Sim | Sim | Exibe instruções derivadas da task selecionada. |
| Feedback visual | Toast/estado | Sim | Não | Confirma salvamento, erro ou carregamento. |

---

### 6. Regras de Exibição

| Código | Regra | Comportamento |
| --- | --- | --- |
| RI-RG-3089-001 | Sem REQ selecionado | Specify deve orientar criação ou seleção de REQ. |
| RI-RG-3089-002 | REQ em `.documents/spec/` | Exibir origem como arquivo de Specify. |
| RI-RG-3089-003 | Design | Exibir que o documento é único e vivo do projeto. |
| RI-RG-3089-004 | DRI | Exibir que o documento é único e vivo do projeto. |
| RI-RG-3089-005 | Task List | Exibir que as tarefas ficam em `.documents/task/task.md`. |
| RI-RG-3089-006 | Legado | Indicar specs antigas em arquivo único quando exibidas. |
| RI-RG-3089-007 | Execute sem task | Exibir placeholder informando que uma task deve ser selecionada. |
| RI-RG-3089-008 | Visual | Preservar tema dark, premium, glassmorphic e componentes existentes. |

---

### 7. Estados da Interface

| Estado | Descrição | Comportamento visual |
| --- | --- | --- |
| Loading | Documentos sendo carregados. | Spinner ou placeholder existente. |
| Empty | Nenhum REQ encontrado. | Mensagem orientativa e CTA de criação. |
| Selected | REQ selecionado. | Specify habilitado com cabeçalho preenchido. |
| Living document | Design, DRI ou Task aberto. | Badge de documento vivo. |
| Legacy | Spec antiga selecionada. | Badge discreta de legado. |
| Editing | Usuário alterando conteúdo. | Editor ativo. |
| Saving | Salvamento em andamento. | Botão desabilitado com feedback. |
| Success | Arquivo salvo. | Toast de sucesso. |
| Error | Falha de leitura/salvamento. | Toast ou mensagem clara. |

---

### 8. Fluxo de Interação

| Ação do usuário | Resposta da interface | Resultado esperado |
| --- | --- | --- |
| Abrir Harness Engineering | Sistema carrega estrutura documental. | Lista mostra REQs e documentos vivos ficam disponíveis. |
| Criar REQ | Modal coleta ID, título e responsável. | Novo arquivo aparece em `.documents/spec/`. |
| Selecionar REQ | Sistema lê arquivo do REQ. | Specify recebe o conteúdo. |
| Editar Specify e salvar | Sistema envia conteúdo do REQ. | Arquivo do REQ é atualizado. |
| Editar Design e salvar | Sistema salva documento vivo. | `design.md` é atualizado. |
| Editar DRI e salvar | Sistema salva documento vivo. | `dri.md` é atualizado. |
| Abrir Task List | Sistema lê `task.md`. | Checklist aparece com progresso. |
| Selecionar executar | Sistema monta instruções. | Aba Execute recebe contexto da task. |

---

### 9. Mapeamento de Dados

| Campo na tela | Nome técnico | Origem | Editável | Obrigatório |
| --- | --- | --- | --- | --- |
| Título do REQ | `title` | Header `#` do arquivo em `.documents/spec/` | Sim | Sim |
| ID do REQ | `requirement_id` | Nome/conteúdo do arquivo de REQ | Não | Sim |
| Arquivo do REQ | `spec_filename` | `.documents/spec/<REQ>.md` | Não | Sim |
| Design | `projectDocuments.design` | `.documents/design/design.md` | Sim | Sim |
| DRI | `projectDocuments.dri` | `.documents/dri/dri.md` | Sim | Não |
| Task List | `projectDocuments.task` | `.documents/task/task.md` | Sim | Sim |
| Task selecionada | `executeTask` | seleção do usuário em Task List | Sim | Não |
| Tipo de storage | `storage_type` | Backend Harness | Não | Sim |

---

### 10. Hierarquia Visual

**Prioridade Alta**

- REQ ativo em Specify.
- Documento vivo ativo.
- Aba atual.
- Conteúdo editável.
- Ações de salvar.
- Task selecionada para Execute.

**Prioridade Média**

- Caminho de origem.
- Estado legado.
- Progresso da Task List.
- Feedback de salvamento.

**Prioridade Baixa**

- Textos explicativos longos.
- Evoluções futuras como migração automática.

---

### 11. Microcopy da Interface

| Elemento | Texto sugerido | Observação |
| --- | --- | --- |
| Estado vazio | Crie ou selecione um REQ para editar o Specify. | Reflete múltiplos REQs. |
| Badge Specify | `.documents/spec` | Indica origem do REQ. |
| Badge Design | Documento vivo do projeto | Indica arquivo único. |
| Badge DRI | Documento vivo do projeto | Indica arquivo único. |
| Badge Task | Task List viva do projeto | Indica arquivo único. |
| Badge legado | Legado — arquivo único | Indica compatibilidade. |
| Ajuda Task List | As tarefas do projeto ficam em `.documents/task/task.md`. | Para nova estrutura. |
| Ajuda Execute | Selecione uma task para montar as instruções de execução. | Evita preenchimento antecipado. |
| Sucesso Specify | REQ salvo com sucesso. | Feedback específico. |
| Sucesso Design | `design.md` salvo com sucesso. | Feedback específico. |
| Sucesso DRI | `dri.md` salvo com sucesso. | Feedback específico. |
| Sucesso Task | `task.md` salvo com sucesso. | Feedback específico. |

---

### 12. Responsividade

| Dispositivo | Comportamento esperado |
| --- | --- |
| Desktop | Manter layout atual com sidebar de REQs e workspace por abas. |
| Tablet | Preservar abas e permitir rolagem independente dos editores. |
| Mobile | Quando suportado, empilhar lista e workspace, mantendo ações principais acessíveis. |

---

### 13. Acessibilidade

| Item | Critério |
| --- | --- |
| Tabs | Etapas devem ter nomes claros e ordem lógica. |
| Botões | Botões de salvar devem indicar o documento correspondente. |
| Badges | Estado legado e documento vivo não devem depender apenas de cor. |
| Teclado | Editores e seleção de task devem ser navegáveis por teclado. |
| Mensagens | Erros e sucessos devem ser claros e não depender apenas de ícones. |
| Contraste | Preservar contraste adequado no tema dark. |

---

### 14. Critérios de Aceite da Interface

| Código | Critério |
| --- | --- |
| CA-RI-3089-001 | A interface deve listar múltiplos REQs vindos de `.documents/spec/`. |
| CA-RI-3089-002 | A interface deve carregar o REQ selecionado na aba Specify. |
| CA-RI-3089-003 | A interface deve carregar `design.md` como documento vivo único. |
| CA-RI-3089-004 | A interface deve carregar `dri.md` como documento vivo único. |
| CA-RI-3089-005 | A interface deve carregar `task.md` como Task List viva do projeto. |
| CA-RI-3089-006 | A interface deve indicar specs legadas quando exibidas. |
| CA-RI-3089-007 | Execute deve exibir placeholder até uma task ser escolhida. |
| CA-RI-3089-008 | Botões de salvar devem informar o documento/etapa salva. |
| CA-RI-3089-009 | Textos da interface devem refletir a estrutura `.documents/spec`, `.documents/design`, `.documents/dri` e `.documents/task`. |
| CA-RI-3089-010 | O padrão visual dark, premium e glassmorphic do GitIDE deve ser preservado. |

---

### 15. Lacunas e Premissas

| Item | Tipo | Descrição |
| --- | --- | --- |
| 1 | Premissa | A pasta documental padrão do GitIDE é `.documents`. |
| 2 | Premissa | Um projeto pode ter múltiplos REQs em `.documents/spec/`. |
| 3 | Premissa | Design, DRI e Task List são documentos únicos e vivos por projeto. |
| 4 | Premissa | Execute é fluxo derivado da task selecionada, não arquivo obrigatório nesta revisão. |
| 5 | Lacuna | Estratégia de migração automática de `.documents/specs/*.md` ainda não foi definida. |
| 6 | Lacuna | Persistência futura de Execute pode ser avaliada após a primeira implementação. |
| 7 | Risco | A mudança de arquitetura exige revisar a implementação já iniciada para `staged_directory`. |
| 8 | Risco | Atualização de checkbox em `task.md` exige cuidado para não alterar tarefa errada. |

---

### 16. Fora do Escopo

- Criar pasta independente por REQ com todos os documentos de etapa.
- Migração automática em massa de specs antigas.
- Exclusão do modo legado.
- Reestruturação visual completa do Harness Engineering.
- Substituição do editor Markdown por editor rico.
- Alteração do Project Charter/TAP.
- Execução automática de código sem task escolhida e aprovação explícita.

---

### 17. Possíveis Evoluções Futuras

- Botão “Migrar specs legadas para `.documents/spec/`”.
- Preview consolidado juntando REQ, design, DRI e tasks relacionadas.
- Persistência dedicada para Execute.
- Histórico/snapshots por documento vivo.
- Metadados em `manifest.json` para índice documental do Harness.
- Exportação do pacote Harness para Word/PDF.
- Integração com IA para gerar ou atualizar somente um documento vivo por vez.

---

## 4. Task List — Tarefas

A lista abaixo representa a decomposição operacional rastreável do requisito **REQ-3089 — Harness Engineering com documentos vivos por projeto**. Cada tarefa deve ser executada individualmente após validação deste REQ e escolha explícita pelo usuário.

- [ ] TASK-REQ-3089-001: Corrigir a listagem backend do Harness Engineering para reconhecer o novo modo principal `.documents/spec/*.md`, mantendo compatibilidade temporária com `.documents/specs/*.md`.
- [ ] TASK-REQ-3089-002: Implementar no backend a criação/reconhecimento da estrutura `.documents/spec/`, `.documents/design/design.md`, `.documents/dri/dri.md` e `.documents/task/task.md`.
- [ ] TASK-REQ-3089-003: Implementar no backend a criação de novo REQ como arquivo individual em `.documents/spec/`.
- [ ] TASK-REQ-3089-004: Implementar leitura e salvamento do REQ selecionado em `.documents/spec/`.
- [ ] TASK-REQ-3089-005: Implementar leitura e salvamento dos documentos vivos `design.md`, `dri.md` e `task.md`.
- [ ] TASK-REQ-3089-006: Adaptar extração e atualização da Task List para ler e salvar checkboxes em `.documents/task/task.md`.
- [ ] TASK-REQ-3089-007: Adaptar o frontend `sddState` e a seleção de REQ para diferenciar REQ em `.documents/spec/`, documento vivo e legado.
- [ ] TASK-REQ-3089-008: Adaptar os botões de salvar Specify, Design, DRI e Task List para salvar os arquivos corretos da nova estrutura.
- [ ] TASK-REQ-3089-009: Adaptar a etapa Execute para montar instruções a partir da task selecionada, do REQ relacionado e dos documentos vivos do projeto.
- [ ] TASK-REQ-3089-010: Atualizar textos e microcopy da interface Harness Engineering para refletir a estrutura `.documents/spec`, `.documents/design`, `.documents/dri` e `.documents/task`.
- [ ] TASK-REQ-3089-011: Criar ou atualizar testes automatizados para listagem, criação, leitura, salvamento, Task List e compatibilidade legada.
- [ ] TASK-REQ-3089-012: Executar validações aprovadas, incluindo testes aplicáveis e `git status`, registrando evidências e limitações.

As tarefas acima substituem a decomposição anterior baseada em diretório por requisito. Qualquer implementação iniciada com `storage_type: staged_directory` deve ser revista para aderir ao novo modelo documental por projeto.

---

## 5. Execute — Implementação

Esta etapa não deve ser preenchida antecipadamente.

Ela deve ser usada somente quando uma tarefa específica do REQ-3089 for selecionada para execução por agente ou programador, seguindo o ciclo:

**Percepção → Planejamento → Aprovação → Execução → Verificação**

A execução deve ser mínima, rastreável, aprovada pelo usuário e validada por testes, build, leitura dos arquivos alterados, status Git ou outro mecanismo aplicável.
