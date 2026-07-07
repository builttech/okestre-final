# DRI — Documento de Requisito de Interface do Projeto

## Projeto

git-ide

## 1. Identificação da Interface

| Campo | Valor |
|---|---|
| REQ | REQ-3091 |
| Interface | Shell principal do GitIDE e módulos internos |
| Tipo | Rebrand visual / Design System |
| Fonte visual | `design_rebrand.md` |
| Status | Aprovado para execução |

## 2. Contexto de Uso

| Item | Descrição |
|---|---|
| Usuários | Operadores e desenvolvedores usando o GitIDE |
| Ambiente | Aplicação web local/servida pelo backend do projeto |
| Objetivo da interface | Oferecer experiência clara, minimalista, técnica e consistente com o novo rebrand |

## 3. Arquitetura da Informação

| Área | Papel na experiência |
|---|---|
| Topbar | Marca, status do servidor, token e logout |
| Sidebar | Navegação entre módulos e seleção de projeto |
| Conteúdo principal | Painéis funcionais por módulo |
| Modais | Criação, configuração e ações contextuais |
| Inputs e botões | Operações de edição, execução e navegação |

## 4. Mapa de Componentes

| Componente | Diretriz visual |
|---|---|
| Shell | Fundo claro `#f9f4ed`, sem atmosfera escura |
| Topbar | Superfície clara com borda inferior fina |
| Sidebar | Superfície clara/creme, navegação geométrica |
| Cards/Painéis | Superfícies `#ffffff` ou `#f4f4f5`, borda preta/cinza fina |
| Botões primários | Fundo `#f4f4f5`/acento `#888888`, cantos retos |
| Inputs | Fundo branco ou cinza claro, borda `#050505` suavizada |
| Código/Terminal | Superfície clara com contraste legível e fonte mono |

## 5. Regras de Exibição

| Regra | Descrição |
|---|---|
| Tema base | A experiência padrão deve ser clara |
| Paleta | Monocromática com acento dominante `#888888` |
| Cantos | Usar 0–2px como padrão visual |
| Espaçamento | Priorizar múltiplos de 16px |
| Tipografia | `Switzer` como primeira preferência, fallback seguro |
| Ornamentos | Evitar gradientes coloridos, badges decorativos e saturação desnecessária |

## 6. Estados

| Estado | Comportamento visual |
|---|---|
| Default | Claro, limpo, técnico |
| Hover | Leve mudança de fundo/borda sem elevação exagerada |
| Active/Selected | Acento cinza `#888888` ou superfície levemente destacada |
| Focus | Outline/box-shadow discreto em cinza |
| Disabled | Texto e borda em cinza claro, sem contraste excessivo |
| Danger | Manter vermelho semântico apenas onde necessário |
| Success | Manter verde semântico apenas onde necessário |

## 7. Fluxo de Interação

| Fluxo | Expectativa |
|---|---|
| Navegar entre abas | Mantém estrutura atual, muda apenas aparência |
| Selecionar projeto | Mantém select e botões existentes com novo estilo |
| Editar arquivos | Editor e árvore recebem estilo claro sem alterar comportamento |
| Usar terminal/git/db/agente | Módulos preservam fluxos e recebem superfícies compatíveis |
| Abrir modais | Modal claro, geométrico e coerente com tokens |

## 8. Mapeamento de Dados

| Dado | Origem | Exibição |
|---|---|---|
| Nome do projeto | Estado atual da aplicação | Select/sidebar |
| Status do servidor | Backend/API existente | Badge na topbar |
| Token | Backend/API existente | Badge copiável |
| Conteúdos de módulos | APIs existentes | Painéis internos |

## 9. Microcopy

| Área | Diretriz |
|---|---|
| Marca | Evitar reforço do nome antigo quando houver nova marca operacional |
| Subtítulos | Manter textos objetivos e técnicos |
| Botões | Preservar microcopy funcional atual |
| Estados vazios | Não criar mensagens novas fora do escopo |

## 10. Responsividade

| Breakpoint | Regra |
|---|---|
| Mobile < 640px | Manter empilhamento quando já suportado e touch targets mínimos |
| Tablet 640–1024px | Preservar estrutura e espaçamentos proporcionais |
| Desktop 1024–1440px | Layout completo atual com novo rebrand |
| Wide > 1440px | Manter contenção visual e legibilidade |

## 11. Acessibilidade

| Critério | Diretriz |
|---|---|
| Contraste | Texto principal preto/cinza sobre superfícies claras |
| Foco | Estados de foco visíveis em inputs e botões |
| Ícones | Preservar ícones existentes e labels quando disponíveis |
| Tamanho alvo | Manter controles com altura adequada para clique |

## 12. Tokens e Estilo

| Token | Valor alvo |
|---|---|
| Background | `#f9f4ed` |
| Surface | `#f4f4f5` / `#ffffff` |
| Text | `#000000` |
| Muted | `#52525b` |
| Accent | `#888888` |
| Secondary | `#aaaaaa` |
| Border | `#050505` suavizado quando necessário |
| Radius | `0px`, `1px`, `2px` |

## 13. Dependências Visuais

| Dependência | Tratamento |
|---|---|
| Switzer | Usar como primeira opção no CSS; fallback para Inter/system |
| RedditMono/Fira Code | Preservar stack mono para código |
| Lucide/FontAwesome | Preservar ícones já carregados |
| `rebrand.css` | Camada final de override visual |

## 14. Critérios de Aceite da Interface

- [ ] A interface geral passa a ser clara e coerente com `design_rebrand.md`.
- [ ] Topbar, sidebar, cards, inputs, botões e modais seguem a paleta alvo.
- [ ] Cantos arredondados grandes são reduzidos para estética geométrica.
- [ ] Acentos coloridos antigos são substituídos por cinza/acento neutro onde não forem semânticos.
- [ ] Foco, hover e active continuam perceptíveis.
- [ ] A navegação e os módulos existentes permanecem operáveis.

## 15. Lacunas e Premissas

- A fonte Switzer não foi encontrada como asset local; a implementação depende de fonte instalada/disponível no ambiente ou fallback.
- Alguns módulos profundos podem exigir QA visual posterior por conterem seletores específicos legados.
- A validação automática não substitui inspeção visual completa no navegador.

## 16. Fora do Escopo

- Redesenhar fluxos de navegação.
- Alterar backend, APIs, banco de dados ou autenticação.
- Adicionar nova biblioteca visual.
- Criar assets binários de fonte.
- Fazer deploy.

## 17. Possíveis Evoluções Futuras

- Adicionar pacote próprio de fontes licenciado no repositório, se autorizado.
- Criar screenshots comparativos antes/depois para QA visual.
- Consolidar tokens em pipeline automático entre `tokens.json` e CSS.
- Remover estilos legados redundantes após estabilização do rebrand.
