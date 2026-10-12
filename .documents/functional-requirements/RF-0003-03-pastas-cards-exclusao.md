# RF-0003-03 — Pastas por computador, cards e exclusão

## Identificação
- REQ pai: `REQ-0003` | Projeto: `act-ide-teste`
- Interface: `RI-0003` | Status: aprovado/em execução

## Objetivo e história do usuário
Como usuário, quero cadastrar qualquer quantidade de pastas ligadas a um computador, vê-las em cards e remover associações que não utilizo mais.

## Fluxo funcional
1. Na aba **Dispositivos e pastas**, selecionar o computador.
2. Sem computador, exibir indicação e ação para aba **Computador**; sem pastas, exibir empty state e CTA **Adicionar pasta**.
3. O modal Adicionar pasta explica o cadastro no aplicativo Okestre Local, onde o usuário escolhe nome, caminho físico e permissão; a VM não solicita caminho absoluto nem cria acesso físico remoto.
4. Após o agente publicar o compartilhamento, apresentar card com nome, permissão e computador, com botão acessível **Excluir pasta**; não exibir caminho absoluto na VM.
5. Pedir confirmação indicando claramente **Remover cadastro** (não apagar conteúdo do computador).
6. Após resposta positiva, registrar bloqueio durável da raiz no servidor, retirar do canal WSS e ocultar o card. Os arquivos locais permanecem intocados, inclusive após reconexão.

## Regras de negócio
- Número ilimitado de cadastros de pastas por regra de negócio; implementar paginação se necessário por performance.
- Toda pasta possui `computer_id`; nenhuma ação pode afetar outros computadores ou usuários.
- Não remover arquivos ou diretórios do sistema operacional em nenhum momento deste fluxo.
- Caminhos são validados apenas no agente local, nunca recebidos, normalizados ou executados como comandos na VM.
- Duplicidade de caminhos físicos é rejeitada pelo agente local. O servidor utiliza somente identificadores opacos de raiz.
- Exclusão é idempotente, sem efeitos físicos; usuário recebe feedback de sucesso/erro.

## APIs e dados propostos
- `GET /api/local/devices`: inclui raízes publicadas pelo agente e autorizadas, sem caminhos locais.
- Cadastro físico: `Config.add_root()` no aplicativo local, com anúncio em WSS após reconexão.
- `POST /api/local/remove-root`: `{device_id,root_id}` com CSRF e sessão root; registro persistente em `blocked_roots` de `local_devices.db`.
- `POST /api/local/bind`: vínculo opcional de projeto com raiz autorizada; vínculo anterior não autoriza acessar raiz bloqueada.

## Critérios de aceite
- 0 pastas: empty state com ação Adicionar pasta que orienta a inclusão no aplicativo local.
- 3+ pastas: cards independentes, sem limite por regra de negócio.
- Excluir uma mantém as demais; outra máquina não perde cards.
- Confirmação alerta que só o vínculo é apagado; nenhum diretório físico é tocado.
- Falhas mostram feedback; cards são navegáveis via teclado e responsivos.

## Riscos, restrições e rastreabilidade
- Navegação e verificação física de pastas são responsabilidade do agente no dispositivo, não do servidor; nenhum caminho absoluto é registrado na VM.
- Nenhuma sincronização real de arquivos é introduzida.
- REQ-0003; Design; RI-0003; tasks TASK-RF-0003-03-*.
- Histórico: 2026-10-11 — criado.
