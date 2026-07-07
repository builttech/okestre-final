# REQ-3091 — Rebrand visual dark technical console da ferramenta

## 1.1 Identificação e Metadados Básicos

| Campo | Valor |
|---|---|
| ID | REQ-3091 |
| Título/Resumo | Rebrand visual dark technical console baseado na referência visual enviada |
| Tipo | Requisito de interface / identidade visual |
| Módulo | Interface Web / Design System |
| Prioridade | Alta |
| Status | Em correção aprovada |
| Solicitante | Usuário |
| Responsável atual | Agente IA |
| Release/Iteração | Branch `rebrand` |
| Esforço estimado | Médio |

## 1.2 Contexto

O projeto `git-ide` está na branch `rebrand`. A primeira aplicação do rebrand seguiu uma leitura clara/light de `design_rebrand.md`, mas o usuário informou que a referência visual correta para esta etapa é dark theme, com estética fiel ao painel técnico apresentado na imagem de referência: console operacional escuro, bordas finas, layout técnico, tipografia mono/condensada, labels em caixa alta e acentos mínimos para estados.

## 1.3 Objetivo Funcional

Aplicar uma nova identidade visual dark à ferramenta, tornando a experiência coerente com a referência visual enviada, sem alterar regras de negócio, fluxos funcionais, APIs, endpoints, persistência ou permissões.

## 1.4 Descrição do Requisito

A aplicação deve adotar um sistema visual dark técnico, com fundo quase preto, painéis retangulares com bordas finas, divisórias sutis, tipografia técnica/monospace para navegação, labels e metadados, texto principal claro, texto secundário azul acinzentado, acentos verdes para estados ativos/sucesso e vermelho para live/error. A interface deve evitar glassmorphism colorido, gradientes decorativos, cantos arredondados grandes e aparência clara.

A mudança deve ser aplicada principalmente por tokens e pela camada CSS de rebrand, mantendo a estrutura HTML e JavaScript existentes sempre que possível.

## 1.5 História de Usuário

Como usuário da ferramenta, quero que a interface reflita fielmente a referência dark technical console para que a experiência visual seja precisa, operacional, premium e consistente com o produto desejado.

## 1.6 Regras de Negócio

- A interface deve usar a imagem de referência enviada pelo usuário como fonte visual prioritária para esta etapa.
- A aparência padrão deve ser dark, não light.
- A paleta deve priorizar fundo quase preto baseado no token Black 950 `#050505`, painéis escuros, bordas claras sutis, texto branco/cinza, texto secundário azul acinzentado, verde para estados ativos e vermelho para estados live/erro.
- A tipografia deve favorecer aparência técnica, compacta e monospace/condensada em navegação, labels, metadados, botões e tabelas.
- Botões primário, secundário e terciário devem seguir uma hierarquia visual global consistente em todas as páginas e módulos.
- Os cantos devem permanecer retos ou quase retos, entre 0 e 2px.
- A implementação não deve criar estilos inline novos.
- A lógica da aplicação não deve ser alterada.
- A estrutura de navegação, abas, painéis e formulários deve continuar funcionando como antes.

## 1.7 Restrições e Premissas

- A referência visual enviada pelo usuário define a prioridade estética desta correção.
- A fonte exata da referência pode não existir localmente; nesse caso, a pilha CSS deve usar fallback seguro com fontes monospace/sistema.
- A mudança deve preservar compatibilidade com os arquivos estáticos atuais.
- A aplicação usa `gitide_server/static/rebrand.css` como camada final de estilo, carregada após os estilos base.
- Não serão adicionados arquivos binários de fonte.

## 1.8 Fora do Escopo

- Alterar comportamento de APIs, rotas ou banco de dados.
- Reescrever componentes JavaScript.
- Alterar fluxos de autenticação, Git, banco de dados, terminal ou agente IA.
- Criar novo framework de UI.
- Adicionar dependências externas obrigatórias.
- Fazer deploy.

## 1.9 Critérios de Aceite

- [ ] A camada visual padrão passa a usar tema dark compatível com a referência visual enviada.
- [ ] Tokens principais refletem a nova paleta dark, tipografia técnica e cantos retos.
- [ ] Topbar, sidebar, cards, botões, inputs, modais, abas, painéis, tabelas e áreas de código recebem overrides compatíveis com o rebrand dark.
- [ ] Botões primário, secundário e terciário ficam visualmente uniformes e consistentes em todos os módulos principais.
- [ ] A interface deixa de usar o override claro aplicado anteriormente.
- [ ] Não são introduzidos estilos inline novos.
- [ ] A implementação preserva a lógica funcional existente.
- [ ] O workspace é validado por status Git e verificação técnica aplicável.

## 1.10 Rastreabilidade Funcional

| Origem | Artefato |
|---|---|
| Solicitação do usuário | Corrigir rebrand para dark theme fiel à referência visual enviada |
| Fonte visual | Imagem de referência enviada no chat |
| Correção cromática | Black 950 `#050505` como base obrigatória do dark theme |
| Task técnica inicial | TASK-REQ-3091-001 |
| Task técnica de correção | TASK-REQ-3091-002 |
| Task técnica de botões | TASK-REQ-3091-006 |
| Task técnica de correção cromática | TASK-REQ-3091-008 |
| Design | `.documents/design/design.md` |
| DRI | `.documents/dri/dri.md` |
