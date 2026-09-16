# Act IA MCP

Servidor MCP integrado ao FastAPI, usando o SDK oficial Python (linha 1.x,
fixada em `mcp>=1.30,<2`). Transporte Streamable HTTP, sem sessao persistente.
Referencia: https://py.sdk.modelcontextprotocol.io/v1/

## Executar

Instale as dependencias no ambiente do backend e reinicie o processo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn gitide_server.main:app --host 127.0.0.1 --port 8000
```

O mesmo entrypoint usado pelo Docker ja monta o MCP. Na VM, publique a nova
versao da imagem/backend com as dependencias atualizadas antes de conectar.
Esta implementacao local nao publica nem reinicia a VM automaticamente.

## Conectar

- URL local: `http://127.0.0.1:8000/mcp/`
- URL publica apos deploy: `https://ide.builtt.com.br/mcp/`
- Transporte: Streamable HTTP.
- Header: `Authorization: Bearer <chave da API Act IA>` em todas as chamadas.
- `/mcp` e `/mcp/` funcionam diretamente, sem redirecionamento.
- A chave e a mesma da API, armazenada no servidor em `~/.gitide/config.json`.
  Configure-a no armazenamento de segredos do cliente; nao a coloque no Git.

No ChatGPT, cadastre o plugin com a URL publica e selecione **OAuth**.
O servidor oferece descoberta e registro dinamico de clientes. O navegador
abre o login existente do Act IA e, em seguida, uma tela de aprovacao.
Somente uma conta root ativa pode autorizar. Na tela de aprovacao, escolha
os projetos e entre Somente leitura (padrao) ou Leitura e edicao. A opcao
Todos os projetos, inclusive futuros deve ser marcada explicitamente para
conceder acesso global. Sem essa opcao, pelo menos um projeto e obrigatorio.
O escopo OAuth continua `mcp`; as restricoes sao armazenadas na concessao
e verificadas pelo servidor a cada chamada, inclusive apos renovar o token.
`list_projects` retorna somente os projetos autorizados. `write_file` e
`patch_file` exigem Leitura e edicao; as outras ferramentas permitem leitura.
As ferramentas continuam visiveis na descoberta, mas chamadas sem permissao
sao recusadas antes de acessar arquivos ou registrar alteracoes.

Compatibilidade: tokens anteriores a esta versao mantem o acesso global de
leitura/edicao originalmente autorizado. O Bearer estatico tambem permanece
global. Para restringir uma conexao antiga, revogue a conexao em Configuracoes
> Conexoes MCP e autorize novamente com os projetos desejados. As permissoes
de uma concessao existente nao sao editadas retroativamente.

## Gerenciar conexoes

Em **Configuracoes > Conexoes MCP**, a conta root pode consultar aplicativo,
conta responsavel, projetos, leitura/edicao, autorizacao, ultimo acesso e status.
Cada autorizacao e uma conexao separada, mesmo quando o aplicativo e o mesmo.
Ha paginacao, atualizacao manual e confirmacao antes de revogar.

A revogacao persiste em `mcp_oauth.db` e bloqueia tokens atuais e renovacoes
da conexao, inclusive depois de reiniciar o backend. Requisicoes ja em execucao
nao sao interrompidas. A chave Bearer global nao e uma conexao OAuth e nao
aparece nesta lista. A revogacao OAuth `/revoke` tambem bloqueia a conexao.

O ultimo acesso representa validacao autenticada de um token MCP, incluindo
descoberta de ferramentas, atualizado no maximo uma vez por minuto. Nao e
uma auditoria de operacoes. Conexoes antigas com refresh token valido sao
importadas automaticamente; datas que nao foram registradas aparecem como
"Nao registrado". Conexoes ja expiradas antes da atualizacao podem nao ser
recuperaveis. A lista preserva os registros de conexoes revogadas/expiradas.

Endpoints administrativos (sessao root obrigatoria, sem acesso via token MCP):
`GET /api/mcp/connections?offset=0&limit=25` e
`POST /api/mcp/connections/{connection_id}/revoke`. A listagem retorna um token
CSRF vinculado a sessao, exigido no header `X-CSRF-Token` para revogar. As
respostas usam `Cache-Control: no-store` e nunca retornam segredos OAuth.
O Bearer estatico continua funcionando para os clientes ja configurados.
Nao e um schema para colar na tela de GPT Actions.

