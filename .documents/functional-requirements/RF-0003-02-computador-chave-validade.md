# RF-0003-02 — Cadastro de computador, chave e validade

## Identificação
- REQ pai: `REQ-0003` | Projeto: `act-ide-teste`
- Interface: `RI-0003` | Status: aprovado/em execução

## Objetivo e história do usuário
Como usuário, quero nomear um computador e emitir uma chave válida por 1, 3, 9 meses ou sem vencimento automático, para conectar dispositivos distintos com credenciais rastreáveis.

## Fluxo funcional
1. Clicar em **Adicionar dispositivo** abre modal focado em **Nome do computador**.
2. Informar nome (obrigatório, aparado, tamanho máximo definido em contrato) e escolher expiração: 1, 3, 9 meses ou Nunca.
3. Acionar **Gerar chave**; desabilitar duplo envio, validar, chamar API autenticada.
4. API cria um pareamento temporário com código criptograficamente aleatório (5 minutos, uso único); registra a duração pretendida para a credencial definitiva.
5. Mostrar e permitir copiar apenas o código temporário de pareamento. O agente local troca esse código por credencial definitiva via `claim`, recebendo o token diretamente sem sua exposição na interface web.
6. Fechar modal e atualizar lista, exibindo computador pendente até o resgate do código; depois mostrar status online/offline, validade e expiração.

## Regras e permissões
- Somente sessão/identidade autorizada pode criar e listar; recusar acesso cruzado.
- Expiração definida no servidor usando meses-calendário a partir do UTC de emissão; `Never` grava `expires_at=null`.
- Credencial criptograficamente aleatória; backend guarda somente hash e metadados, com comparação segura quando usada.
- Não incluir a chave em log, analytics, URL, estado global persistido, banco em texto plano ou respostas GET.
- Emissões só após confirmação do backend; tentativa falha não pode deixar computador sem chave.
- Se usuário selecionar Nunca, exibir alerta sobre risco e orientar revogação futura (não implementar revogação nesta entrega).
- Segurança da credencial não altera autenticação existente sem teste de regressão.
- Tratamento de colisão, duplicidade de envio e erro transacional; considerar idempotência na API.

## Dados, contratos propostos e validações
- `POST /api/local/pair`: `{name, expires_in_months: 1|3|9|null}`, com sessão root e CSRF.
- Resposta: `{code, expires_in:300, expires_in_months}` com `Cache-Control: no-store`; o código não é a credencial final.
- `POST /api/local/claim`: emissão do segredo final diretamente ao agente; `GET /api/local/devices` devolve metadados sem código, token ou hash.
- Nome vazio, valor de expiração inválido, falha de sessão e erro de persistência geram mensagens específicas.

## Critérios de aceite
- Modal contém os campos/ações solicitados; opções são exatamente 1/3/9 meses/nunca.
- O backend gera uma chave diferente por computador, sem guardar texto puro.
- O código temporário pode ser copiado no modal imediatamente após emissão, não é reenviado por GET. A chave final nunca é devolvida à interface web.
- A API calcula corretamente data de expiração e informa estado expirado quando aplicável.
- Falha ao gerar não produz cadastro inconsistente nem duplica registros por clique repetido.

## Dependências e fora do escopo
- Integração com agente local e revogação existentes são preservadas; rotação fica fora deste escopo.
- Não enviar chave por e-mail; não armazenar em `localStorage`.
- REQ-0003; Design; RI-0003; tasks TASK-RF-0003-02-*.
- Histórico: 2026-10-11 — criado.
