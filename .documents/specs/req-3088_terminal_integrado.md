# REQ-3088 — Terminal Integrado

## 1. Specify — Especificação Funcional

### 1.1 Identificação e Metadados Básicos

**ID Único:** REQ-3088

**Título / Resumo:** Terminal Integrado

**Tipo:** Requisito funcional

**Módulo:** Terminal / Execução de Comandos / Operações do Workspace

**Prioridade:** P2

**Status:** Especificado

**Solicitante:** Augusto Nascimento

**Responsável atual:** Equipe técnica GitIDE

**Release / Iteração:** A definir

**Esforço estimado:** A definir após detalhamento técnico das tarefas

---

### 1.2 Contexto

O GitIDE precisa oferecer um terminal integrado para permitir a execução controlada de comandos dentro do diretório do projeto ativo. Esse recurso é essencial para tarefas como rodar testes, builds, servidores locais, validações rápidas, comandos Git autorizados e outras operações técnicas necessárias durante o desenvolvimento.

Como o terminal pode executar ações sensíveis no ambiente local, o requisito deve priorizar segurança, rastreabilidade e consentimento explícito do usuário. O terminal integrado não deve ser tratado como uma área livre para manipulação irrestrita de arquivos, mas sim como um canal operacional para comandos aprovados e relacionados ao projeto ativo.

Este requisito define o comportamento esperado para entrada de comandos, execução, retorno de saída, controle de erros, bloqueios de segurança, histórico e integração com o fluxo de aprovação do GitIDE.

---

### 1.3 Objetivo Funcional

Permitir que o usuário execute comandos operacionais no contexto do projeto ativo por meio de uma interface integrada ao GitIDE, com feedback de saída, status de execução, tratamento de erros, histórico e mecanismos de aprovação para comandos sensíveis.

O terminal integrado deve apoiar o ciclo de desenvolvimento sem comprometer a segurança do workspace, evitando comandos destrutivos, manipulação indevida de arquivos e execuções fora do diretório permitido.

---

### 1.4 Descrição do Requisito

O sistema deve disponibilizar uma área de **Terminal Integrado** onde o usuário possa enviar comandos para execução no diretório raiz do projeto ativo. A execução deve ocorrer por endpoint controlado do backend, que deve validar o projeto, preparar o ambiente de trabalho e retornar stdout, stderr, código de saída e estado final da execução.

O terminal deve diferenciar comandos operacionais permitidos de comandos potencialmente perigosos. Comandos sensíveis devem exigir aprovação explícita do usuário antes da execução. Comandos usados para leitura, criação, edição ou remoção direta de arquivos via shell não devem ser o mecanismo padrão para manipulação de arquivos, pois o GitIDE já possui endpoints específicos para leitura e escrita rastreável.

---

### 1.5 História de Usuário

Como usuário do GitIDE, eu quero executar comandos técnicos dentro do projeto ativo pela própria interface, para que eu consiga validar builds, rodar testes, iniciar serviços locais e realizar operações Git sem sair do fluxo do GitIDE.

Como agente de IA conectado ao GitIDE, eu preciso executar apenas comandos autorizados e operacionais, para que eu possa validar alterações com segurança sem manipular arquivos indevidamente ou executar ações destrutivas sem aprovação do usuário.

---

## 2. Escopo Funcional

### 2.1 Dentro do Escopo

- Executar comandos no diretório raiz do projeto ativo.
- Exibir stdout, stderr e código de saída.
- Indicar estado de execução: aguardando, executando, sucesso, erro ou retido para aprovação.
- Solicitar aprovação para comandos sensíveis ou bloqueados pelo mecanismo de segurança.
- Permitir execução de comandos operacionais, como testes, builds, servidores locais, migrações aprovadas e comandos Git autorizados.
- Registrar histórico básico de comandos executados e seus resultados quando suportado.
- Permitir copiar saída do terminal.
- Preservar contexto do projeto ativo durante a execução.
- Bloquear ou reter comandos considerados perigosos, destrutivos ou fora da política definida.
- Retornar mensagens claras em caso de erro, timeout, comando inválido ou ausência de projeto.

### 2.2 Fora do Escopo

