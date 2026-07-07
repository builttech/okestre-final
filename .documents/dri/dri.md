# DRI — Documento de Requisito de Interface do Projeto

## Projeto

git-ide

## 1. Identificação da Interface

| Campo | Valor |
|---|---|
| REQ | REQ-3091 |
| Interface | Shell principal do GitIDE e módulos internos |
| Tipo | Rebrand visual / Design System |
| Fonte visual | Imagem de referência dark technical console enviada pelo usuário |
| Status | Correção aprovada para execução |

## 2. Contexto de Uso

| Item | Descrição |
|---|---|
| Usuários | Operadores e desenvolvedores usando o GitIDE |
| Ambiente | Aplicação web local/servida pelo backend do projeto |
| Objetivo da interface | Oferecer experiência dark, técnica, operacional e fiel à referência visual |

## 3. Arquitetura da Informação

| Área | Papel na experiência |
|---|---|
| Topbar | Marca, status do servidor, token e ações globais em linha compacta |
| Sidebar | Navegação entre módulos e seleção de projeto com aparência SYS_NAV |
| Conteúdo principal | Painéis funcionais por módulo com moldura técnica |
| Modais | Ações contextuais em superfície escura retangular |
| Inputs e botões | Operações de edição, execução e navegação com aparência terminal |
| Tabelas/Listas | Exibição de registros com divisórias finas e estados por pontos/acentos |

## 4. Mapa de Componentes

| Componente | Diretriz visual |
|---|---|
| Shell | Fundo quase preto, sem tema claro |
| Topbar | Barra compacta escura com borda inferior fina |
| Sidebar | Painel escuro com borda, labels em caixa alta e navegação técnica |
| Cards/Painéis | Superfícies pretas/cinza muito escuras, bordas finas, cantos retos e corner brackets nos quatro cantos; em Settings, `settings-card.card` usa padding global de 8px e o header fica colado no topo e laterais |
| Botões primários | Ação principal global: retangular, mono uppercase, borda/acento verde, texto claro, hover com acento operacional |
| Botões secundários | Ação comum global: retangular, mono uppercase, borda discreta, texto cinza claro e hover com borda mais visível |
| Botões terciários | Ação contextual/ícone/baixo peso: retangular, mono uppercase, sem preenchimento forte, texto muted e hover discreto |
| Inputs | Fundo preto, borda fina, prompt/placeholder técnico |
| Código/Terminal | Superfície preta, texto mono, acento verde para prompt/live |
| Tabelas | Linhas discretas, cabeçalhos pequenos, metadados compactos |

## 5. Regras de Exibição

| Regra | Descrição |
|---|---|
| Tema base | A experiência padrão deve ser dark |
| Paleta | Base Black 950 `#050505`, cinzas frios, branco, azul acinzentado, verde status e vermelho live/error |
| Cantos | Usar 0–2px como padrão visual |
| Espaçamento | Compacto e modular, preservando múltiplos coerentes de 8/16px; cards de Settings devem usar padding externo interno de 8px com header encostado no topo/laterais |
| Tipografia | Monospace/sistema técnico para navegação, labels, botões, tabelas e metadados |
| Ornamentos | Evitar glassmorphism, gradientes coloridos, sombras pesadas e saturação desnecessária |
| Hierarquia de botões | Primário, secundário e terciário devem usar tokens e estados consistentes em todos os módulos do workspace |

## 6. Estados

| Estado | Comportamento visual |
|---|---|
| Default | Escuro, técnico, com bordas finas |
| Hover | Leve mudança de fundo/borda sem elevação exagerada |
| Active/Selected | Texto branco e borda/acento verde ou cinza claro |
| Focus | Outline discreto em verde/acinzentado |
| Disabled | Texto escurecido e borda quase invisível |
| Live/Error | Vermelho pontual, sem preencher grandes superfícies |
| Success/Online | Verde pontual para status, prompt e indicadores |

## 7. Fluxo de Interação

| Fluxo | Expectativa |
|---|---|
| Navegar entre abas | Mantém estrutura atual, muda apenas aparência |
| Selecionar projeto | Mantém select e botões existentes com novo estilo dark terminal |
| Editar arquivos | Editor e árvore recebem estilo escuro sem alterar comportamento |
| Usar terminal/git/db/agente | Módulos preservam fluxos e recebem superfícies compatíveis |
| Abrir modais | Modal escuro, geométrico e coerente com tokens |

