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
- [x] TASK-REQ-3087-021: Implementar criação de novo arquivo pelo painel Arquivos do Workspace, usando endpoint seguro de escrita, validação de caminho relativo, feedback visual, recarregamento da árvore e abertura automática do arquivo criado.
- [x] TASK-REQ-3087-022: Ajustar o botão de criação de arquivo no painel Arquivos do Workspace para exibir somente o ícone, mantendo acessibilidade por `title` e `aria-label`, sem alterar o comportamento de criação de arquivo.

As tarefas acima não substituem os critérios de aceite da etapa **Specify**. Cada item deve ser tratado como unidade de execução técnica, com plano próprio, aprovação explícita e verificação antes de ser marcado como concluído.

---

## 4. Execute — Implementação

Esta etapa não deve ser preenchida antecipadamente.

Ela deve ser usada somente quando uma tarefa específica do REQ-3087 for selecionada para execução por agente ou programador, seguindo o ciclo:

**Percepção → Planejamento → Aprovação → Execução → Verificação**

A execução deve ser mínima, rastreável, aprovada pelo usuário e validada por testes, build, leitura do arquivo alterado, status Git ou outro mecanismo aplicável.

## 5. DRI — Documento de Requisito de Interface

### RI-REQ-3087-001 — Arquivos do Workspace

### 1. Identificação da Interface

| Campo | Valor |
| --- | --- |
| Código | RI-REQ-3087-001 |
| Nome da interface | Arquivos do Workspace |
| Módulo | Workspace / Explorador de Arquivos / Editor |
| RF relacionado | REQ-3087 — Arquivos do Workspace |
| SubRFs relacionados | RF-3087-001 Listagem de arquivos; RF-3087-002 Abertura de arquivo; RF-3087-003 Edição de arquivo; RF-3087-004 Criação de arquivo; RF-3087-005 Atualização da árvore; RF-3087-006 Integração com agente IA |
| Tipo de interface | Página com painel dividido, árvore/lista, editor textual e modal de criação |
| Perfil de usuário | Desenvolvedor, operador técnico, usuário GitIDE e agente IA supervisionado |
| Dispositivo prioritário | Desktop responsivo |
| Objetivo da tela | Permitir navegar, abrir, editar e criar arquivos do projeto ativo com segurança, feedback visual e rastreabilidade. |

---

### 2. Objetivo da Interface

A interface **Arquivos do Workspace** deve permitir que o usuário compreenda a estrutura do projeto ativo, selecione arquivos permitidos, visualize conteúdo textual, realize edições controladas, salve alterações e crie novos arquivos em caminhos relativos válidos.

Ela se conecta diretamente ao **REQ-3087** porque materializa, na experiência do usuário, os contratos funcionais de listagem, leitura, escrita, criação, atualização da árvore, proteção contra caminhos inválidos e integração com rastreabilidade do GitIDE.

A interface também deve apoiar o agente IA supervisionado, garantindo que qualquer leitura ou escrita de arquivo ocorra por endpoints autorizados e que alterações sejam precedidas de plano, aprovação e verificação.

---

### 3. Contexto de Uso

| Campo | Valor |
| --- | --- |
| Quem usa | Usuário técnico do GitIDE, desenvolvedor, operador do workspace e agente IA supervisionado. |
| Quando usa | Durante análise de código, leitura de documentação, criação de arquivos, edição de arquivos textuais, validação de alterações ou revisão de estrutura do projeto. |
| Por que usa | Para manipular arquivos do projeto ativo sem sair do GitIDE, mantendo segurança, rastreabilidade e contexto do workspace. |
| Gatilho de acesso | Clique na opção lateral **Arquivos do Workspace** após selecionar um projeto ativo. |
| Resultado esperado | Arquivos permitidos são exibidos, arquivos textuais podem ser abertos/editados, novos arquivos podem ser criados e a árvore permanece atualizada. |

---

### 4. Arquitetura da Informação