## Publicar OAuth

Configure `GITIDE_PUBLIC_URL=https://ide.builtt.com.br` no backend (esse e o
padrao). Use a origem HTTPS publica, sem caminho. Em testes locais use
`http://127.0.0.1:8000` e acesse o servidor por essa mesma origem.
Recrie/reinicie o backend com as dependencias atualizadas. O proxy deve
encaminhar estas rotas ao mesmo backend, sem exigir login no proxy:

- `/.well-known/oauth-authorization-server`
- `/.well-known/oauth-protected-resource/mcp/`
- `/.well-known/oauth-protected-resource/mcp` e `/.well-known/oauth-protected-resource`
- `/register`, `/authorize`, `/token`, `/revoke`
- `/oauth/consent`, `/login`, `/api/auth/login`, `/mcp/`
- `/mcp` (tambem deve chegar ao backend sem redirecionamento no proxy)

Persistir `~/.gitide/mcp_oauth.db` junto com `~/.gitide/config.json` no volume
da instalacao. Os registros OAuth sao cifrados com chave derivada do
`session_secret` existente. Trocar esse segredo invalida o armazenamento OAuth;
preserve o par no backup. Nao compartilhe o banco entre instalacoes com
origens/segredos diferentes. O banco usa SQLite, assim como o backend atual.

O protocolo e processado pelo SDK MCP: codigo de autorizacao com PKCE S256,
callback previamente registrado, escopo `mcp` e audiencia do endpoint MCP.
Codigos duram 2 minutos e sao consumidos uma unica vez; aprovacao dura 10
minutos. Access tokens duram 1 hora; refresh tokens, 30 dias, com rotacao
e invalidacao do par anterior. `/revoke` revoga a conexao correspondente.
Desativar a conta ou remover seu perfil root impede o uso/renovacao dos tokens.
O cadastro dinamico suporta clientes com segredo conforme metadata do SDK.

Na tela do ChatGPT, informe a URL com barra final e selecione OAuth. A
descoberta deve preencher os endpoints; complete login e aprovacao no Act IA.
O fluxo foi testado localmente, mas a conexao real pelo ChatGPT so pode ser
confirmada depois do deploy e da autorizacao no navegador do usuario.
Referencia: https://developers.openai.com/plugins/build/auth

## Ferramentas

| Nome | Parametros principais | Resultado |
| --- | --- | --- |
| `list_projects` | `offset`, `limit` | Projetos com id/nome e proxima pagina |
| `list_files` | `project_id`, `query`, `offset`, `limit` | Arquivos filtrados pelo caminho |
| `read_file` | `project_id`, `filepath`, `start_line`, `limit` | Texto, hash SHA-256 integral e proxima linha |
| `git_status` | `project_id` | Status retornado pelo servico Git existente |
| `write_file` | `project_id`, `filepath`, `content`, `expected_sha256` | Gravacao, snapshot e novo hash |
| `search_files` | `project_id`, `query`, `path_filter`, `case_sensitive`, `offset`, `limit` | Linhas contendo texto literal, com arquivo e numero de linha |
| `patch_file` | `project_id`, `filepath`, `expected_sha256`, `target_content`, `replacement_content`, `allow_multiple` | Substituicao de trecho, snapshot e novo hash |
| `git_diff` | `project_id`, `filepath`, `staged` | Diff de um arquivo rastreado: working tree/index ou index/HEAD |
| `list_requirements` | `project_id`, `query`, `offset`, `limit` | Caminhos Markdown de requisitos e especificacoes, incluindo pastas legadas |
| `read_requirement` | `project_id`, `filepath`, `start_line`, `limit` | Leitura paginada de uma especificacao com hash integral |
| `list_tasks` | `project_id`, `status`, `offset`, `limit` | Tarefas rastreaveis e hash integral do task.md |
| `create_task` | `project_id`, `code`, `title`, `expected_sha256` | Acrescenta uma tarefa pendente com codigo unico |
| `update_task` | `project_id`, `code`, `checked`, `expected_sha256` | Conclui ou reabre uma tarefa pelo codigo |
| `execute_command` | `project_id`, `command`, `command_id` opcional | Solicita aprovacao e executa um comando de shell nao interativo |

