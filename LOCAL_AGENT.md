# Okestre Local — primeira versão funcional

Branch: `codex/local-agent-bridge`. Esta versão implementa acesso MCP a arquivos locais e um painel próprio de dispositivos. Não foi publicada na VM.

## O que funciona

- Agente Python ou aplicativo Windows portátil, com bandeja, pareamento, seletor de pastas, leitura/edição, pausa e remoção de compartilhamento.
- Canal de saída WebSocket autenticado; HTTPS/WSS obrigatório fora do localhost. Não exige porta de entrada no computador.
- Cadastro e revogação de dispositivos no painel `/local-devices`, disponível pelo ícone de computador no topo do Okestre.
- Vínculo entre projeto e pasta por identificador opaco. Caminhos absolutos locais não são enviados à VM.
- MCP: `list_files`, `read_file`, `search_files`, `write_file`, `patch_file`, requisitos e tarefas.
- Escrita condicionada a SHA-256, substituição atômica e histórico local da versão anterior.
- Deduplicação durável do identificador de uma mutação recebida pelo agente. Operações interrompidas em estado ambíguo não são repetidas automaticamente.
- Painel web com leitura paginada completa, edição, criação de arquivos em pastas existentes e detecção de conflito.
- Configuração e credencial protegidas com DPAPI do usuário Windows. Não existe chave OpenAI no agente.

## Iniciar pelo código

