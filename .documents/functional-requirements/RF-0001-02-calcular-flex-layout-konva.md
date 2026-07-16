# RF-0001-02 — Calcular Flex Layout no canvas Konva

## Identificação

- ID: `RF-0001-02`
- REQ pai: `REQ-0001`
- Título: Calcular Flex Layout no canvas Konva
- Projeto: `act-ide-teste`

## Objetivo

Criar um motor de layout no frontend capaz de calcular posições e dimensões dos filhos de frames com Auto Layout, refletindo o resultado nos nós Konva.

## Contexto funcional

Konva.js não executa CSS Flexbox. O canvas precisa de uma engine própria que leia o modelo do documento e atualize coordenadas absolutas dos filhos de acordo com as propriedades do frame.

## História do usuário

Como usuário da aba Design, quero que os filhos de um frame sejam reposicionados automaticamente quando altero direção, gap, padding, wrap, alinhamento ou sizing.

## Descrição funcional

O motor deve identificar frames com `layout.enabled`, coletar filhos pelo `parentId`, separar filhos absolutos e ocultos, medir dimensões, formar linhas/colunas, aplicar distribuição, alinhamento e padding, ajustar dimensões `hug` e atualizar os nós no canvas.

## Fluxo funcional

1. Sistema identifica containers com Auto Layout.
2. Sistema calcula containers aninhados antes dos ancestrais.
3. Sistema coleta filhos participantes do fluxo.
4. Sistema mede largura/altura de cada filho.
5. Sistema forma linhas conforme direção e wrap.
6. Sistema aplica justify, align, gaps e padding.
7. Sistema atualiza `x`, `y`, `width` e `height` quando aplicável.
8. Sistema redesenha camadas afetadas.

## Regras de negócio

- `row`, `row-reverse`, `column` e `column-reverse` devem ser suportados.
- `wrap` deve criar novas linhas/colunas quando não houver espaço interno suficiente.
- `justifyContent` deve suportar `start`, `center`, `end`, `space-between`, `space-around`, `space-evenly`.
- `alignItems` deve suportar `start`, `center`, `end`.
- `alignContent` deve operar quando houver múltiplas linhas/colunas.
- `rowGap` e `columnGap` devem ser respeitados como espaçamento mínimo.
- `widthMode` e `heightMode` devem aceitar `fixed` e `hug`.
- Filhos com `layoutItem.position = absolute` não participam do fluxo.

## Validações funcionais

- Valores inválidos devem cair em defaults seguros.
- Dimensões mínimas devem evitar largura/altura zero.
- Layout aninhado não deve causar loop infinito.

## Dados necessários

- Propriedades de container `layout`.
- Propriedades de filho `layoutItem`.
- Dimensões de cada nó.
- Relações `parentId`.

## Permissões

Não aplicável.

## Integrações

- Konva `contentLayer` para aplicar posições.
- Inspector e árvore de layers para refletir dados atualizados.

## Critérios de aceite

- Direção horizontal organiza filhos da esquerda para direita.
- Direção horizontal invertida organiza visualmente da direita para esquerda.
- Direção vertical organiza filhos de cima para baixo.
- Direção vertical invertida organiza visualmente de baixo para cima.
- Wrap move itens para nova linha/coluna quando necessário.
- Gaps, padding, justify e align mudam visualmente o resultado.
- Frames `hug` ajustam dimensão ao conteúdo.
- Layout aninhado recalcula sem quebrar o canvas.

## Fora do escopo

- CSS Grid.
- Cálculo de margens negativas.
- Distribuição por porcentagens ou unidades fracionárias.

## Dependências

- RF-0001-01.
- Modelo atual do canvas.

## Riscos

- Diferenças sutis em relação ao Flexbox real podem exigir refinamento futuro.

## Rastreabilidade

- REQ: `REQ-0001`
- Discovery: seções 4 a 16 e 21.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Regras de layout definidas.
- [x] Critérios de aceite definidos.
