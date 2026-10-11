# Okestre Local: ponte MCP para projetos no computador

Data: 2026-10-11
Branch: `codex/local-agent-bridge`
Base local: `main`, commit `b9e0b46`.
Status: primeiro incremento implementado localmente em 2026-10-11; não publicado na VM.

## Progresso do primeiro incremento

- Implementados: roteamento de ferramentas MCP, schema de localização, pareamento, credencial de dispositivo, revogação, transporte, CLI e leitura/pesquisa local.
- Implementados também: escrita/patch com hash, snapshots e deduplicação locais, requisitos/tarefas, painel próprio de dispositivos/arquivos, aplicativo Windows com bandeja e build portátil.
- Rotas legadas para projetos locais são bloqueadas explicitamente. O executor servidor permanece com o contrato anterior; a seleção ocorre no registro das ferramentas MCP.
- Validado em Windows: testes de regressão MCP/OAuth, ponte por WebSocket real no loopback, operações locais, limites de acesso, painel Edge e inicialização do executável.
- Pendentes: Git, terminal aprovado localmente, integração completa das abas existentes, histórico gráfico, inicialização automática, instalador/distribuição assinada, Windows limpo, publicação e validação real VM/GPT.
- Nenhum projeto existente foi migrado e nenhum arquivo de projeto foi removido da VM.

Consulte `LOCAL_AGENT.md` para execução, restrições e implantação. As etapas abaixo continuam como roteiro completo; o primeiro incremento não encerra todas elas.

## Objetivo

Manter os arquivos dos projetos no computador do usuário. O GPT acessa o MCP público da VM; a VM autentica, autoriza e encaminha operações para um agente local. Leituras, pesquisas, edições, Git, snapshots e, em etapa posterior, comandos são executados no computador.

O agente é um programa determinístico, sem modelo de IA e sem chave OpenAI. A VM pode guardar contas, concessões, dispositivos, vínculos de projetos e auditoria de metadados. Conteúdo solicitado transita em memória pela VM e chega ao provedor de IA, mas não deve ser persistido pela ponte, pelo proxy ou pelos logs. Isso não implica retenção zero no provedor.

## Evidências no código atual

- `gitide_server/mcp_server.py`: `safe_path` e operações MCP acessam diretamente `project.path`; `run` centraliza parte da autorização e obtenção do projeto.
- `gitide_server/database.py`: `Project.path` possui conversão Windows/Linux, inadequada para identificar uma pasta de um dispositivo remoto. `FileSnapshot` armazena conteúdo; `PendingCommand` armazena o comando.
- `gitide_server/vcs.py`: escrita e histórico persistem snapshots no banco do servidor.
- `gitide_sync.py`: exportação/importação ZIP replica arquivos; não implementa execução remota em pastas locais.
- `gitide_server/mcp_terminal.py`: executa comandos no host do servidor.
- `gitide_server/mcp_audit.py`: já define auditoria restrita a metadados, útil como base.

## Arquitetura proposta

```text
GPT -- MCP HTTPS --> VM Okestre -- canal WSS --> Okestre Local --> pasta autorizada
                                              conexão iniciada pelo computador
```

Manter o contrato MCP externo e introduzir uma interface de operações de projeto. As ferramentas deixam de manipular caminhos diretamente e selecionam o executor conforme o cadastro. Projetos existentes no servidor continuam identificados explicitamente como `server`; projetos novos locais usam `device`. Nunca recorrer ao disco da VM quando um projeto local estiver offline.

Essa compatibilidade é com a localização dos projetos, não uma alteração do motor de IA. A migração de projetos existentes para armazenamento local é explícita. Não copiar nem remover os arquivos atuais automaticamente.

Componentes propostos:

- `gitide_server/project_backend.py`: contrato de listagem, leitura, pesquisa, escrita, patch, tarefas e Git.
- `gitide_server/local_bridge/`: cadastro, pareamento, autorização e transporte de requisições/respostas.
- `okestre_local/`: cliente Windows, registro privado de pastas, executor, armazenamento local e interface de bandeja.
- Painel web: dispositivos, online/offline, projetos vinculados e revogação.
- Testes isolados de protocolo, operações e integração MCP/ponte/agente.

Começar com núcleo Python e CLI para validar o fluxo. Depois empacotar aplicativo Windows com interface de bandeja, seletor de pastas, inicialização opcional com o Windows, pausa e histórico. Escolher a biblioteca gráfica e o empacotador após uma prova curta de instalação e execução em Windows sem Python instalado.

## Cadastro e permissões

1. Usuário autenticado cria um pareamento de curta duração na VM.
2. Agente apresenta o código; usuário confirma o dispositivo e a conta no painel.
3. Emitir credencial exclusiva, revogável e rotacionável; guardar o segredo no armazenamento protegido do Windows, não em arquivos de projeto.
4. Usuário escolhe pastas no computador. Cada raiz recebe identificador opaco; a VM não precisa conhecer seu caminho absoluto.
5. Associar projeto, conta, dispositivo e raiz. Validar autorização no servidor e no agente em cada operação.
6. Permissões efetivas são a interseção da concessão MCP com a autorização local. Terminal desabilitado inicialmente.

Bloquear caminhos absolutos, `..`, UNC, caminhos de dispositivo, fluxos alternativos NTFS e escapes por symlinks/junctions. Considerar troca de links entre validação e acesso; validação apenas textual não basta. Preservar bloqueios de segredos e regras de exclusão existentes. Revogação cancela novas chamadas e fecha o canal; operações já aplicadas não são revertidas automaticamente.

