# Substituição do motor de IA pelo OpenAI Agents SDK

Data: 09/10/2026
Status: planejamento; implementação não iniciada.
Projeto: `C:\Users\augus\.workspace\act\git-ide`

## Objetivo e decisão

Substituir integralmente a orquestração própria pelo Agents SDK Python. O produto terá um único motor de IA: sem fallback silencioso para o loop antigo, sem parser de texto para simular chamadas de ferramentas e sem duas implementações permanentes.

Preservar interface, recursos do projeto, arquivos existentes e serviços de negócio que funcionam. Corrigir ferramentas defeituosas durante a migração: a troca de orquestrador não corrige automaticamente operações de arquivo, banco, Git ou infraestrutura.

“100% SDK” significa que toda execução de modelos da aplicação passa pela camada baseada no SDK, incluindo gerações pontuais com saída estruturada. HTTP de integrações externas, regras de acesso, armazenamento e execução de ferramentas continuam sendo responsabilidades do backend.

## Base confirmada no código

- `gitide_server/agent.py`: `call_llm` chama OpenAI, Gemini e Ollama via HTTP; `extract_json` recupera respostas; `run_agent_loop` coordena ferramentas com limite de 12 ou 50 passos.
- `execute_agent_tool` implementa arquivos, comandos, SQL, Git e documentos. Resultados de ferramentas são reenviados como mensagens de usuário no fluxo atual.
- `gitide_server/main.py`: `/api/projects/{project_id}/agent/run` transmite eventos SSE; existem endpoints de configuração e histórico por projeto.
- Há ferramentas adicionais de QA e Ops Infra registradas em `_native_agent_ops_tools` e descritas em texto.
- Outras rotas chamam `call_llm` para documentos, estimativas e demais gerações: a migração precisa cobri-las também.
- `requirements.txt` inspecionado não declara `openai-agents`.

Esta base resulta de leitura do código, não de testes em runtime. Ainda é necessário inventariar todos os consumidores, permissões e defeitos reproduzíveis.

## Arquitetura proposta

Interface existente → API FastAPI → serviço de execução → Agent/Runner → ferramentas tipadas → serviços de negócio existentes.

Criar um pacote dedicado, por exemplo `gitide_server/ai/`, com separação entre runtime, agentes, ferramentas, sessões, eventos, políticas e configuração. Conferir convenções e conteúdo existente antes de definir os arquivos finais.

- Um agente principal inicialmente; especialistas apenas se uma necessidade concreta justificar.
- Ferramentas com schemas explícitos e validação de argumentos. O servidor injeta usuário, projeto e permissões; o modelo não escolhe sua própria identidade ou escopo.
- Ferramentas recebem contexto de execução, sem compartilhar uma sessão SQLAlchemy entre tarefas concorrentes.
- Histórico conversacional persistido pelo mecanismo de sessões do SDK, com isolamento por projeto, usuário e conversa conforme o modelo de autenticação existente.
- Registro de execução da aplicação separado do histórico: identificador, estado, timestamps, eventos, consumo, falhas e aprovações.
- Estados mínimos: queued, running, awaiting_approval, completed, failed, cancelled e interrupted. Reiniciar o servidor deve identificar execuções interrompidas; retomada automática só onde comprovadamente segura.
- SSE desacoplado da vida útil da execução. Reconectar observa a mesma execução por identificador e cursor, sem reenviar o pedido nem repetir ferramentas.
- Cancelamento e limites de turnos, duração, tamanho de resultados e consumo. Reportar quando uma operação externa não puder ser cancelada.
- Eventos visíveis descrevem ações, ferramentas e resultados; não dependem de um campo de raciocínio privado do modelo.

## Provedores e compatibilidade

OpenAI será o primeiro provedor validado. Preservar a intenção de suporte a Gemini e Ollama usando adaptadores compatíveis com o SDK, após testar chamadas de ferramentas, saída estruturada e streaming para cada combinação de modelo e provedor.

Não declarar suporte universal nem manter o motor antigo para contornar incompatibilidades. Combinações incompatíveis devem ser identificadas na configuração, com erro claro. Se a paridade não for possível, registrar a limitação para uma decisão de produto antes da ativação final.

Selecionar e fixar uma versão compatível do SDK durante a implementação. Confirmar APIs na documentação e no pacote instalado; não presumir que estado persistido do SDK equivale a uma fila durável de trabalho.

## Etapas de execução

### 1. Inventário e reprodução dos problemas

- [ ] Ler instruções aplicáveis do repositório e registrar o estado Git, preservando alterações existentes.
- [ ] Mapear todos os usos de `call_llm`, `extract_json`, `run_agent_loop`, configuração, histórico e eventos da interface.
- [ ] Catalogar ferramentas principais e extras, entradas, efeitos, permissões e consumidores externos/MCP.
- [ ] Reproduzir falhas reais em arquivos, QA, documentos, Git e Ops Infra sem operar produção.
- [ ] Definir uma matriz de paridade: funcionalidade atual → destino SDK → teste → resultado.

Entrega: inventário verificável e casos que demonstram os problemas atuais.

### 2. Fundação do runtime

- [ ] Instalar versão fixada de `openai-agents` e validar dependências Python/MCP.
- [ ] Implementar configuração e adaptação de provedor/modelo, reutilizando armazenamento seguro apropriado.
- [ ] Integrar um Agent/Runner com ferramentas somente de leitura para validar o caminho completo.
- [ ] Implementar contexto de projeto, erros normalizados e limites de execução.
- [ ] Configurar tracing com decisão explícita sobre exportação e ocultação de dados sensíveis.

Entrega: pedido real atravessa API, SDK, ferramenta e interface, com resultado verificável.

### 3. Migração e correção das ferramentas

