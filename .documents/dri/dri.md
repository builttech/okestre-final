# DRI — Documento de Requisito de Interface do Projeto

## Projeto

act-ide-teste

# RI-0001 — Auto Layout na Aba Design

## Identificação da interface

- RI: `RI-0001`
- Nome: Auto Layout na Aba Design
- Tela: `/design-canvas`
- Arquivos principais: `gitide_server/static/konva-designer.html`, `gitide_server/static/konva-designer.js`, `gitide_server/static/rebrand.css`
- RFs vinculados: `RF-0001-01`, `RF-0001-02`, `RF-0001-03`, `RF-0001-04`

## Objetivo

Adicionar uma seção de Auto Layout ao inspector da aba Design, permitindo configurar layout flexível de frames diretamente pela interface visual.

## Contexto de uso

O usuário seleciona um frame ou elemento no canvas Konva. O painel direito exibe propriedades do item selecionado. A seção Auto Layout deve aparecer como parte desse inspector, sem substituir os controles existentes de posição, tamanho e aparência.

## Arquitetura da informação

A seção Auto Layout deve conter:

1. Cabeçalho com título e ação principal.
2. Estado de compatibilidade da seleção.
3. Controles de direção.
4. Controle de wrap.
5. Controles de alinhamento e distribuição.
6. Campos de gap.
7. Campos de padding.
8. Controles de sizing do frame.
9. Controles de participação no fluxo para filhos.
10. Microcopy de ajuda curta.

## Mapa de componentes

- `section.konva-auto-layout-section`
- `.konva-auto-layout-header`
- `.konva-auto-layout-actions`
- `.konva-auto-layout-body`
- `.konva-segmented-control`
- `.konva-field-grid`
- `.konva-auto-layout-state`
- `.konva-auto-layout-hint`

## Regras de exibição

- Sem seleção: o inspector permanece no estado vazio existente.
- Seleção de frame sem Auto Layout: exibir botão `Ativar` e descrição curta.
- Seleção de frame com Auto Layout: exibir controles completos e botão `Remover`.
- Seleção de filho dentro de frame com Auto Layout: exibir controle `Fluxo` com opções `Estático` e `Absoluto`.
- Seleção incompatível fora de frame: exibir mensagem informativa curta.

## Estados

- Padrão: controles visíveis e editáveis para frame com Auto Layout.
- Hover: botões e segmentos destacam superfície.
- Ativo: segmento selecionado usa destaque visual do design system.
- Foco: campos e botões mantêm foco visível.
- Desabilitado: estado para seleção incompatível.
- Erro: campos numéricos são normalizados para zero; não há erro bloqueante.

## Fluxo de interação

1. Usuário seleciona frame.
2. Se layout estiver inativo, clica em `Ativar`.
3. Sistema cria defaults e recalcula filhos.
4. Usuário altera direção, wrap, distribuição, align, gaps, padding e sizing.
5. Canvas atualiza em tempo real.
6. Usuário pode remover layout com `Remover`.
7. Usuário pode usar undo/redo por teclado.

## Mapeamento de dados

- `data-layout-action="enable"`: ativa layout.
- `data-layout-action="disable"`: remove layout.
- `data-layout-prop`: altera propriedade de `node.layout`.
- `data-layout-item-prop`: altera propriedade de `node.layoutItem`.
- Inputs numéricos: `rowGap`, `columnGap`, `paddingTop`, `paddingRight`, `paddingBottom`, `paddingLeft`.
- Selects: `alignItems`, `justifyContent`, `alignContent`, `widthMode`, `heightMode`.

## Hierarquia visual

A seção deve seguir o estilo dark/premium/glass do painel direito:

- cartão com borda sutil;
- header compacto;
- botões segmentados;
- campos em grid de duas colunas;
- labels pequenas em uppercase;
- destaque turquesa para estados ativos.

## Microcopy

- Título: `Auto Layout`
- CTA: `Ativar`
- Remoção: `Remover`
- Ajuda frame inativo: `Organize filhos automaticamente com direção, gap e padding.`
- Ajuda filho: `Filhos absolutos ficam fora do fluxo, mas continuam dentro do frame.`

## Responsividade

A tela é desktop-first. Os controles devem quebrar em grid compacto dentro do painel direito e não exceder a largura do aside. Em painéis estreitos, campos continuam em duas colunas quando houver espaço mínimo, ou ocupam toda a largura se o CSS responsivo for acionado futuramente.