### Terminal MCP

Reconecte via OAuth com Leitura e edicao e a opcao explicita de terminal.
Conexoes antigas e chaves API globais nao recebem permissao de executar.
A permissao persiste na renovacao e aparece em Conexoes MCP.

Primeiro chame `execute_command` sem `command_id`. A resposta retorna
`pending_approval` e um identificador. Aprove o comando exato no painel
existente do Act IA e repita a chamada com o mesmo comando e identificador.
Cada aprovacao e consumida uma unica vez; chamadas repetidas nao executam
novamente um identificador consumido. O registro de aprovacao existente guarda
o texto do comando: nao inclua senhas ou tokens nele. Historico MCP e o log
de execucao MCP nao guardam comando ou saida.

O shell roda NO SERVIDOR, com o projeto como diretorio inicial e com os
privilegios e ambiente do processo Act IA. Nao e sandbox: pode acessar outros
arquivos, segredos e rede. `.gitideignore` nao restringe comandos. Use apenas
para contas e projetos confiaveis; a permissao por projeto controla o inicio
da chamada, nao os recursos acessiveis ao shell.

Limites: 30 segundos, 64 KB de stdout/stderr combinados, stdin fechado,
sem sessao persistente ou terminal interativo. Retorna exit_code, timed_out,
truncated e output; saida nao UTF-8 pode conter caracteres substituidos.
No timeout tenta encerrar a arvore/grupo de processos; isto nao impede um
programa de escapar do grupo ou iniciar servicos independentes. Nao use
para servidores em background. Comandos nao possuem rollback nem snapshots
automaticos; revise Git antes e depois. Uma falha apos consumir aprovacao
nao reutiliza essa aprovacao. Revogacao impede novas chamadas, mas nao cancela
um comando que ja esta rodando.

### Requisitos e tarefas

`list_requirements` lista Markdown em `.documents/requirements`,
`.documents/functional-requirements`, `.documents/spec` e `.documents/specs`.
`query` filtra caminhos; `read_requirement` usa os mesmos limites e protecoes
de `read_file`. Esta entrega nao cria nem altera requisitos por ferramenta dedicada.

Tarefas usam `.documents/task/task.md` e o mesmo parser da API REST. Estados:
`pending` (checkbox aberto), `completed` (marcado), ou `all` na listagem.
Nao ha novo estado "em andamento". Identificadores seguem o formato existente,
por exemplo `TASK-RF-0001-01-001`, `TASK-REQ-01-001` ou `TASK-QA-ABC-001`.

Leia `list_tasks` antes de escrever e envie seu `sha256` em `expected_sha256`.
Documento inexistente retorna `missing`. Criacao rejeita codigo duplicado e
titulo vazio/multilinha; atualizacao rejeita codigo ausente ou ambiguo.
Escritas preservam o restante do documento, reutilizam snapshots e ActivityLog
do gravador existente e respeitam a permissao OAuth de edicao. Cada ferramenta
tambem aparece no Historico MCP, sem argumentos ou conteudo.

Criar tarefa acrescenta apenas o item da lista: nao gera `task.details.md`,
nao aprova o pacote Harness nem executa a tarefa. O detalhamento pode ser lido
e editado pelas ferramentas de arquivo existentes, conforme o fluxo do projeto.
As garantias de concorrencia continuam limitadas ao lock do worker MCP e hash;
editores externos e a API REST nao compartilham esse lock.

Fluxo de edicao parcial: `search_files` localiza o trecho, `read_file` fornece
conteudo e hash, `patch_file` substitui o texto exato, `git_diff` revisa o resultado.
A busca e literal por linha (sem regex), ignora binarios e arquivos acima de
1 MiB, respeita as exclusoes e retorna snippets de ate 240 caracteres. Um
snippet pode estar truncado: use `read_file` na linha indicada para ler o trecho.
`next_offset` permite continuar a busca enquanto o projeto permanece estavel.
`skipped_files` conta os arquivos pulados ate o fim da varredura dessa pagina.