| Ordem | Seção | Objetivo | Tipo de componente |
| --- | --- | --- | --- |
| 1 | Cabeçalho do explorador | Identificar a área de arquivos e expor ações rápidas como criar arquivo e recarregar árvore. | Header com título e botões de ação |
| 2 | Árvore/lista de arquivos | Exibir arquivos permitidos do projeto ativo, ignorando diretórios bloqueados. | Painel lateral / lista hierárquica |
| 3 | Cabeçalho do editor | Mostrar o arquivo ativo e disponibilizar a ação de salvar quando aplicável. | Header de editor com ação principal |
| 4 | Metadados do arquivo | Exibir tamanho e data de modificação quando disponíveis. | Barra informativa |
| 5 | Editor textual | Exibir e permitir edição de conteúdo textual suportado. | Textarea/editor com gutter |
| 6 | Histórico de snapshots | Mostrar versões locais disponíveis para rollback quando existirem. | Drawer / timeline |
| 7 | Modal de criação de arquivo | Capturar caminho relativo e conteúdo inicial opcional para criar novo arquivo. | Modal com formulário |

---

### 5. Mapa de Componentes

| Componente | Tipo | Obrigatório | Editável | Comportamento esperado |
| --- | --- | --- | --- | --- |
| Título “Explorador de Arquivos” | Texto/Header | Sim | Não | Identifica o painel de navegação do workspace. |
| Botão “Novo arquivo” | Botão somente ícone | Sim | Não | Abre o modal de criação de arquivo exibindo apenas o ícone visual. Deve manter `title` e `aria-label` para acessibilidade. |
| Botão “Recarregar” | Botão/ícone | Sim | Não | Recarrega a árvore/lista de arquivos do projeto ativo. |
| Lista de arquivos | Lista/árvore | Sim | Não | Exibe caminhos permitidos retornados pelo backend. Arquivo selecionado deve ter destaque visual. |
| Nome do arquivo ativo | Texto/label | Sim | Não | Exibe o arquivo aberto ou mensagem orientativa quando nenhum arquivo estiver selecionado. |
| Botão “Salvar” | Botão | Sim | Não | Permanece desabilitado sem arquivo editável ou sem contexto válido; salva via endpoint `/files/write`. |
| Metadados do arquivo | Barra informativa | Não | Não | Exibe tamanho e última modificação quando disponíveis. |
| Gutter de linhas | Indicador visual | Não | Não | Exibe numeração sincronizada com o editor. |
| Editor textual | Campo textual | Sim | Sim | Exibe conteúdo de arquivos textuais e permite edição quando habilitado. |
| Drawer de snapshots | Timeline | Não | Não | Exibe snapshots locais quando houver histórico do arquivo. |
| Campo “Caminho relativo do arquivo” | Input | Sim | Sim | Obrigatório no modal de criação; deve rejeitar caminhos absolutos, `..`, barra inicial e segmentos vazios. |
| Campo “Conteúdo inicial” | Textarea | Não | Sim | Permite informar conteúdo textual inicial do novo arquivo. |
| Botão “Criar arquivo” | Botão | Sim | Não | Valida caminho, impede sobrescrita pela ação de criação, chama `/files/write`, recarrega árvore e abre o arquivo criado. |
| Botão “Cancelar” | Botão | Sim | Não | Fecha o modal sem criar arquivo. |

---

### 6. Regras de Exibição

| Código | Regra | Comportamento |
| --- | --- | --- |
| RI-RG-3087-001 | Projeto obrigatório | Sem projeto ativo, a área de arquivos não deve permitir operações de leitura, escrita ou criação. |
| RI-RG-3087-002 | Estado inicial do editor | Quando nenhum arquivo estiver aberto, exibir mensagem orientativa e manter o editor desabilitado. |
| RI-RG-3087-003 | Arquivo selecionado | O item selecionado na lista deve ter destaque visual consistente com o tema do GitIDE. |
| RI-RG-3087-004 | Salvamento disponível | O botão **Salvar** deve estar disponível somente quando houver arquivo aberto/editável. |
| RI-RG-3087-005 | Diretórios ignorados | Diretórios bloqueados ou pesados não devem aparecer na árvore principal. |
| RI-RG-3087-006 | Arquivo não suportado | Arquivos binários ou não textuais devem exibir mensagem clara e não abrir no editor textual. |
| RI-RG-3087-007 | Criação segura | O modal de criação deve orientar o usuário a usar caminho relativo e impedir sobrescrita por essa ação. |
| RI-RG-3087-008 | Feedback obrigatório | Toda ação de carregar, salvar, criar ou falhar deve apresentar feedback por estado visual, mensagem ou toast. |
| RI-RG-3087-009 | Acessibilidade de ícones | Ações exibidas somente por ícone devem manter nome acessível por `title`, `aria-label` ou equivalente. |