- [ ] Migrar leitura, escrita e patch, preservando confinamento de caminhos e snapshots.
- [ ] Migrar status/branches e operações Git de escrita com escopo e efeitos explícitos.
- [ ] Migrar documentos e ferramentas QA, incluindo consulta da anotação antes da execução relacionada.
- [ ] Migrar comandos locais com timeout, controle de processo, saída limitada e diretório validado.
- [ ] Revisar SQL: remover necessidade de expor credenciais ao modelo quando houver perfis seguros; aplicar classificação de operação, limites e políticas de escrita do produto.
- [ ] Migrar Ops Infra, mantendo regras de autorização dos serviços e validando efeitos remotos.
- [ ] Aplicar a mesma política de habilitação às ferramentas principais e extras.
- [ ] Integrar aprovações necessárias via SDK, vinculadas à execução, ferramenta e argumentos exatos; aprovar não pode repetir ação concluída.

Entrega: ferramentas tipadas com paridade funcional e erros reais expostos ao agente e à interface.

### 4. Sessões, execução persistida e interface

- [ ] Implementar armazenamento de conversas, execuções, eventos e aprovações pendentes.
- [ ] Importar histórico antigo como mensagens de conversa, sem executar novamente ações registradas.
- [ ] Preservar backups e tornar importação idempotente; definir tratamento de registros incompletos.
- [ ] Adaptar SSE e interface para texto incremental, ferramenta iniciada/concluída, aprovação, erro, cancelamento e conclusão.
- [ ] Reconectar usando cursor; impedir pedidos duplicados e definir serialização por conversa.
- [ ] Persistir estado suficiente para retomar aprovações usando as APIs suportadas do SDK.
- [ ] Definir recuperação após restart: sinalizar interrupção, reconciliar efeitos e nunca repetir automaticamente uma escrita de resultado incerto.

Entrega: continuidade de conversa e estados confiáveis, incluindo queda da conexão e reinício do servidor.

### 5. Migração das demais chamadas de IA

- [ ] Migrar cada rota de geração para o novo serviço baseado em SDK.
- [ ] Usar saídas tipadas/estruturadas quando houver contrato de dados, sem reparação manual de JSON.
- [ ] Manter regras de validação de negócio, inclusive estimativas incompletas ou inconsistentes.
- [ ] Validar Gemini/Ollama no novo motor ou registrar claramente combinações não suportadas.

Entrega: nenhum consumidor da aplicação depende das chamadas HTTP antigas ao modelo.

### 6. Validação, ativação e remoção do legado

- [ ] Executar testes de integração e verificações reais descritas abaixo.
- [ ] Validar o fluxo na interface, incluindo aprovação e reconexão.
- [ ] Remover loop antigo, parsers de recuperação, configurações obsoletas e referências sem consumidores.
- [ ] Conferir por busca e execução que todos os caminhos de IA usam o novo serviço.
- [ ] Documentar configuração, modelos validados, limitações, atualização e operação.
- [ ] Ativar a versão com SDK após passar os critérios de aceite.

Reversão: restaurar a versão anterior e o backup compatível de dados se necessário. O legado não permanece como motor alternativo dentro da nova versão. Durante desenvolvimento, o novo caminho pode ser isolado sem executar ambos sobre a mesma solicitação.

## Critérios de aceite

| Cenário | Evidência necessária |
| --- | --- |
| Ler arquivo | Conteúdo e caminho corretos, restritos ao projeto autorizado |
| Alterar arquivo | Diff esperado, snapshot preservado e resultado conferido no disco |
| Ferramenta falha | Erro visível, sem mensagem falsa de sucesso |
| Ferramenta desabilitada | Não executa, inclusive ferramentas extras |
| Aprovar/rejeitar ação | Rejeição sem efeito; aprovação executa uma única vez com os argumentos aprovados |
| QA | Anotação correta consultada e status coerente com resultado validado |
| Documento/estimativa | Saída abre ou valida no formato requerido e satisfaz regras de negócio |
| Comando | Exit code, timeout, cancelamento e saída tratados corretamente |
| Banco | Leitura limitada e escrita sujeita às regras de acesso, em ambiente de teste |
| Git/Ops Infra | Operação verificada em repositório/ambiente descartável; nenhuma publicação implícita |
| Sessão | Continuidade sem cruzar usuários, projetos ou conversas |
| Reconexão/restart | Estado correto; pedido e efeitos de escrita não duplicados |
| Limites | Execução termina com motivo explícito ao atingir limite |
| Provedor | Cada combinação anunciada passa por ferramentas, saída estruturada e streaming |
| Remoção do legado | Ausência de consumidores do loop/parser antigo e de fallback oculto |

Usar testes determinísticos para políticas, eventos, idempotência e isolamento; testes de integração para serviços; chamadas reais limitadas para validar o SDK com o provedor; navegador para o fluxo do usuário. Separar resultados de código, backend, navegador e serviços externos. Chaves serão configuradas conforme o fluxo de credenciais aplicável na implementação, sem gravá-las no plano ou nos logs.

## Definição de concluído

Todas as capacidades do inventário foram migradas e validadas, ou tiveram uma limitação de produto explicitamente resolvida. O motor antigo não participa de nenhuma execução. A interface reflete resultados e interrupções corretamente. Documentação e procedimento de reversão estão disponíveis. Não declarar 100% funcional com base apenas em instalação, importação ou testes simulados.

## Referências

- SDK: https://openai.github.io/openai-agents-python/
- Execução: https://openai.github.io/openai-agents-python/running_agents/
- Tracing: https://openai.github.io/openai-agents-python/tracing/
- Fontes locais: `gitide_server/agent.py`, `gitide_server/main.py`, `gitide_server/static/app.js`, `requirements.txt`.