- Substituir completamente um terminal nativo do sistema operacional.
- Permitir execução irrestrita de comandos destrutivos sem aprovação.
- Usar shell como mecanismo padrão para leitura, escrita, criação ou exclusão de arquivos do projeto.
- Executar comandos fora do diretório do projeto ativo.
- Expor tokens, senhas ou credenciais em mensagens, logs ou histórico.
- Executar comandos interativos que dependam de entrada contínua sem suporte específico.
- Gerenciar processos de longa duração sem controle de encerramento, timeout ou feedback.
- Automatizar deploys, migrations ou pushes sem confirmação explícita do usuário.

---

## 3. Regras de Negócio

### RN-001 — Execução no projeto ativo

Todo comando deve ser executado dentro do diretório raiz do projeto ativo identificado pelo GitIDE.

### RN-002 — Aprovação para comandos sensíveis

Comandos sensíveis, destrutivos, de deploy, Git push, merge, migrations, inicialização de serviços ou qualquer operação que possa alterar estado do projeto devem exigir aprovação explícita quando a política de segurança determinar.

### RN-003 — Terminal não substitui endpoints de arquivo

Leitura, criação, edição e exclusão de arquivos devem ser realizadas preferencialmente pelos endpoints próprios do GitIDE. O terminal não deve ser usado por agentes para manipulação direta de arquivos via comandos como `cat`, `echo`, `sed`, `tee`, `rm`, `cp`, `mv` ou equivalentes.

### RN-004 — Retorno completo da execução

A resposta da execução deve informar, no mínimo, status, stdout, stderr e código de saída.

### RN-005 — Proteção contra exposição de credenciais

O sistema deve evitar exibir ou repetir tokens, senhas, URLs autenticadas e segredos em logs, histórico ou mensagens de resposta.

### RN-006 — Timeout e controle de execução

Comandos devem possuir timeout ou controle de encerramento para evitar travamento indefinido do backend ou da interface.

### RN-007 — Feedback visual obrigatório

A interface deve mostrar claramente quando o comando está executando, foi concluído com sucesso, falhou ou ficou pendente de aprovação.

### RN-008 — Histórico auditável

Sempre que suportado, o terminal deve manter trilha de comandos executados, usuário/ator que solicitou, projeto, horário e resultado resumido.

### RN-009 — Compatibilidade entre sistemas operacionais

O terminal deve considerar diferenças entre Windows e Linux, evitando assumir comandos exclusivos de um único sistema quando houver alternativa mais portável.

---

## 4. Fluxos Funcionais

### 4.1 Fluxo Principal — Executar comando simples

1. O usuário acessa o Terminal Integrado.
2. O sistema identifica o projeto ativo.
3. O usuário digita um comando operacional.
4. O sistema envia o comando ao backend.
5. O backend valida o projeto e a política de segurança.
6. O comando é executado no diretório do projeto.
7. O backend captura stdout, stderr e código de saída.
8. A interface exibe o resultado ao usuário.

### 4.2 Fluxo Principal — Executar validação técnica

1. O usuário ou agente solicita comando de validação, como teste ou build.
2. O sistema apresenta o comando planejado.
3. Após aprovação quando necessária, o comando é executado.
4. O terminal exibe logs da execução.
5. O resultado é usado como evidência de validação.
6. O agente reporta somente validações realmente executadas.

### 4.3 Fluxo Alternativo — Comando retido para aprovação

1. O usuário ou agente solicita comando sensível.
2. O backend identifica necessidade de aprovação manual.
3. A execução é retida.
4. O sistema retorna status `pending_approval` e identificador do comando.
5. A interface solicita aprovação do usuário.
6. Após aprovação, o comando pode ser reenviado ou liberado conforme mecanismo do GitIDE.

### 4.4 Fluxo Alternativo — Comando com erro

1. O comando é executado.
2. O processo retorna código de saída diferente de zero.
3. O backend captura stderr e stdout.
4. A interface mostra a falha de forma clara.
5. O sistema não assume sucesso quando o código de saída indica erro.

### 4.5 Fluxo de Erro — Projeto não encontrado

1. O terminal recebe solicitação para projeto inexistente ou não cadastrado.
2. O backend rejeita a execução.
3. A interface informa que o projeto ativo não foi encontrado.
4. Nenhum comando é executado.

### 4.6 Fluxo de Erro — Timeout

1. O comando excede o tempo máximo permitido.
2. O backend interrompe ou marca a execução como expirada.
3. A interface informa timeout.
4. O usuário pode decidir ajustar o comando ou executar novamente.

---

## 5. Requisitos Funcionais Detalhados

### RF-3088-001 — Entrada de comando

O sistema deve permitir que o usuário informe um comando textual para execução no terminal integrado.

