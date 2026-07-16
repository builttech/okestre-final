# REQ-0001 — Auto Layout Flexível na Aba Design

## Identificação

- ID: `REQ-0001`
- Título: Auto Layout Flexível na Aba Design
- Projeto: `act-ide-teste`
- Origem: `.discovery/saida/Feat_ Auto Layout Flexível na Aba Design.md`
- Tela principal: `/design-canvas`

## Objetivo

Permitir que frames do Design Canvas organizem automaticamente seus elementos filhos usando comportamento equivalente a Flexbox, com controles de direção, alinhamento, distribuição, wrap, gaps, padding, dimensionamento fixo ou ajustado ao conteúdo e posicionamento absoluto de filhos.

## Contexto de negócio

O Design Canvas em Konva.js já permite montar layouts visuais, mas exige posicionamento manual dos elementos. A feature de Auto Layout reduz esforço de composição, melhora consistência visual e aproxima a experiência de ferramentas modernas de design como Penpot/Figma, mantendo rastreabilidade e persistência no modelo local do Act IA.

## Escopo macro

- Ativar e remover Auto Layout em frames existentes.
- Adicionar modelo de dados de layout nos frames.
- Adicionar propriedades de participação no layout nos filhos.
- Calcular posições e dimensões de filhos em um motor Flex Layout próprio para Konva.js.
- Renderizar controles na aba Design para edição das propriedades.
- Persistir configurações no documento local do canvas.
- Suportar Auto Layout aninhado em nível compatível com o modelo flat por `parentId`.
- Preservar aparência ao remover Auto Layout.

## RFs vinculados

- `RF-0001-01` — Modelar e ativar Auto Layout em frames.
- `RF-0001-02` — Calcular Flex Layout no canvas Konva.
- `RF-0001-03` — Disponibilizar controles de Auto Layout na aba Design.
- `RF-0001-04` — Persistir layout, histórico e estados operacionais.

## Regras gerais

- O modelo de dados do Design Canvas é a fonte oficial da configuração de layout.
- Os nós Konva devem refletir o resultado calculado pelo motor de layout.
- Grid Layout não faz parte do escopo.
- Campos numéricos de gap e padding não devem aceitar valores negativos.
- Frames com sizing `hug` devem ajustar largura/altura com base em filhos, gaps e padding.
- Filhos absolutos permanecem dentro do frame, mas fora do cálculo de fluxo.
- A remoção do Auto Layout deve preservar as posições visuais atuais dos filhos.

## Fontes de dados

- Documento local salvo em `localStorage` pela chave do Design Canvas.
- Modelo em memória `state.doc.nodes`.
- Estrutura hierárquica derivada de `parentId`.

## Dados necessários

### Container

- `layout.enabled`
- `layout.direction`
- `layout.wrap`
- `layout.alignItems`
- `layout.justifyContent`
- `layout.alignContent`
- `layout.rowGap`
- `layout.columnGap`
- `layout.paddingTop`
- `layout.paddingRight`
- `layout.paddingBottom`
- `layout.paddingLeft`
- `layout.widthMode`
- `layout.heightMode`

### Filho

- `layoutItem.position`
- `layoutItem.order`
- `layoutItem.zIndex`

## Critérios de aceite macro

- Um frame selecionado permite ativar Auto Layout na aba Design.
- Ao ativar Auto Layout, filhos do frame são organizados automaticamente.
- Direções horizontal, horizontal invertida, vertical e vertical invertida reposicionam os filhos corretamente.
- Wrap cria linhas/colunas adicionais quando o espaço interno é insuficiente.
- Gaps e padding alteram a posição dos filhos no canvas.
- Alinhamento e distribuição alteram visualmente a organização dos filhos.
- Modos fixo/hug afetam dimensões do frame conforme esperado.
- Filhos absolutos não participam do fluxo.
- As configurações persistem após salvar/recarregar.
- Remover Auto Layout preserva a aparência visual atual.

## Dependências

- Canvas existente em `gitide_server/static/konva-designer.html`.
- Lógica de canvas em `gitide_server/static/konva-designer.js`.
- Estilos em `gitide_server/static/rebrand.css`.
- Biblioteca Konva.js carregada pela tela.

## Premissas

- A primeira entrega trabalha com seleção única de frame, compatível com o estado atual do canvas.
- A criação de Auto Layout a partir de seleção múltipla pode ser documentada como evolução futura se a infraestrutura de multi-seleção ainda não existir.
- O histórico undo/redo será implementado em snapshot local simples dentro da própria tela, sem backend novo.
- A validação visual final depende do servidor local/VM estar disponível.

## Restrições

- Não usar estilos inline novos.
- Não criar backend novo.
- Não alterar contratos de APIs existentes.
- Não editar arquivos em `.discovery/saida`.
- Não implementar Grid Layout.

## Fora do escopo

- Grid Layout.
- Responsividade mobile avançada por toque prolongado.
- Manipulação direta de gaps no canvas por drag específico.
- Multi-seleção completa caso a infraestrutura atual não suporte.
- Persistência remota do documento do canvas.

## Riscos

- A ausência de multi-seleção limita a criação automática de frame a partir de seleção múltipla nesta primeira entrega.
- A engine Flex própria pode divergir em detalhes de CSS Flexbox real.
- O layout aninhado exige ordenação de cálculo cuidadosa para não gerar regressões.
- Mudanças em drag/resize podem afetar parentId, camadas e inspector.

## Rastreabilidade

- TAP: `.documents/project-charter.md`
- Discovery: `.discovery/saida/Feat_ Auto Layout Flexível na Aba Design.md`
- Design: `.documents/design/design.md`
- DRI: `.documents/dri/dri.md`

## Histórico de alterações

- 2026-07-16: REQ criado a partir do discovery da feature Auto Layout Flexível.

## Checklist de qualidade

- [x] Objetivo documentado.
- [x] Escopo macro definido.
- [x] RFs vinculados.
- [x] Regras gerais listadas.
- [x] Critérios de aceite macro definidos.
- [x] Fora do escopo explícito.
- [x] Rastreabilidade registrada.