---

### 7. Estados da Interface

| Estado | Descrição | Comportamento visual |
| --- | --- | --- |
| Sem projeto | Nenhum projeto ativo foi selecionado. | Exibir estado global de nenhum projeto selecionado e bloquear ações do workspace. |
| Loading | Lista de arquivos ou conteúdo em carregamento. | Exibir spinner ou indicador de carregamento no painel correspondente. |
| Empty | Projeto sem arquivos exibíveis ou listagem vazia. | Exibir mensagem orientativa no explorador. |
| View | Arquivo textual carregado para leitura. | Conteúdo exibido no editor com cabeçalho e metadados. |
| Edit | Usuário alterando conteúdo textual. | Editor habilitado, gutter sincronizado e ação de salvar disponível quando aplicável. |
| Saving | Salvamento em andamento. | Botão de salvar desabilitado temporariamente e feedback de processamento. |
| Creating | Novo arquivo sendo criado pelo modal. | Botão de criação desabilitado com indicador de carregamento. |
| Success | Operação concluída. | Toast, mensagem curta ou mudança de estado confirmando criação/salvamento. |
| Error | Falha ao listar, abrir, criar ou salvar. | Mensagem clara sem expor credenciais, com possibilidade de correção ou nova tentativa. |
| Read-only | Arquivo não editável ou operação não permitida. | Editor bloqueado e mensagem informando a restrição. |

---

### 8. Fluxo de Interação

| Ação do usuário | Resposta da interface | Resultado esperado |
| --- | --- | --- |
| Acessar Arquivos do Workspace | Sistema carrega arquivos do projeto ativo. | Lista/árvore apresenta arquivos permitidos. |
| Clicar em Recarregar | Interface solicita nova listagem ao backend. | Árvore reflete o estado atual do workspace. |
| Selecionar arquivo textual | Sistema lê conteúdo pelo endpoint de leitura. | Editor exibe conteúdo e metadados. |
| Editar arquivo aberto | Editor captura alteração do usuário. | Conteúdo fica apto para salvamento. |
| Clicar em Salvar | Sistema envia conteúdo ao endpoint de escrita. | Arquivo é salvo, snapshot/rastreabilidade é criada quando disponível e status visual é atualizado. |
| Clicar em Novo arquivo | Modal de criação é exibido. | Usuário pode informar caminho e conteúdo inicial. |
| Informar caminho válido e criar | Sistema valida existência e chama `/files/write`. | Arquivo é criado, árvore recarregada e arquivo aberto no editor. |
| Informar caminho inválido | Interface exibe erro contextual. | Nenhum arquivo é criado. |
| Tentar criar arquivo existente | Interface alerta sobre sobrescrita bloqueada. | Usuário precisa escolher outro caminho. |
| Cancelar criação | Modal fecha sem enviar dados. | Nenhum arquivo é alterado. |

---

### 9. Mapeamento de Dados