## Protocolo e confiabilidade

Mensagens versionadas com `request_id`, dispositivo, raiz, operação, argumentos, prazo e autorização vinculada à chamada. Resposta com o mesmo identificador, estado, resultado limitado ou erro padronizado. Não aceitar uma raiz arbitrária indicada pelo cliente MCP.

- Heartbeat, reconexão com atraso progressivo e variação aleatória, limites de mensagens e concorrência.
- Primeira implantação com um processo responsável pelo canal. Não escalar para vários workers sem roteamento explícito entre eles; registrar essa restrição na configuração de deploy.
- Requisições pendentes e conteúdo somente em memória na VM, sem fila durável contendo arquivos.
- Computador offline: erro explícito `device_offline`; expiração: `request_timeout`; mudança concorrente: `conflict`.
- Escrita condicionada a SHA-256, bloqueio local por arquivo, substituição atômica e snapshot local.
- Registro local durável de identificadores de mutação com estados e recuperação após falha. Uma resposta perdida não autoriza repetir a mutação automaticamente.
- Estado ambíguo após interrupção deve ser reconciliado ou informado como indeterminado; não prometer execução exatamente uma vez para efeitos arbitrários de shell.
- Limitar tamanho, tempo e volume de saídas; paginação para leituras e pesquisas.

## Etapas e critérios de conclusão

### 1. Separar operações de projeto

Inventariar acessos diretos a disco no MCP, painel, tarefas, histórico, Git, exportação/importação e execução de agentes. Criar interface de backend e adaptar o executor atual, preservando contratos MCP e permissões. Criar migração de schema versionada e reversível: projetos existentes recebem localização `server`; projetos `device` não exigem caminho da VM.

Critério: testes existentes relevantes continuam passando; chamadas para projetos locais não alcançam o executor de disco do servidor. APIs ainda não adaptadas retornam indisponibilidade explícita para esses projetos.

### 2. Pareamento e transporte mínimo

Criar cadastro de dispositivos, pareamento, revogação, canal autenticado, heartbeat e roteamento. Implementar CLI local com registro de raiz. Iniciar por listar arquivos, ler e pesquisar, sem alterações.

Critério: MCP local integrado à ponte lê uma pasta temporária fora do diretório do servidor; testar dispositivo offline, revogado, conta incorreta, raiz não autorizada, mensagem inválida, prazo e limite de tamanho.

### 3. Edições e histórico local

Implementar escrita, patch, snapshots e recuperação local. Encaminhar requisitos e tarefas ao mesmo executor, evitando chamadas indiretas ao VCS da VM.

Critério: edição MCP aparece na pasta real; mudança concorrente é rejeitada; repetição do identificador não duplica escrita; falha de conexão após salvar pode ser reconciliada; rollback restaura o conteúdo local.

### 4. Git e painel

Encaminhar status e diff ao Git local. Exibir dispositivos, estado da conexão, permissões e localização dos projetos. Adaptar editor, árvore e histórico para usar o backend. Recursos ainda não suportados ficam explicitamente indisponíveis para projetos locais.

Critério: painel e MCP observam o mesmo arquivo e diff; nenhuma rota adaptada tenta resolver o caminho local como `/workspace` da VM.

### 5. Aplicativo Windows

Adicionar bandeja, login/pareamento, seletor de pastas, pausa, histórico e inicialização opcional. Empacotar sem exigir Python do usuário e impedir duas instâncias concorrentes com a mesma identidade.

Critério: instalar e executar em Windows limpo, reiniciar o computador, suspender/retomar, perder internet, reconectar e revogar. Documentar distribuição e atualização do executável; não habilitar atualizações sem autenticidade verificada.

### 6. Terminal local opcional

Adicionar permissão independente e aprovação local do comando exato, com validade e consumo único. Comando, saída e histórico ficam locais; encaminhar somente dados necessários. Não reutilizar `PendingCommand` da VM para guardar comandos de projetos locais. Limitar tempo, saída e processos filhos.

Critério: execução ocorre no Windows e na pasta correta, jamais na VM; rejeição e repetição não executam; falhas ambíguas não provocam execução automática. Deixar claro que shell não é sandbox de pasta.

### 7. Validação real e migração

Publicar primeiro em ambiente de teste e conectar um cliente MCP real. Exercitar leitura, pesquisa, edição, conflito, offline, revogação, Git e recuperação após falha. Usar conteúdo marcador para inspecionar banco, logs, arquivos temporários e configurações de proxy da VM, verificando ausência de persistência de payloads pela solução.

Para migrar um projeto existente: transferir uma vez para a pasta escolhida, comparar inventário e hashes, validar pelo MCP e só então planejar remoção explícita de cópias, snapshots e backups anteriores na VM. Não apagar dados nesta fase de implementação.

Critério: demonstração ponta a ponta pela VM e pelo cliente real, além dos testes locais. Build e testes unitários não estabelecem funcionamento no Windows distribuído ou na implantação real.

## Primeiro incremento de código

Implementar as etapas 1 e 2: backend de projeto, schema de localização, pareamento e leitura local via ponte. Validar primeiro o fluxo completo de leitura antes de liberar escrita, terminal ou instalador. O resultado mínimo é uma chamada MCP `read_file` retornando um arquivo que existe apenas na pasta autorizada do computador.

## Fora do escopo inicial

Sincronização bidirecional, cópia permanente para a VM, execução offline pelo GPT, múltiplos computadores escrevendo no mesmo projeto, acesso irrestrito ao disco e substituição do motor de IA. Integrações de banco existentes exigem avaliação separada antes de prometer execução local.