O patch exige o hash integral atual e rejeita texto ausente ou ambiguo.
`allow_multiple=true` autoriza substituir todas as ocorrencias. O limite final
continua sendo 1 MiB. O snapshot e o registro FILE_PATCH usam o servico existente.

`git_diff` exige um arquivo e o projeto na raiz do repositorio. Arquivos novos
nao rastreados nao aparecem no diff; consulte `git_status` e `read_file` nesses
casos. O resultado limita-se a 64 KB e sinaliza `truncated`; a execucao tem timeout
de 15 segundos. Nao executa diff externo nem conversores textconv.

Fluxo: listar projetos, selecionar id, listar arquivos, ler arquivo e gravar
o conteudo completo usando o hash retornado. Para criar um arquivo, usar
`expected_sha256: "missing"`; se ja existir, a operacao falha.
Uma leitura paginada nao representa o conteudo completo a ser gravado.
Requisitos e tarefas em Markdown podem ser encontrados por `list_files`
com `query: ".documents/"` e lidos com `read_file`.

## Limites

- Listagens retornam ate 200 itens por pagina; o inventario ainda percorre
  os arquivos do projeto a cada chamada. Status Git reutiliza a resposta da API.
- Leitura/escrita somente de texto UTF-8 ate 1 MiB; pagina de leitura ate
  200 linhas, podendo retornar ate 1 MiB de conteudo. JSON minificado em uma
  unica linha e aceito, sem a antiga trava de 64 KB por pagina.
- Caminhos relativos, confinados ao projeto, inclusive apos resolver links.
  Respeita `.gitideignore` e bloqueia acesso a metadados `.git`.
- A chave global tem acesso a todos os projetos, como na API atual. Novas
  concessoes OAuth possuem restricoes por conexao/projeto e leitura/edicao.
  Cookies nao autenticam chamadas MCP, apenas o login/consentimento.
- O hash detecta alteracoes feitas desde a leitura. O lock serializa chamadas
  de escrita MCP dentro do mesmo worker; nao garante exclusao mutua contra
  editores externos, a API REST ou outros workers.
- Gravacoes reutilizam ActivityLog e os snapshots do servico existente.
  Nao ha ferramentas dedicadas de exclusao ou commit; o shell autorizado pode realiza-los.
- Anotacoes MCP identificam leitura e escrita; confirmacao pelo usuario depende
  do cliente e nao e imposta pelas anotacoes no servidor.

Hosts e Origins sao validados. Para outro dominio, configure listas separadas
por virgula em `GITIDE_MCP_ALLOWED_HOSTS` (host, sem protocolo) e
`GITIDE_MCP_ALLOWED_ORIGINS` (origem, com protocolo). O proxy deve preservar o
Host permitido e o header Authorization e encaminhar `/mcp/` ao backend.

## Integracao Supabase

### OAuth (principal)

Conectar Supabase inicia a autorizacao oficial no painel Supabase. O retorno
abre Integracoes e permite selecionar um projeto remoto e os projetos locais
autorizados. Nao solicita senha PostgreSQL: consultas usam a Management API
via HTTPS. PostgreSQL avancado continua disponivel para conexao direta.

Configuracao unica no servidor (nao coloque segredos no frontend):

```text
SUPABASE_OAUTH_CLIENT_ID=<client-id-do-oauth-app>
SUPABASE_OAUTH_CLIENT_SECRET=<client-secret-do-oauth-app>
GITIDE_PUBLIC_URL=https://ide.builtt.com.br
```

Cadastre o OAuth App em Organization Settings > OAuth Apps do Supabase.
URL de retorno exata para esse dominio:
`https://ide.builtt.com.br/api/integrations/supabase/callback`.
No ambiente local, use uma configuracao/app de teste com GITIDE_PUBLIC_URL
`http://127.0.0.1:8766` e o mesmo caminho de callback. O proxy precisa encaminhar
`/api/integrations/supabase/*` ao backend. Alteracoes de variaveis exigem restart.