**Critérios específicos:**

- O campo de comando deve estar associado ao projeto ativo.
- Comando vazio não deve ser executado.
- A interface deve permitir limpar ou substituir o comando antes da execução.

### RF-3088-002 — Execução controlada

O sistema deve executar comandos por meio do endpoint de terminal do GitIDE, sempre no diretório do projeto ativo.

**Critérios específicos:**

- A execução deve retornar status e código de saída.
- O comando deve ser executado em ambiente controlado.
- Erros de execução devem ser exibidos ao usuário.

### RF-3088-003 — Saída do terminal

O sistema deve exibir stdout e stderr de forma legível.

**Critérios específicos:**

- A saída deve preservar quebras de linha.
- A interface deve diferenciar sucesso, erro e pendência quando possível.
- O usuário deve conseguir copiar a saída para análise.

### RF-3088-004 — Aprovação de comandos sensíveis

O sistema deve reter comandos sensíveis até aprovação explícita.

**Critérios específicos:**

- O retorno deve indicar `pending_approval` quando aplicável.
- A interface deve mostrar o comando pendente e seu identificador.
- O comando só deve prosseguir após aprovação do usuário.

### RF-3088-005 — Histórico de comandos

O sistema deve registrar histórico básico de comandos executados quando houver suporte no backend.

**Critérios específicos:**

- O histórico deve conter comando, projeto, data/hora, status e código de saída.
- Dados sensíveis devem ser mascarados ou omitidos.
- O histórico não deve expor tokens em URLs ou variáveis.

### RF-3088-006 — Execução por agente IA

O sistema deve permitir que o agente IA solicite execução de comandos operacionais, respeitando o fluxo de planejamento, aprovação e verificação.

**Critérios específicos:**

- O agente deve explicar objetivo do comando antes da execução.
- O agente deve aguardar aprovação quando o comando afetar o projeto.
- O agente não deve usar terminal para manipulação direta de arquivos.

### RF-3088-007 — Tratamento de comandos longos

O sistema deve tratar comandos de longa duração com estado visual adequado e timeout.

**Critérios específicos:**

- A interface deve indicar execução em andamento.
- O backend deve evitar bloqueio indefinido.
- O usuário deve receber feedback se o comando expirar.

### RF-3088-008 — Compatibilidade operacional

O terminal deve funcionar nos sistemas suportados pelo GitIDE, respeitando diferenças entre Windows e Linux.

**Critérios específicos:**

- Comandos documentados devem preferir alternativas portáveis quando possível.
- Erros por comando inexistente devem ser reportados claramente.

---

## 6. Requisitos Não Funcionais

- O terminal deve apresentar respostas de forma rápida para comandos curtos.
- A interface deve preservar a identidade visual dark, premium e glassmorphic do GitIDE.
- O backend deve validar o projeto antes de executar qualquer comando.
- A execução deve possuir política de timeout ou proteção equivalente.
- Logs e histórico não devem expor credenciais.
- O recurso deve ser compatível com Windows e Linux sempre que possível.
- O terminal deve ser auditável e adequado ao uso por agentes de IA.
- Mensagens de erro devem ser claras, sem excesso de detalhes sensíveis.
- Comandos de validação devem produzir evidências reutilizáveis no relatório final do agente.

---

## 7. Critérios de Aceitação

- [ ] Dado que existe um projeto ativo, quando o usuário executa um comando simples permitido, então o comando roda no diretório do projeto e retorna stdout, stderr e código de saída.
- [ ] Dado que o usuário tenta executar comando vazio, quando aciona execução, então o sistema bloqueia a ação e informa que o comando é obrigatório.
- [ ] Dado que um comando retorna erro, quando a execução termina, então a interface mostra código de saída e stderr sem indicar sucesso falso.
- [ ] Dado que o comando é sensível, quando enviado ao backend, então o sistema retorna pendência de aprovação antes de executar.
- [ ] Dado que o comando ficou pendente, quando o usuário aprova manualmente, então o comando pode ser executado conforme política do GitIDE.
- [ ] Dado que o comando excede o timeout, quando o limite é alcançado, então o sistema informa timeout e evita bloqueio indefinido.
- [ ] Dado que há tokens ou credenciais em saída ou URLs, quando o terminal exibe logs, então o sistema evita expor esses valores desnecessariamente.
- [ ] Dado que o agente IA precisa validar uma alteração, quando solicita um comando, então ele apresenta plano e aguarda aprovação antes da execução.
- [ ] Dado que o agente IA precisa ler ou editar arquivo, quando planeja a ação, então ele usa endpoints de arquivos e não comandos shell de manipulação.
- [ ] Dado que o comando executado é um teste ou build, quando termina com sucesso, então o resultado pode ser usado como evidência de validação.
- [ ] Dado que o projeto não existe, quando uma execução é solicitada, então nenhum comando é executado e o erro é apresentado.
- [ ] Dado que o terminal está em execução, quando o usuário acessa a saída, então as quebras de linha e mensagens são preservadas.