## Acessibilidade

- Botões com `type="button"`.
- Labels associadas por texto visível.
- Estados ativos com `aria-pressed` quando aplicável.
- Inputs numéricos com `min="0"`.
- Foco visível preservado pelo CSS.

## Critérios de aceite da interface

- [ ] A seção Auto Layout aparece no inspector da aba Design.
- [ ] O frame selecionado permite ativar Auto Layout.
- [ ] O frame com Auto Layout exibe controles completos.
- [ ] Os controles refletem o estado atual do frame.
- [ ] Alterações nos controles atualizam o canvas.
- [ ] O filho de Auto Layout permite alternar entre estático e absoluto.
- [ ] A interface mantém identidade dark/premium/glass.
- [ ] Não há estilos inline novos.

## Lacunas e premissas

- Multi-seleção completa ainda não é assumida como disponível.
- Tooltips avançados podem ser evoluídos depois.
- Feedback visual avançado de gap/padding no canvas pode ser incremental.

## Fora do escopo

- Grid Layout.
- Manipulação direta de gap no canvas.
- Responsividade mobile avançada.
- Persistência remota.

## Evoluções futuras

- Criar frame Auto Layout a partir de seleção múltipla.
- Indicador visual de inserção durante reordenação complexa.
- Drag direto para alterar gaps.
- Vinculação de gaps/padding com tokens de spacing.

## Rastreabilidade

- TAP: `.documents/project-charter.md`
- REQ: `REQ-0001`
- RFs: `RF-0001-01`, `RF-0001-02`, `RF-0001-03`, `RF-0001-04`
- Design: `.documents/design/design.md`

## Histórico

- 2026-07-16: RI criado para a feature Auto Layout Flexível.


# RI-0003 — Local Devices: Computadores e Pastas

## Identificação da interface
- REQ: REQ-0003; RFs: RF-0003-01, RF-0003-02, RF-0003-03.
- Tela: `/local-devices`; frontend em `gitide_server/static/local-devices.html`, `.js` e `.css`; backend em `gitide_server/local_bridge.py`.
- Versão: aprovada e em implementação após sincronização Git.

## Objetivo e contexto de uso
Separar identidade de computadores, criação de chaves de conexão e pastas associadas. Usuário gerencia múltiplos computadores e pastas sem confundir remover uma associação com apagar arquivos locais.

## Arquitetura da informação
- Aba 1: **Computador** — cabeçalho, estado vazio ou cards de computadores, CTA **Adicionar dispositivo**.
- Aba 2: **Dispositivos e pastas** — computador selecionado, estado vazio ou cards de pastas, CTA **Adicionar pasta**.
- Fluxos modais: adicionar computador e revelar código temporário de pareamento uma vez; instruir adição de pasta no aplicativo local; confirmar remoção de compartilhamento da pasta.

## Mapa de componentes
- `LocalDevicesTabs` — navegação interna entre abas e conteúdo ativo.
- `ComputerEmptyState` / `ComputerCardGrid` / `ComputerCard` — lista e seleção.
- `AddComputerDialog` — nome, expiração, gerar chave.
- `KeyReveal` — chave temporária, copiar e segurança.
- `ComputerPicker`, `FolderEmptyState`, `AddFolderDialog`, `FolderCardGrid`, `FolderCard`, `RemoveFolderConfirm`.

## Regras de exibição e estados
1. Loading: indicar consulta em andamento sem empty prematuro.
2. Zero computadores: título **Nenhum computador cadastrado**, descrição e **Adicionar dispositivo**.
3. Com computadores: cards com nome, status da chave e validade; CTA permanece disponível para novo computador.
4. Modal Adicionar dispositivo: campo obrigatório **Nome do computador** e seletor **Expiração da chave**: 1 mês, 3 meses, 9 meses, Nunca; ações Cancelar e **Gerar chave**.
5. Com opção **Nunca**: aviso explícito de que a chave não terá expiração automática.
6. Após POST bem-sucedido: revelar um código de pareamento de 5 minutos com **Copiar código**. A expiração escolhida se aplica à credencial do agente emitida no claim e nunca visível na web.
7. Aba Pastas sem computador: instrução para cadastrar/selecionar um computador e link à primeira aba.
8. Sem pastas do computador: título **Nenhuma pasta cadastrada para este computador** e **Adicionar pasta**.
9. Com pastas: cards com nome, permissão e projeto vinculado, computador selecionado e ação **Excluir pasta**. O caminho físico permanece somente no dispositivo.
10. Confirmação: **Remover cadastro desta pasta? Os arquivos no computador não serão apagados.** Depois de confirmar, POST `/api/local/remove-root` bloqueia permanentemente essa identidade de pasta no servidor.
11. API com falha: erro contextual, botão Tentar novamente, preservar input e não atualizar cards indevidamente.
12. Operações em andamento: desabilitar duplo envio e manter estado de foco.