Escopos no OAuth App: Projects Read (`projects:read`) para listar projetos e
Database Write (`database:write`) para o endpoint SQL, inclusive SELECT.
Nao solicitar Secrets, Auth, Storage ou permissoes de criacao de projetos.
Os niveis read/write/full do Okestre continuam sendo impostos antes das
chamadas; leituras enviam `read_only: true` ao Supabase. Isso nao reduz os
escopos do token remoto: proteja o backend que o armazena.

PKCE S256 e state descartavel vinculam a autorizacao ao root e a sessao local.
Access/refresh tokens ficam cifrados no banco OAuth, separados dos vinculos
de projeto. Renovacoes sao serializadas e nao ha repeticao automatica de SQL
apos erro. Desconectar autorizacao remove os tokens locais e desativa todos
os vinculos dependentes; para revogar globalmente, use tambem o painel Supabase.
Excluir apenas uma integracao nao remove uma autorizacao usada por outros
vinculos. Uma autorizacao revogada externamente pode exigir nova conexao.

OAuth usa limite de resposta HTTP de 2 MiB e apresenta ate 200 linhas/64 KB.
Timeout de conexao/leitura HTTP: 8s/25s; nao implica cancelamento de uma consulta
ja aceita no Supabase. Nao ha rollback de escritas confirmadas remotamente.
CREATE TABLE/CREATE TABLE AS/SELECT INTO exigem schema explicito e incluem
habilitacao de RLS na mesma transacao enviada ao Supabase. Nao cria politicas
publicas. As aprovacoes de escrita existentes continuam valendo.

Sem Client ID/Secret, o botao informa a configuracao faltante e nao tenta
autorizacao. O fluxo foi validado com respostas simuladas e navegador; a
autorizacao real depende do cadastro OAuth App e das credenciais do servidor.

Referencias oficiais:
- https://supabase.com/docs/guides/integrations/build-a-supabase-oauth-integration
- https://supabase.com/docs/reference/api/v1-list-all-projects
- https://supabase.com/docs/reference/api/v1-run-a-query

### PostgreSQL avancado

Configuracoes > Integracoes permite cadastrar, editar, testar, desativar e
excluir conexoes PostgreSQL do Supabase. Nao gerencia Auth, Storage, Edge
Functions, chaves nem projetos da Management API. Neon fica para outra entrega.
Use os dados do painel Connect do Supabase: host, porta, banco, usuario e
senha PostgreSQL (nao anon/service_role). Hosts diretos `db.<ref>.supabase.co`
e pooler `*.pooler.supabase.com` sao aceitos; self-hosted e dominios customizados
nao sao suportados nesta versao. TLS verifica certificado e hostname usando
as CAs do sistema (libpq 16+; psycopg2-binary 2.9.12 fixado nas dependencias).

Referencia de conexao: https://supabase.com/docs/guides/database/connecting-to-postgres

Permissoes por integracao: `read`, `write` (SELECT e DML), `full` (inclui DDL).
O parser PostgreSQL rejeita multiplas instrucoes, COPY e controle manual de
sessao/transacao. Funcoes fora de uma lista pequena de builtins, casts e outras
construcoes exigem full. Leitura usa transacao READ ONLY. A conta PostgreSQL
deve ter privilegios minimos compativeis com o nivel escolhido: o filtro SQL
nao substitui GRANT/REVOKE, RLS nem isola funcoes, operadores e triggers existentes.
Nao use uma conta privilegiada para acesso de leitura/escrita nao confiavel.
Terminais MCP com acesso ao host nao sao isolados das credenciais do servidor.

Cada chamada exige um projeto autorizado tanto no OAuth quanto na integracao.
Conexoes OAuth somente leitura nao executam escritas mesmo em integracoes full.
Chaves API globais mantem o acesso global existente, limitado pelo perfil da
integracao. `list_integrations` omite credenciais; `database_schema` consulta
colunas visiveis; `database_query` executa uma instrucao por chamada. Resultados
retornam no maximo 200 linhas/64 KB, com `truncated`, e valores nao nulos como
texto. Limites de statement/lock: 15s/3s; conexao: 8s. O driver pode materializar
resultados de escritas com RETURNING antes do corte de saida; evite lotes enormes.
Consultas de estrutura truncadas podem ser refinadas usando database_query.