## 8. Mapeamento de Dados

| Dado | Origem | Exibição |
|---|---|---|
| Nome do projeto | Estado atual da aplicação | Select/sidebar |
| Status do servidor | Backend/API existente | Badge/indicador na topbar |
| Token | Backend/API existente | Badge copiável |
| Conteúdos de módulos | APIs existentes | Painéis internos |
| Estados de operação | APIs/estado local | Pontos verdes/vermelhos e labels técnicos |

## 9. Microcopy

| Área | Diretriz |
|---|---|
| Marca | Manter identificação técnica sem copy promocional longa |
| Subtítulos | Usar textos objetivos, compactos e operacionais |
| Botões | Preferir caixa alta quando estilisticamente apropriado |
| Estados vazios | Não criar mensagens novas fora do escopo |

## 10. Responsividade

| Breakpoint | Regra |
|---|---|
| Mobile < 640px | Manter empilhamento quando já suportado e touch targets mínimos |
| Tablet 640–1024px | Preservar estrutura e espaçamentos proporcionais |
| Desktop 1024–1440px | Layout completo atual com novo rebrand dark |
| Wide > 1440px | Manter contenção visual e legibilidade |

## 11. Acessibilidade

| Critério | Diretriz |
|---|---|
| Contraste | Texto claro sobre superfícies quase pretas |
| Foco | Estados de foco visíveis em inputs e botões |
| Ícones | Preservar ícones existentes e labels quando disponíveis |
| Tamanho alvo | Manter controles com altura adequada para clique |

## 12. Tokens e Estilo

| Token | Valor alvo |
|---|---|
| Background | `#050505` |
| Background token | Black 950 |
| Surface | `#080808` / `#0b0b0b` |
| Text | `#f4f7fb` |
| Muted | `#6f7688` |
| Subtle | `#343a46` |
| Border | `rgba(255,255,255,0.14)` |
| Strong Border | `rgba(255,255,255,0.28)` |
| Green Accent | `#00d084` |
| Red Accent | `#ff3347` |
| Radius | `0px`, `1px`, `2px` |

## 13. Dependências Visuais

| Dependência | Tratamento |
|---|---|
| Fonte técnica | Usar `Fira Code`, `SFMono-Regular`, `Consolas`, monospace como base técnica |
| Lucide/FontAwesome | Preservar ícones já carregados |
| `rebrand.css` | Camada final de override visual |
| `tokens.json` | Registro dos tokens dark da referência |

## 14. Critérios de Aceite da Interface

- [ ] A interface geral passa a ser dark e coerente com a referência visual enviada.
- [ ] Topbar, sidebar, cards, inputs, botões, tabelas e modais seguem a paleta dark alvo.
- [ ] Botões primário, secundário e terciário ficam uniformes em todos os módulos e preservam estados hover/focus/disabled coerentes.
- [ ] Cantos arredondados grandes são reduzidos para estética técnica/retangular.
- [ ] Cards, painéis e modais principais exibem corner brackets nos quatro cantos.
- [ ] Acentos coloridos antigos são substituídos por verde/vermelho pontual e cinzas técnicos.
- [ ] Foco, hover e active continuam perceptíveis.
- [ ] A navegação e os módulos existentes permanecem operáveis.

## 15. Lacunas e Premissas

- A fonte exata da referência não foi fornecida como asset local; a implementação usa fallback técnico/mono.
- Alguns módulos profundos podem exigir QA visual posterior por conterem seletores específicos legados.
- A validação automática não substitui inspeção visual completa no navegador.

## 16. Fora do Escopo

- Redesenhar fluxos de navegação.
- Alterar backend, APIs, banco de dados ou autenticação.
- Adicionar nova biblioteca visual.
- Criar assets binários de fonte.
- Fazer deploy.

## 17. Possíveis Evoluções Futuras

- Criar screenshots comparativos antes/depois para QA visual.
- Consolidar tokens em pipeline automático entre `tokens.json` e CSS.
- Remover estilos legados redundantes após estabilização do rebrand.
- Adicionar fonte licenciada específica se a marca exigir fidelidade tipográfica absoluta.