---

## 8. Rastreabilidade

### 8.1 Links Ascendentes

- TAP: `.documents/project-charter.md`
- Produto: GitIDE
- Módulo: Terminal Integrado / Execução de Comandos

### 8.2 Links Descendentes

- TASK-3088-001 — Mapear implementação atual do endpoint de execução de comandos.
- TASK-3088-002 — Revisar política de aprovação para comandos sensíveis.
- TASK-3088-003 — Padronizar retorno de stdout, stderr, exit code e status.
- TASK-3088-004 — Melhorar feedback visual do terminal na interface.
- TASK-3088-005 — Implementar ou revisar mascaramento de credenciais em logs.
- TASK-3088-006 — Validar timeout e tratamento de comandos longos.
- TASK-3088-007 — Criar testes para sucesso, erro, pendência de aprovação e timeout.

### 8.3 Código e Deploy

- Commits: A preencher durante a implementação.
- Pull Requests: A preencher durante a implementação.
- Pipelines: A definir conforme fluxo do projeto.

### 8.4 Casos de Teste

- CT-3088-001 — Executar comando simples permitido.
- CT-3088-002 — Bloquear comando vazio.
- CT-3088-003 — Retornar stderr e exit code em caso de falha.
- CT-3088-004 — Reter comando sensível para aprovação.
- CT-3088-005 — Executar comando aprovado após pendência.
- CT-3088-006 — Validar timeout de comando longo.
- CT-3088-007 — Mascarar ou evitar exposição de credenciais.
- CT-3088-008 — Validar execução no diretório do projeto ativo.

---

## 9. Design — Planejamento Funcional e Técnico

### 9.1 Arquitetura Proposta

A funcionalidade deve utilizar o backend do GitIDE como mediador de execução. O frontend envia o comando e o identificador do projeto. O backend valida o projeto, aplica regras de segurança, executa o comando no diretório do projeto ativo quando permitido e retorna o resultado estruturado.

A interface deve apresentar área de entrada do comando, botão de execução, indicador de estado, área de saída e mensagens de erro. Quando o backend retornar pendência de aprovação, a interface deve mostrar o comando e o identificador da aprovação.

O agente IA deve seguir o mesmo fluxo, solicitando comandos apenas após explicar o motivo e aguardando aprovação do usuário quando necessário.

### 9.2 Componentes Envolvidos

- Backend de projetos/workspaces.
- Endpoint de execução de comandos.
- Camada de segurança/aprovação de comandos.
- Interface do Terminal Integrado.
- Sistema de logs/histórico, se disponível.
- Módulo Git, para comandos como status, pull, merge e push autorizados.
- Agente IA conectado ao GitIDE.

### 9.3 Contratos Técnicos Esperados

#### POST `/api/projects/{project_id}/execute`

Executa comando operacional dentro do diretório do projeto ativo.

**Payload esperado:**

```json
{
  "command": "python -m pytest"
}
```

**Resposta de sucesso esperada:**

```json
{
  "status": "success",
  "exit_code": 0,
  "stdout": "...",
  "stderr": ""
}
```

**Resposta de erro esperada:**

```json
{
  "status": "error",
  "exit_code": 1,
  "stdout": "",
  "stderr": "mensagem de erro"
}
```

**Resposta de aprovação pendente esperada:**

```json
{
  "status": "pending_approval",
  "command_id": 123,
  "message": "Execução retida por segurança e requer aprovação manual."
}
```

### 9.4 Dados e Integrações

**Banco de dados:** Não há dependência direta obrigatória para o terminal, exceto quando comandos aprovados executarem migrations ou validações de banco.

**Git:** O terminal pode executar comandos Git operacionais autorizados, como status, log, fetch, pull, merge, commit e push.

**Agente IA:** O agente pode solicitar comandos de validação, mas deve respeitar planejamento, aprovação e relatório final.