Aprovacao de TODA escrita vem ativada por padrao, podendo ser desligada pelo
root. O SQL fica pendente nesta tela por dez minutos; apos aprovar, repetir o
SQL exato com `approval_id`. Aprovacao vincula integracao, revisao, projeto,
conexao e SQL, e e consumida antes da execucao. Editar a integracao invalida
aprovacoes anteriores. Falha de rede apos commit pode deixar resultado incerto;
consulte o banco antes de criar outra aprovacao. Desativar/revogar impede novas
chamadas, nao desfaz operacoes ja iniciadas. Nao ha rollback posterior automatico.

CREATE TABLE, CREATE TABLE AS e SELECT INTO habilitam RLS na tabela resultante
antes do commit, inclusive se CREATE IF NOT EXISTS encontrar tabela existente.
Nao sao criadas politicas nem grants publicos automaticamente. Qualifique os
schemas, por exemplo `public.minha_tabela`. Views e funcoes privilegiadas exigem
revisao das regras Supabase de security_invoker/security_definer pelo operador.

Configuracoes completas e SQLs pendentes sao cifrados com o mesmo segredo do
OAuth, em `mcp_oauth.db`. As senhas nao voltam ao frontend; campo vazio numa
edicao preserva a senha. Somente root via sessao e CSRF pode administrar ou
aprovar. Auditoria MCP registra nome da ferramenta/projeto/resultado sem SQL,
senha ou linhas retornadas. Proteja o volume e o par banco/session_secret.
As aprovacoes expiradas ficam armazenadas cifradas; limpeza por retencao ainda
nao foi implementada.

Testes locais usam bancos temporarios e mocks da conexao PostgreSQL. A validacao
real do Supabase deve ser feita por Testar conexao e uma consulta de leitura
num projeto de teste; nao foi executada com credenciais remotas nesta entrega.

## Historico de auditoria

Em Configuracoes > Historico MCP, a conta root pode consultar chamadas por
conexao, projeto, ferramenta, resultado e periodo, com paginacao. Ver conexao
abre o cadastro correspondente, onde a revogacao continua exigindo confirmacao.
A API de consulta e `GET /api/mcp/audit`, restrita a root e sem cache.

Cada chamada de ferramenta registra data, conexao/conta, ferramenta, projeto,
duracao e resultado: sucesso, erro ou acesso negado por permissao de projeto ou
escrita. Autenticacao ausente/invalida registra um evento anonimo sem ferramenta
ou projeto. A chave API global nao identifica uma pessoa individualmente.
As datas da tela usam o fuso local do navegador.

O historico nao armazena tokens, senhas, argumentos, conteudo de arquivos,
resultados ou mensagens brutas de excecao. Os metadados de auditoria ficam na
tabela `mcp_audit` do mesmo `mcp_oauth.db`, sem cifragem adicional desses campos;
proteja o arquivo e seus backups. A coleta comeca apos instalar esta versao:
nao reconstitui chamadas anteriores e ainda nao possui limpeza por retencao.
Falhas de armazenamento geram um aviso generico no log e nao interrompem a
operacao MCP, evitando tratar uma edicao ja concluida como falha de ferramenta.

## Validar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_mcp*.py'
```

Os testes usam banco e workspace temporarios: inicializacao MCP, descoberta,
autenticacao, Origin, paginacao, leitura, escrita com snapshot, conflito de
versao, criacao, projeto inexistente e bloqueios de acesso.
OAuth: descoberta, cadastro dinamico, consentimento e CSRF, PKCE, replay,
callback, audiencia, renovacao, revogacao, expiracao, persistencia e conta root.

O teste opcional `test_mcp_oauth_browser.py` requer `pip install playwright`
no ambiente de desenvolvimento e Microsoft Edge instalado. Ele reproduz o
bloqueio de redirecionamento causado por `form-action 'self'` e verifica que
o callback OAuth registrado e alcancado no primeiro clique com a politica
corrigida. O callback de teste roda exclusivamente em loopback.