## Fluxo de interação
- Abrir tela → consultar computadores → exibir lista ou vazio.
- Adicionar dispositivo → completar campos → Gerar chave → confirmação com segredo de uso único → atualizar cards.
- Repetir criação para cadastrar computadores adicionais.
- Trocar aba → escolher computador → carregar pastas.
- Adicionar pasta → modal orienta inclusão e permissão no aplicativo Okestre Local → reconexão do agente → Atualizar pastas → novo card aparece.
- Excluir pasta → confirmar remoção cadastral → atualizar grade preservando os demais cards.

## Mapeamento de dados
- Computadores: GET `/api/local/devices` e POST `/api/local/pair`. Formulário envia `name` e `expires_in_months` 1/3/9/null.
- Resposta do pareamento: `{code,expires_in,expires_in_months}`; resgate posterior no `/api/local/claim` entrega token diretamente ao agente; a listagem não devolve segredos.
- Pastas: array de `roots` em `/api/local/devices`; adicionar via aplicativo local; remover pelo POST `/api/local/remove-root`.
- Seleção por `device.id`, cards por `root.id`, nunca por índices visuais.
- Não persistir código de pareamento no storage do navegador nem expor credencial definitiva ao browser.

## Hierarquia visual e microcopy
- Preservar design tokens, cores, componentes, ícones e tipografia existentes no módulo real.
- Abas claras e títulos com contraste; empty state com ícone de computador/pasta, título, descrição e CTA único.
- Mensagens: **Computador preparado**, **Código gerado**, **Pastas atualizadas**, **Cadastro da pasta removido**.
- Rótulo **Excluir pasta** pode aparecer no card, mas a confirmação explica que só o cadastro será removido.
- Status da chave: válida, expirada ou sem expiração automática, conforme dados do backend.

## Responsividade e acessibilidade
- Grade fluida com cards uma coluna em largura estreita; modais adaptáveis, sem scroll horizontal.
- Abas com role tablist/tab/tabpanel, aria-selected, navegação por teclado, foco visível.
- Dialog com aria-modal, rótulo, foco inicial, Escape, trap e retorno do foco ao gatilho.
- Inputs label-for, mensagens de erro por campo e status geral via aria-live.
- Ações icon-only precisam aria-label; botão de remoção não depende apenas da cor.

## Critérios de aceite da interface
- [ ] Sem computador, empty state e CTA abrem modal.
- [ ] Campo nome é obrigatório; opções da chave são 1/3/9 meses/nunca.
- [ ] É possível incluir múltiplos computadores sem sobrescrever os anteriores.
- [ ] Código de pareamento é exibido uma única vez e desaparece ao fechar; token definitivo é exclusivo do agente.
- [ ] Aba Pastas fica vinculada ao computador selecionado, sem misturar dados.
- [ ] N pastas são representadas em cards; exclusão remove só o vínculo.
- [ ] Loading, erro, confirmação, mobile e navegação via teclado funcionam.

## Lacunas, premissas, fora do escopo e evoluções
- Lacuna resolvida após sincronização Git: rota e frontend localizados no projeto 46. A inserção física de pastas exige confirmação no próprio Windows por razões de segurança.
- Premissa: Dispositivos e pastas refere-se aos cadastros de pastas por computador, não a um novo tipo de dispositivo.
- Fora do escopo: apagar arquivos físicos, remover computador, girar/revogar chaves, explorar diretórios locais no servidor.
- Futuro: busca de computadores, filtros de pasta, reemissão/revogação de chave e sinalização de agente online.

## Rastreabilidade e histórico
- TAP seção 10; REQ-0003; RF-0003-01/02/03; Design seção 16; TASK-RF-0003-*; estimativa RUN-LOCAL-DEVICES-20261011.
- 2026-10-11: pacote aprovado; desenho reconciliado com API `/api/local/*`, agente Windows e código de pareamento de uso único.
