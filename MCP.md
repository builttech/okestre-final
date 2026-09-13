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
Somente uma conta root ativa pode autorizar. O escopo `mcp` concede acesso
a todas as ferramentas e projetos; a tela de aprovacao explicita esse acesso.
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
e invalidacao do par anterior. `/revoke` revoga o par de tokens correspondente.
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
  200 linhas e 64 KB. Linhas maiores precisam ser tratadas pela API existente.
- Caminhos relativos, confinados ao projeto, inclusive apos resolver links.
  Respeita `.gitideignore` e bloqueia acesso a metadados `.git`.
- A chave global tem acesso a todos os projetos, como na API atual. Nao ha
  ACL individual por usuario/projeto neste adaptador. Cookies nao autenticam MCP.
- O hash detecta alteracoes feitas desde a leitura. O lock serializa chamadas
  de escrita MCP dentro do mesmo worker; nao garante exclusao mutua contra
  editores externos, a API REST ou outros workers.
- Gravacoes reutilizam ActivityLog e os snapshots do servico existente.
  Nao ha ferramentas de exclusao, shell ou commit nesta versao.
- Anotacoes MCP identificam leitura e escrita; confirmacao pelo usuario depende
  do cliente e nao e imposta pelas anotacoes no servidor.

Hosts e Origins sao validados. Para outro dominio, configure listas separadas
por virgula em `GITIDE_MCP_ALLOWED_HOSTS` (host, sem protocolo) e
`GITIDE_MCP_ALLOWED_ORIGINS` (origem, com protocolo). O proxy deve preservar o
Host permitido e o header Authorization e encaminhar `/mcp/` ao backend.

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
