# REQ-0003 — Gestão de computadores e pastas em Local Devices

## Identificação
- ID: `REQ-0003`
- Projeto: `act-ide-teste` (workspace Act IA 46)
- Origem: solicitação de evolução de `local-devices` em 2026-10-11.
- TAP: `.documents/project-charter.md`, seção 10.
- Estado: aprovado pelo usuário; implementação iniciada no projeto 46 após sincronização Git.

## Objetivo e contexto de negócio
Eliminar a confusão entre identidade do computador, chave de conexão e pastas compartilhadas em `local-devices`. Usuários podem registrar vários computadores e um número não limitado por regra de negócio de pastas vinculadas a cada computador.

## Escopo macro
1. Duas abas, **Computador** e **Dispositivos e pastas**, visíveis na mesma experiência.
2. Aba Computador: se a lista estiver vazia, exibir empty state com CTA **Adicionar dispositivo**; caso exista cadastro, exibir computadores em cards/lista com nome, status, expiração e ação de adicionar outro.
3. Modal: **Nome do computador** (obrigatório), seleção de expiração **1 mês, 3 meses, 9 meses, Nunca**; ação principal **Gerar chave**, persistindo o computador e emitindo credencial.
4. Exibir após geração somente o código temporário de pareamento com opção copiar; o segredo de conexão definitivo é emitido durante o resgate e fica apenas no aplicativo local protegido.
5. Aba Dispositivos e pastas: selecionar computador e cadastrar quantas raízes locais forem necessárias no aplicativo Okestre Local; a VM recebe somente identificadores opacos e nomes, exibe cards, fornece instruções de adição e permite remover o acesso remotamente, com confirmação.
6. Estados de carregamento, vazio, erro, sucesso, validação, teclado e responsividade.

## RFs vinculados
- `RF-0003-01`: estruturar abas, empty state e listagem de computadores.
- `RF-0003-02`: cadastro de computador com emissão de chave e validade.
- `RF-0003-03`: cadastro e remoção de pastas associadas a computador.

## Regras gerais
- Múltiplos computadores por escopo de usuário; identidade por ID imutável, nome exibível não é token ou identificador de segurança.
- Valores válidos de expiração: 1, 3, 9 ou `never`. Registrar instante UTC da criação e `expires_at` opcional; usar mês-calendário, não 30 dias fixos, na implementação.
- Credencial gerada no backend com entropia criptográfica; armazenar apenas resumo irreversível, usar conexão autenticada, nunca escrever segredo em log. A opção nunca requer destaque de risco.
- Pastas sempre pertencem a um computador existente, e só podem ser gerenciadas pelo proprietário autorizado.
- A remoção de pasta apaga o cadastro/vínculo, não o conteúdo do disco local; erros não podem levar à exclusão física.
- Não introduzir limites arbitrários para número de pastas; duplicidade de caminhos normalizados por computador deve ser tratada.
- A aba Pastas, sem computadores, informa a dependência e oferece acesso ao cadastro de computador.
- Emissão/consumo de chave pelo agente local depende de compatibilidade com eventual protocolo já em uso; não substituir contratos existentes sem inventário.

## Fontes de dados e dados necessários
- Repositório persistente já encontrado: SQLite `local_devices.db` via `gitide_server/local_bridge.py`; projetos vinculados permanecem no SQLAlchemy SQLite principal.
- Computador: `id, owner, name, created, token_hash, expires_at, revoked, roots, blocked_roots`. A tabela `pairing` armazena código temporário em hash e duração escolhida.
- Pasta: `root_id`, nome e permissão anunciados pelo agente; o caminho real e a validação física permanecem exclusivamente na configuração local.
- Código de pareamento em claro: somente resposta ao POST de cadastro, uso único/5 minutos; credencial efetiva em claro: somente resposta do claim ao agente. GET/listagem nunca expõem ambos.

## Critérios de aceite macro
- No estado inicial vazio, botão **Adicionar dispositivo** abre modal; o modal exige nome, oferece 1/3/9 meses/nunca e permite gerar chave.
- Um segundo computador pode ser adicionado sem sobrescrever o primeiro.
- Chaves expiram conforme a opção, ou ficam sem vencimento automático em `Nunca`; API não as retorna posteriormente.
- Vários cards de pastas persistem por computador; exclusão remove apenas o card/registro solicitado.
- Trocar computador altera a lista de pastas corretamente, sem vazamento de dados entre computadores.
- Erros de servidor preservam dados do formulário e permitem nova tentativa sem duplicação silenciosa.

## Dependências, premissas e restrições
- Dependências tecnológicas atuais: FastAPI, HTML/JS/CSS estáticos, SQLAlchemy/SQLite, autenticação do GitIDE; verificar localização real da tela antes da implementação.
- A rota `/local-devices` foi localizada após sincronização Git, com UI em `gitide_server/static/local-devices.*` e API em `gitide_server/local_bridge.py`. Os contratos `/api/local/*` serão preservados e estendidos.
- Autorização existente exige sessão de usuário root, token CSRF e isolamento por owner; o protocolo do agente usa código efêmero e token WSS com hash armazenado, preservados e estendidos por expiração.
- Preservar design tokens e contratos; não expor chaves em analytics, logs ou persistência do browser.

## Fora do escopo
Exclusão de arquivos físicos, explorador de arquivos local, exclusão de computador, rotação de chave, provisionamento de agente, execução remota, quotas comerciais.

## Riscos
Riscos atualizados: manutenção da segurança do pareamento e canal WSS; persistência do bloqueio de raiz ao reconectar; token sem expiração; regressão no editor de arquivos local; testes E2E dependem de runtime/autorização de terminal.

## Rastreabilidade e histórico
- TAP: seção 10; RF-0003-01/02/03; Design vivo; RI-0003; Task List RF-0003.
- 2026-10-11: criado para planejamento da reorganização de Local Devices.
- 2026-10-11: aprovado; inventário após sincronização localizou frontend, DeviceStore e agente Windows; especificação adaptada aos contratos seguros existentes.