**Sistema de arquivos:** O terminal não deve ser usado como mecanismo padrão de manipulação direta de arquivos; isso deve ocorrer pelos endpoints próprios.

---

## 10. Task List — Tarefas Técnicas

- [ ] TASK-3088-001: Revisar implementação atual do endpoint `/api/projects/{project_id}/execute`.
- [ ] TASK-3088-002: Mapear quais comandos são permitidos, sensíveis, retidos ou bloqueados.
- [ ] TASK-3088-003: Padronizar estrutura de resposta com `status`, `exit_code`, `stdout` e `stderr`.
- [ ] TASK-3088-004: Implementar ou revisar estado visual de execução no frontend.
- [ ] TASK-3088-005: Melhorar apresentação de erro, sucesso e pendência de aprovação.
- [ ] TASK-3088-006: Revisar proteção contra exposição de tokens em logs e histórico.
- [ ] TASK-3088-007: Validar timeout e comportamento para comandos longos.
- [ ] TASK-3088-008: Garantir execução no diretório correto do projeto ativo.
- [ ] TASK-3088-009: Criar testes automatizados para sucesso, erro e pendência de aprovação.
- [ ] TASK-3088-010: Documentar comandos recomendados para validação, build, testes e Git.

---

## 11. Execute — Orientações de Implementação

Antes de qualquer implementação relacionada ao REQ-3088, o agente técnico deve:

1. Confirmar o projeto ativo e o ID do projeto.
2. Ler `GPT_INSTRUCTIONS.md`, se existir na raiz do workspace.
3. Inspecionar apenas os arquivos necessários para a task selecionada.
4. Preparar plano específico para a task.
5. Aguardar aprovação explícita do usuário.
6. Aplicar alteração mínima e cirúrgica.
7. Validar com testes, build ou verificação manual documentada.
8. Executar `git status` para registrar arquivos modificados.
9. Reportar alterações, validações, riscos e próximos passos.

### 11.1 Estratégia Recomendada

A implementação deve começar pela revisão do endpoint de execução de comandos e da política de retenção para comandos sensíveis. Em seguida, a interface deve ser ajustada para diferenciar visualmente execução em andamento, sucesso, erro e pendência de aprovação.

Melhorias visuais devem preservar a identidade dark/glassmorphic do GitIDE e utilizar arquivos CSS existentes, sem introduzir estilos inline novos.

### 11.2 Validações Recomendadas

- Validar comando simples de status, como `git status --short --branch`.
- Validar comando de teste ou build disponível no projeto.
- Validar comando que retorna erro controlado.
- Validar comando retido para aprovação.
- Validar timeout com comando longo em ambiente seguro.
- Validar que stdout e stderr são exibidos corretamente.
- Validar que o diretório de execução é o projeto ativo.

---

## 12. Riscos, Dependências e Pendências

### 12.1 Riscos

- Comandos mal utilizados podem alterar ou remover arquivos do projeto.
- Comandos de longa duração podem travar recursos se não houver timeout adequado.
- Saídas de terminal podem conter tokens, senhas ou URLs autenticadas.
- Diferenças entre Windows e Linux podem causar falhas de comando.
- Execução automática por agente IA sem aprovação pode comprometer segurança operacional.
- Comandos interativos podem ficar aguardando entrada indefinidamente.

### 12.2 Dependências

- Projeto ativo cadastrado no GitIDE.
- Backend de execução de comandos funcional.
- Política de segurança/aprovação configurada.
- Interface de terminal no frontend.
- Ambiente local com ferramentas necessárias instaladas, como Python, Node.js, Git ou outros comandos do projeto.

### 12.3 Pendências

- Definir lista formal de comandos sempre bloqueados.
- Definir lista de comandos que exigem aprovação manual.
- Definir tempo máximo padrão de execução.
- Definir mecanismo para interromper comandos em execução.
- Definir política de histórico e retenção de logs.
- Definir mascaramento automático de credenciais em stdout/stderr.

---

## 13. Observações Finais

O Terminal Integrado é um recurso poderoso e sensível dentro do GitIDE. Ele deve acelerar o desenvolvimento e a validação técnica, mas sempre com foco em segurança, controle humano e rastreabilidade.

A implementação do REQ-3088 deve garantir que comandos operacionais sejam simples de executar, enquanto ações destrutivas, sensíveis ou com impacto no estado do projeto sejam tratadas por aprovação explícita e registro adequado.