| Campo na tela | Nome técnico | Origem | Editável | Obrigatório |
| --- | --- | --- | --- | --- |
| Projeto ativo | `state.activeProjectId` | Seleção de projeto no GitIDE | Não | Sim |
| Lista de arquivos | `files[].path` | `GET /api/projects/{project_id}/files` | Não | Sim |
| Tamanho do arquivo | `files[].size` | Endpoint de listagem / metadados do arquivo | Não | Não |
| Última modificação | `files[].last_modified` | Endpoint de listagem / metadados do arquivo | Não | Não |
| Arquivo ativo | `state.activeFilepath` | Seleção do usuário na lista | Não | Não |
| Conteúdo do arquivo | `content` | `GET /files/read` e textarea do editor | Sim | Não |
| Caminho do novo arquivo | `filepath` | Campo do modal | Sim | Sim |
| Conteúdo inicial | `content` | Campo do modal | Sim | Não |
| Snapshot | `snapshot_id` | `POST /files/write` / backend GitIDE | Não | Não |
| Status Git | `modified`, `untracked`, `deleted`, `staged` | Endpoint de status Git quando disponível | Não | Não |

---

### 10. Hierarquia Visual

**Prioridade Alta**

- Estado do projeto ativo.
- Lista/árvore de arquivos permitidos.
- Arquivo selecionado e conteúdo do editor.
- Ações principais: novo arquivo, recarregar e salvar.
- Mensagens de erro, validação e sucesso.

**Prioridade Média**

- Metadados do arquivo.
- Histórico de snapshots.
- Ajuda textual do modal de criação.
- Estados de carregamento e confirmação.

**Prioridade Baixa**

- Detalhes auxiliares de tamanho/data quando indisponíveis.
- Textos de orientação de uso.
- Evoluções futuras como filtros, busca ou agrupamentos.

---

### 11. Microcopy da Interface

| Elemento | Texto sugerido | Observação |
| --- | --- | --- |
| Título do painel | Explorador de Arquivos | Deve ser direto e operacional. |
| Estado inicial do editor | Selecione um arquivo para visualizar | Orienta o usuário antes da primeira seleção. |
| CTA de criação | Ícone de novo arquivo | Deve ser exibido somente como ícone no cabeçalho do explorador, mantendo `title` e `aria-label` com o texto “Adicionar novo arquivo”. |
| Título do modal | Criar novo arquivo | Explica a ação principal. |
| Label de caminho | Caminho relativo do arquivo | Reforça que caminhos absolutos não devem ser usados. |
| Placeholder de caminho | ex: docs/novo-arquivo.md | Demonstra padrão esperado. |
| Label de conteúdo inicial | Conteúdo inicial | Campo opcional para iniciar o arquivo. |
| Ajuda do modal | Use caminhos relativos ao projeto. | Deve orientar sem excesso de texto. |
| Aviso de segurança | O GitIDE bloqueia caminhos inválidos e não sobrescreve arquivos existentes por esta ação. | Deixa claro o comportamento de proteção. |
| Erro de caminho vazio | Informe o caminho relativo do arquivo. | Mensagem acionável. |
| Erro de caminho inválido | Use caminho relativo, sem barra inicial. | Mensagem contextual. |
| Erro de arquivo existente | Escolha outro caminho para evitar sobrescrita. | Evita perda acidental. |
| Toast de sucesso | Arquivo criado | Confirma criação e pode exibir o caminho. |
| Toast de erro | Erro ao criar arquivo | Deve vir acompanhado da causa resumida. |

---

### 12. Responsividade

| Dispositivo | Comportamento esperado |
| --- | --- |
| Desktop | Layout prioritário em duas colunas: explorador à esquerda e editor à direita; modal centralizado; ações no cabeçalho do explorador. |
| Tablet | Painéis podem reduzir largura, preservar árvore e editor com scroll independente; modal mantém formulário em coluna única. |
| Mobile | Quando suportado, priorizar navegação em coluna única, com explorador e editor empilhados; ações principais devem permanecer acessíveis e não depender apenas de hover. |

---

### 13. Acessibilidade

| Item | Critério |
| --- | --- |
| Labels | Campos do modal devem possuir labels persistentes e claros. |
| Contraste | Cores devem manter leitura confortável no tema dark/glassmorphic. |
| Navegação por teclado | Modal deve permitir foco no campo de caminho e acionamento por Enter/Ctrl+Enter quando aplicável. |
| Botões por ícone | Botões sem texto visível devem possuir `title`, `aria-label` ou nome acessível equivalente. |
| Mensagens de erro | Erros devem ser compreensíveis, acionáveis e não expor caminhos sensíveis além do necessário. |
| Leitores de tela | Ações de criar, salvar, recarregar e fechar modal devem ter nomes claros. |
| Foco | Ao abrir o modal, o foco deve ir para o campo de caminho relativo. |