No repositório, instale as dependências do servidor no ambiente usado pela VM. Para a ponte, use **um único worker e uma única réplica**:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn gitide_server.main:app --host 127.0.0.1 --port 8000 --workers 1 --ws-max-size 8388608
```

O agente tem dependências separadas:

```powershell
python -m pip install -r requirements-local.txt
python -m okestre_local gui
```

Usar a CLI é opcional:

```powershell
python -m okestre_local pair https://sua-vm.example
# Informe o código de pareamento no prompt oculto.
python -m okestre_local add C:\projetos\meu-projeto --name "Meu projeto" --write
python -m okestre_local run
```

Sem `--write`, a pasta fica somente leitura. O agente não cria subpastas implicitamente: para tarefas novas, prepare `.documents/task` no computador.

## Conectar ao GPT

1. Acesse o Okestre na VM com sua sessão root e abra `/local-devices`.
2. Informe o nome do computador e gere um código válido por cinco minutos, de uso único.
3. Abra o aplicativo local, clique em **Parear** e informe o endereço da VM e o código.
4. Adicione uma pasta de projeto e escolha se permite edição.
5. No painel da VM, clique em **Atualizar** e depois em **Vincular projeto** junto à pasta.
6. Autorize o projeto na conexão OAuth do GPT. Concessões anteriores restritas a outros projetos não recebem acesso automaticamente.
7. Solicite `list_projects` e `read_file` para o novo projeto.

Projetos locais exigem identidade OAuth da mesma conta que pareou o dispositivo. O Bearer global legado não dá acesso a eles. A sessão web autenticada dessa conta pode usar o painel próprio. Reparear exige cadastrar novamente as pastas; revogue a identidade anterior no painel.

## Executável Windows

```powershell
python -m pip install -r requirements-local.txt pyinstaller
.\scripts\build-local-agent.ps1 -Python .venv\Scripts\python.exe
```

Resultado: `outputs/okestre-local/OkestreLocal/OkestreLocal.exe`. Distribua **a pasta inteira**, incluindo `_internal`, ou o ZIP gerado para entrega. É um aplicativo portátil; não há instalador, assinatura de código ou atualização automática nesta versão. A inicialização automática com o Windows ainda não foi implementada.

Fechar a janela mantém o programa na bandeja. Use **Sair** no ícone para desconectar e encerrar. Somente uma instância pode usar o mesmo diretório de configuração.

O diretório padrão é `%LOCALAPPDATA%\OkestreLocal`. A configuração fica em `config.protected`; `history.sqlite3` contém snapshots e registros locais. Proteja esse diretório e inclua-o na sua política de backup. Os snapshots ficam em texto/binário local, sem criptografia adicional. A credencial DPAPI pertence ao usuário Windows e não deve ser copiada para outro computador.

## Consultar e restaurar histórico

Encerre o agente antes de usar os comandos de manutenção abaixo:

```powershell
python -m okestre_local history
python -m okestre_local restore ID_DO_SNAPSHOT --expected-sha256 HASH_ATUAL_DO_ARQUIVO
```

O hash precisa corresponder ao conteúdo atual. A restauração preserva o conteúdo substituído em outro snapshot. Snapshots de criação não removem arquivos; exclusão não faz parte desta versão. Histórico gráfico e política de retenção ainda estão pendentes: monitore o espaço usado pelo banco local.

## Implantação da VM

- Preserve o volume `~/.gitide`, incluindo `local_devices.db`, `gitide.db` e os bancos/configurações OAuth existentes.
- O schema de projetos recebe três colunas adicionais automaticamente. Projetos existentes continuam no modo `server`; nenhum arquivo é transferido ou apagado por essa migração.
- O proxy deve permitir upgrade WebSocket em `/api/local/connect`, além das rotas HTTPS já existentes. Configure timeout ocioso superior a 45 segundos e limite de frame de 8 MiB.
- Mantenha **um processo e uma réplica**. O mapa de conexões e pedidos existe somente em memória; múltiplos workers exigem outra camada de roteamento, ainda não implementada.
- Desative captura de corpos de requisições/respostas, frames e credenciais no proxy/APM. A ponte não persiste payloads, mas uma configuração externa de observabilidade pode fazê-lo. Não habilite logs de frames WebSocket.
- Em queda/reinício, as conexões são restabelecidas. Não há fila persistente de pedidos. Ao perder uma resposta de escrita, leia o arquivo para reconciliar o resultado antes de tentar novamente.
- Antes da atualização, faça backup do banco de metadados. Para voltar a uma versão antiga sem suporte a projetos locais, restaure esse backup; o código antigo não deve operar sobre registros `device`.

## Limites explícitos

- Git, terminal, integrações de banco e execução do agente de IA da VM não estão disponíveis para projetos locais neste incremento. O MCP devolve indisponibilidade; não executa na VM como alternativa.
- Rotas antigas `/api/projects/{id}/...` são bloqueadas para projetos locais. Ao selecionar um projeto local, a interface abre o novo painel. A integração completa com as demais abas está pendente.
- Textos UTF-8 de até 1 MiB; até 200 linhas por página; inventário limitado a 20 mil entradas por chamada. Mensagens até 8 MiB, até oito pedidos pendentes por dispositivo e prazo padrão de 30 segundos.
- A política bloqueia segredos comuns, metadados Git, diretórios internos/dependências, caminhos especiais Windows, links simbólicos, junctions e hard links. Não equivale a detecção universal de segredos em qualquer arquivo.
- A troca de arquivo é atômica; o hash é conferido novamente antes da troca. Editores externos não participam do lock do agente, portanto não existe uma transação distribuída com o VS Code.
- Computador desligado, pasta removida ou agente pausado significa indisponibilidade. Não há cópia de contingência na VM.
- Relógios do computador e da VM precisam estar sincronizados para validar os prazos.
- O conteúdo solicitado transita pela VM e pelo serviço de IA. Armazenamento local do projeto não significa que seu conteúdo nunca saia da máquina.

## Verificação

```powershell
python -m pytest tests/test_local_agent.py tests/test_local_bridge.py tests/test_local_main.py tests/test_mcp_server.py tests/test_mcp_oauth.py -q
# Teste de interface opcional: pip install playwright e Microsoft Edge instalado.
python -m pytest tests/test_local_devices_browser.py -q
```

Os testes da ponte usam HTTP/MCP e WebSocket reais no loopback, com arquivos temporários separados do banco do servidor. Exercitam leitura/edição, hash, snapshots locais, replay, isolamento de conta, grants, CSRF, revogação, pausa, caminhos inseguros e migração de schema. A aplicação real é importada em um perfil temporário isolado no teste de integração.

O teste do painel usa Edge em desktop e largura móvel. O executável oferece `--home DIRETORIO_TEMPORARIO self-test`, que verifica DPAPI, leitura local e inicialização Tk. Esses testes não substituem instalação em Windows limpo, suspensão/retomada, proxy HTTPS público ou conexão real do GPT à VM, que permanecem pendentes.

Validação em 2026-10-11: 57 testes da bateria principal passaram, além de um teste adicional que executou o aplicativo Windows empacotado e confirmou leitura e gravação via MCP/WebSocket reais no loopback (58 testes distintos). O self-test do executável terminou com código zero; JavaScript e diff passaram nas verificações de sintaxe/espaçamento. Capturas do painel desktop e móvel e o log de build estão em `outputs/local-bridge-qa`, fora do Git.
