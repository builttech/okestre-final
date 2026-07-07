# REQ-3091 — Rebrand visual Dayact IA-like da ferramenta

## 1.1 Identificação e Metadados Básicos

| Campo | Valor |
|---|---|
| ID | REQ-3091 |
| Título/Resumo | Rebrand visual da ferramenta com base em `design_rebrand.md` |
| Tipo | Requisito de interface / identidade visual |
| Módulo | Interface Web / Design System |
| Prioridade | Alta |
| Status | Aprovado para execução |
| Solicitante | Usuário |
| Responsável atual | Agente IA |
| Release/Iteração | Branch `rebrand` |
| Esforço estimado | Médio |

## 1.2 Contexto

O projeto `git-ide` está na branch `rebrand` e possui o arquivo `design_rebrand.md`, que define um novo direcionamento visual inspirado em Dayact IA. A interface atual possui uma camada `rebrand.css` com estética escura, glassmorphic e acentos coloridos, divergindo da nova proposta clara, minimalista, monocromática e técnica.

## 1.3 Objetivo Funcional

Aplicar uma nova identidade visual à ferramenta, tornando a experiência coerente com o design documentado em `design_rebrand.md`, sem alterar regras de negócio, fluxos funcionais, APIs, endpoints, persistência ou permissões.

## 1.4 Descrição do Requisito

A aplicação deve adotar um sistema visual claro com fundo principal `#f9f4ed`, superfícies claras, texto preto/cinza, acento dominante `#888888`, cantos retos entre 0 e 2px, espaçamento baseado em múltiplos de 16px e tipografia com `Switzer` como primeira preferência de fonte, preservando fallback seguro quando a fonte não estiver instalada ou disponível.

A mudança deve ser aplicada principalmente por tokens e pela camada CSS de rebrand, mantendo a estrutura HTML e JavaScript existentes sempre que possível.

## 1.5 História de Usuário

Como usuário da ferramenta, quero que a interface reflita o novo rebrand documentado para que a experiência visual seja clara, premium, minimalista e consistente em todos os módulos principais do produto.

## 1.6 Regras de Negócio

- A interface deve usar o `design_rebrand.md` como fonte de verdade visual.
- A paleta deve priorizar `#f9f4ed`, `#f4f4f5`, `#ffffff`, `#000000`, `#52525b`, `#888888`, `#aaaaaa` e `#050505`.
- A aparência padrão deve ser clara, não escura.
- Elementos funcionais de alerta, erro e sucesso podem manter cores semânticas discretas quando necessário para compreensão operacional.
- A implementação não deve criar estilos inline novos.
- A lógica da aplicação não deve ser alterada.
- A estrutura de navegação, abas, painéis e formulários deve continuar funcionando como antes.

## 1.7 Restrições e Premissas

- O arquivo `design_rebrand.md` está disponível na raiz do projeto e será tratado como referência visual.
- A fonte Switzer pode não existir localmente no workspace; nesse caso, a pilha CSS deve usar fallback seguro.
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

- [ ] A camada visual padrão passa a usar tema claro compatível com `design_rebrand.md`.
- [ ] Tokens principais refletem a nova paleta, tipografia e cantos retos.
- [ ] Topbar, sidebar, cards, botões, inputs, modais, abas, painéis e áreas de código recebem overrides compatíveis com o rebrand.
- [ ] A marca e o título principal deixam de enfatizar o nome antigo quando aplicável.
- [ ] Não são introduzidos estilos inline novos.
- [ ] A implementação preserva a lógica funcional existente.
- [ ] O workspace é validado por status Git e verificação técnica aplicável.

## 1.10 Rastreabilidade Funcional

| Origem | Artefato |
|---|---|
| Solicitação do usuário | Realizar rebrand da ferramenta seguindo `design_rebrand.md` |
| Fonte visual | `design_rebrand.md` |
| Task técnica | TASK-REQ-3091-001 |
| Design | `.documents/design/design.md` |
| DRI | `.documents/dri/dri.md` |