---

### 14. Critérios de Aceite da Interface

| Código | Critério |
| --- | --- |
| CA-RI-3087-001 | A interface deve listar arquivos permitidos do projeto ativo ao abrir a aba Arquivos do Workspace. |
| CA-RI-3087-002 | O usuário deve conseguir recarregar a lista de arquivos manualmente. |
| CA-RI-3087-003 | Ao selecionar arquivo textual válido, o conteúdo deve aparecer no editor. |
| CA-RI-3087-004 | O editor deve exibir estado orientativo quando nenhum arquivo estiver selecionado. |
| CA-RI-3087-005 | O usuário deve conseguir salvar alterações em arquivo textual pelo endpoint seguro de escrita. |
| CA-RI-3087-006 | A interface deve exibir feedback de sucesso ou erro após salvar. |
| CA-RI-3087-007 | O usuário deve conseguir abrir o modal de criação de arquivo pela ação Novo arquivo. |
| CA-RI-3087-008 | O modal deve exigir caminho relativo válido para criar arquivo. |
| CA-RI-3087-009 | A criação deve bloquear caminho absoluto, `..`, barra inicial e segmentos vazios. |
| CA-RI-3087-010 | A criação deve impedir sobrescrita de arquivo já existente por essa ação. |
| CA-RI-3087-011 | Após criar arquivo, a árvore deve ser recarregada e o arquivo criado deve abrir automaticamente no editor. |
| CA-RI-3087-012 | Botões exibidos somente como ícone devem manter nome acessível por `title`, `aria-label` ou equivalente. |
| CA-RI-3087-013 | Mensagens de erro não devem expor tokens, senhas, chaves de API ou URLs autenticadas. |
| CA-RI-3087-014 | A interface deve preservar o padrão visual dark, premium e glassmorphic do GitIDE. |

---

### 15. Lacunas e Premissas

| Item | Tipo | Descrição |
| --- | --- | --- |
| 1 | Premissa | O backend `/files/write` cria arquivos textuais em caminhos válidos e gera snapshot/rastreabilidade quando suportado. |
| 2 | Premissa | A interface opera prioritariamente em desktop, com responsividade progressiva para telas menores. |
| 3 | Lacuna | Limites formais de tamanho máximo para abertura e edição textual ainda precisam ser definidos. |
| 4 | Lacuna | Política final para exibição/edição de arquivos sensíveis como `.env` ainda precisa ser definida. |
| 5 | Risco | Se validações de caminho divergirem entre frontend e backend, pode haver falha de experiência ou bloqueio tardio. |
| 6 | Risco | Projetos muito grandes podem exigir busca, filtro ou carregamento incremental para manter performance. |

---

### 16. Fora do Escopo

- Criar, mover, renomear ou excluir diretórios pelo painel de Arquivos do Workspace.
- Sobrescrever arquivo existente pela ação de criação de novo arquivo.
- Editar arquivos binários no editor textual.
- Acessar arquivos fora da raiz do projeto ativo.
- Manipular arquivos via terminal em fluxos conduzidos por agente IA.
- Resolver conflitos Git automaticamente dentro do editor de arquivos.
- Sincronizar arquivos em tempo real com armazenamento externo.

---

### 17. Possíveis Evoluções Futuras

- Busca textual dentro do workspace.
- Filtro por extensão, tipo de arquivo ou status Git.
- Criação de pastas diretamente pela interface do workspace.
- Renomear, mover e excluir arquivos com confirmação e snapshots.
- Indicadores visuais por status Git diretamente na árvore.
- Preview específico para Markdown, imagens e JSON.
- Editor com destaque de sintaxe.
- Proteção especial para arquivos sensíveis como `.env`.
- Carregamento incremental para projetos grandes.
