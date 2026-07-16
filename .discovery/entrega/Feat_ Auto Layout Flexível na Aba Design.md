# Feat: Auto Layout Flexível na Aba Design

![](files/019f6b07-57d3-71cd-83ec-6f7d2e2701e6/image.png)

# Implementação de Auto Layout Flexível na Aba Design

## Objetivo

Implementar no canvas construído com Konva.js um sistema de **Auto Layout baseado em Flexbox**, permitindo que frames organizem, alinhem, distribuam e redimensionem automaticamente seus elementos filhos.

A implementação deverá reproduzir os controles apresentados na referência visual e seguir o comportamento funcional do **Flex Layout do Penpot**, sem incluir qualquer funcionalidade de Grid Layout.

O Flex Layout do Penpot utiliza conceitos equivalentes ao CSS Flexbox, incluindo direção, alinhamento, distribuição, quebra de linha, gaps, padding e dimensionamento automático do container. ([help.penpot.app](http://help.penpot.app))

---

# 1\. Escopo da Implementação

A funcionalidade deverá permitir:

- Ativar Auto Layout em frames existentes.
- Criar um frame com Auto Layout a partir de uma seleção.
- Organizar automaticamente os filhos do frame.
- Definir direção horizontal ou vertical.
- Inverter a direção dos elementos.
- Configurar alinhamento transversal.
- Configurar distribuição no eixo principal.
- Ativar quebra automática de linha.
- Configurar gaps entre linhas e colunas.
- Configurar padding horizontal, vertical ou individual.
- Definir largura e altura fixas ou ajustadas ao conteúdo.
- Reordenar elementos diretamente no canvas.
- Manter elementos específicos fora do fluxo por posicionamento absoluto.
- Suportar Auto Layout aninhado.
- Integrar todas as alterações ao histórico de undo e redo.

Não faz parte deste escopo:

- Grid Layout.
- Linhas e colunas de grid.
- Áreas nomeadas.
- Unidades fracionárias.
- Posicionamento manual em células.
- Qualquer comportamento baseado em CSS Grid.

---

# 2\. Estrutura da Aba Design

Ao selecionar um frame, grupo ou conjunto de elementos compatíveis, a aba **Design** deverá apresentar a seção:

## Auto Layout

Estados possíveis:

- Auto Layout desativado.
- Auto Layout ativado.
- Estado misto em seleção múltipla.
- Indisponível para tipos de elementos incompatíveis.

A seção deverá possuir:

- Botão para ativar Auto Layout.
- Botão para remover Auto Layout.
- Menu contextual de opções.
- Controles de direção.
- Controles de alinhamento.
- Controles de distribuição.
- Controle de quebra de linha.
- Campos de gap.
- Campos de padding.
- Controles de dimensionamento do frame.
- Ajuda contextual.

---

# 3\. Ativação do Auto Layout

## Aplicação em um Frame Existente

Ao ativar Auto Layout em um frame:

- O frame passa a atuar como um container flexível.
- Seus filhos entram no fluxo automático.
- A ordem visual passa a seguir a ordem da árvore de camadas.
- As posições livres anteriores devem ser convertidas para uma ordem coerente.
- A largura e a altura atuais do frame devem ser preservadas inicialmente.
- A direção inicial deve ser inferida ou definida como horizontal.
- O frame deve continuar selecionado após a ativação.

## Aplicação em uma Seleção

Ao aplicar Auto Layout sobre vários objetos selecionados:

- Um novo frame deverá ser criado.
- Os objetos selecionados serão movidos para dentro dele.
- A ordem relativa dos objetos deverá ser preservada.
- O novo frame deverá utilizar a bounding box da seleção.
- Os filhos devem receber coordenadas relativas ao novo container.
- O Auto Layout deve ser aplicado como uma única transação no histórico.

O Penpot permite aplicar Flex Layout a layers, grupos, boards ou seleções, criando um container com propriedades de layout para os elementos selecionados. ([help.penpot.app](http://help.penpot.app))

---

# 4\. Controles de Alinhamento dos Itens

Os três primeiros controles da referência representam o alinhamento dos elementos no eixo transversal.

O eixo transversal depende da direção escolhida:

- Em direção horizontal, o eixo transversal é vertical.
- Em direção vertical, o eixo transversal é horizontal.

## Alinhar ao Início

Posiciona todos os elementos no início do eixo transversal.

### Direção horizontal

- Os elementos ficam alinhados ao topo.

### Direção vertical

- Os elementos ficam alinhados à esquerda.

## Alinhar ao Centro

Centraliza os elementos no eixo transversal.

### Direção horizontal

- Os elementos ficam centralizados verticalmente.

### Direção vertical

- Os elementos ficam centralizados horizontalmente.

## Alinhar ao Final

Posiciona os elementos no final do eixo transversal.

### Direção horizontal

- Os elementos ficam alinhados à base.

### Direção vertical

- Os elementos ficam alinhados à direita.

O Penpot disponibiliza alinhamento dos itens em início, centro e fim. ([help.penpot.app](http://help.penpot.app))

---

# 5\. Controles de Direção

Os quatro controles com setas definem o eixo principal e a ordem dos filhos.

## Horizontal

Os elementos são organizados da esquerda para a direita.

Comportamento equivalente:

- Direção em linha.
- Primeiro elemento à esquerda.
- Próximos elementos posicionados horizontalmente.
- Gap horizontal aplicado entre os itens.

## Horizontal Invertido

Os elementos são organizados da direita para a esquerda.

Regras:

- A ordem lógica dos filhos não precisa ser alterada.
- A inversão deve ser uma propriedade do layout.
- A árvore de camadas deve continuar apresentando uma ordem previsível.
- A renderização deve considerar a direção invertida.

## Vertical

Os elementos são organizados de cima para baixo.

Comportamento:

- Primeiro elemento no topo.
- Próximos elementos posicionados abaixo.
- Gap vertical aplicado entre os itens.

## Vertical Invertido

Os elementos são organizados de baixo para cima.

Assim como na direção horizontal invertida:

- A propriedade de direção deve controlar a renderização.
- A lista original de filhos deve permanecer íntegra.
- Não deve ser necessário inverter permanentemente a árvore de camadas.

O Flex Layout de referência possui as direções row, row-reverse, column e column-reverse. ([help.penpot.app](http://help.penpot.app))

---

# 6\. Quebra Automática de Linha

O controle com a seta curva deverá ativar ou desativar o comportamento de wrap.

## Wrap Desativado

- Todos os elementos permanecem em uma única linha ou coluna.
- O conteúdo pode ultrapassar os limites internos do frame.
- O frame pode aumentar caso esteja configurado como ajustado ao conteúdo.
- Elementos não devem quebrar automaticamente para outra linha.

## Wrap Ativado

Quando não houver espaço disponível no eixo principal:

- Os elementos devem ser movidos para uma nova linha ou coluna.
- A separação entre linhas utiliza o gap transversal.
- A separação entre itens utiliza o gap principal.
- O cálculo deve considerar padding e dimensões internas do frame.

### Direção horizontal

- Os elementos quebram em novas linhas.

### Direção vertical

- Os elementos quebram em novas colunas.

O Penpot utiliza wrap em conjunto com a direção para distribuir elementos em múltiplas linhas. ([help.penpot.app](http://help.penpot.app))

## Controles Contextuais de Wrap

Quando o wrap estiver ativado, deverá ser disponibilizado um controle complementar de distribuição das linhas:

- Início.
- Centro.
- Final.
- Espaço entre.
- Espaço ao redor.

Esse controle deve permanecer oculto ou desabilitado quando houver apenas uma linha.

---

# 7\. Distribuição no Eixo Principal

Os seis controles da segunda linha representam a distribuição dos elementos no eixo principal.

## Início

Posiciona os elementos no início do container.

### Horizontal

- Alinhados à esquerda.

### Vertical

- Alinhados ao topo.

## Centro

Centraliza o conjunto de elementos dentro do container.

O gap definido continua sendo respeitado entre os elementos.

## Final

Posiciona o conjunto no final do container.

### Horizontal

- Alinhados à direita.

### Vertical

- Alinhados à base.

## Espaço Entre

Distribui o espaço disponível apenas entre os elementos.

Comportamento:

- Primeiro item encostado no início.
- Último item encostado no final.
- Espaçamento igual entre os itens.
- O gap configurado deve atuar como espaçamento mínimo.

## Espaço ao Redor

Distribui espaço ao redor de cada item.

Comportamento:

- Todos os itens recebem espaço lateral equivalente.
- As extremidades possuem aproximadamente metade do espaço interno existente entre dois itens.

## Espaço Uniforme

Distribui o mesmo espaço:

- Antes do primeiro item.
- Entre todos os itens.
- Depois do último item.

O Penpot contempla distribuição em início, centro, fim, space-between, space-around e space-evenly. ([help.penpot.app](http://help.penpot.app))

---

# 8\. Gap Entre Elementos

A interface deverá apresentar dois campos independentes.

## Gap entre Linhas

Controla a distância vertical entre linhas.

Aplicações:

- Entre itens em uma direção vertical sem wrap.
- Entre linhas quando uma direção horizontal utiliza wrap.
- Entre grupos de conteúdo distribuídos verticalmente.

## Gap entre Colunas

Controla a distância horizontal entre colunas.

Aplicações:

- Entre itens em uma direção horizontal sem wrap.
- Entre colunas quando uma direção vertical utiliza wrap.
- Entre grupos de conteúdo distribuídos horizontalmente.

O Penpot diferencia os gaps de linha e de coluna. ([help.penpot.app](http://help.penpot.app))

## Regras dos Campos

- Aceitar somente valores iguais ou superiores a zero.
- Permitir edição por teclado.
- Permitir incremento e decremento.
- Permitir ajuste por arraste horizontal sobre o valor.
- Exibir unidade.
- Permitir vinculação futura com tokens de espaçamento.
- Atualizar o canvas durante a edição.
- Criar apenas uma entrada no histórico ao finalizar a alteração.

## Gap Vinculado

Opcionalmente, os dois gaps poderão permanecer vinculados.

Quando vinculados:

- Alterar um valor atualiza o outro.
- Um único valor representa o espaçamento geral.

Quando desvinculados:

- Cada eixo mantém seu próprio valor.

---

# 9\. Padding do Container

A referência apresenta controles resumidos para padding vertical e horizontal.

## Padding Vertical

Controla simultaneamente:

- Padding superior.
- Padding inferior.

## Padding Horizontal

Controla simultaneamente:

- Padding esquerdo.
- Padding direito.

## Expansão para Lados Individuais

O controle lateral deverá alternar entre:

### Modo Resumido

- Padding vertical.
- Padding horizontal.

### Modo Individual

- Padding superior.
- Padding direito.
- Padding inferior.
- Padding esquerdo.

O Penpot permite controlar padding superior, direito, inferior e esquerdo, além de editar os espaçamentos numericamente. ([help.penpot.app](http://help.penpot.app))

## Regras de Edição

- Valores não podem ser negativos.
- O canvas deve atualizar em tempo real.
- Alterar o padding não deve modificar diretamente as dimensões dos filhos.
- Em frames com tamanho fixo, o padding reduz a área disponível para os filhos.
- Em frames ajustados ao conteúdo, o padding aumenta a dimensão calculada do frame.

---

# 10\. Dimensionamento do Flex Board

A seção **Flex Board** deverá controlar como o container calcula sua largura e altura.

Cada eixo possui duas opções:

- Fixo.
- Ajustar ao conteúdo.

## Largura Fixa

A largura do frame é definida manualmente.

Comportamento:

- Os filhos são distribuídos dentro da largura existente.
- Alterações no conteúdo não modificam automaticamente a largura.
- Wrap pode ser acionado quando os elementos não couberem.
- Overflow pode ocorrer quando wrap estiver desativado.

## Largura Ajustada ao Conteúdo

A largura é calculada com base em:

- Largura dos filhos.
- Gap entre os filhos.
- Padding esquerdo.
- Padding direito.
- Quantidade de linhas ou colunas.
- Direção do layout.

O frame deve ser recalculado sempre que:

- Um filho é inserido.
- Um filho é removido.
- Um filho muda de largura.
- O gap é alterado.
- O padding é alterado.
- A direção é alterada.
- A visibilidade de um filho é alterada.

## Altura Fixa

A altura é definida manualmente.

Os filhos devem ser alinhados e distribuídos dentro da área disponível.

## Altura Ajustada ao Conteúdo

A altura é calculada a partir de:

- Altura dos filhos.
- Gap.
- Padding superior e inferior.
- Quantidade de linhas geradas pelo wrap.
- Direção do container.

O Flex Layout do Penpot disponibiliza dimensionamento fixo ou ajustado ao conteúdo para largura e altura. ([help.penpot.app](http://help.penpot.app))

---

# 11\. Modelo de Dados do Auto Layout

Cada container deverá possuir propriedades próprias de layout.

## Propriedades do Container

- Auto Layout ativado.
- Direção.
- Wrap ativado.
- Alinhamento transversal.
- Distribuição principal.
- Distribuição das linhas.
- Gap de linha.
- Gap de coluna.
- Padding superior.
- Padding direito.
- Padding inferior.
- Padding esquerdo.
- Modo de largura.
- Modo de altura.
- Largura fixa.
- Altura fixa.
- Ordem dos filhos.
- Clipping.
- Largura mínima.
- Altura mínima.
- Estado bloqueado.

## Propriedades dos Filhos

- Identificador do parent.
- Ordem dentro do fluxo.
- Posicionamento estático ou absoluto.
- Margens.
- Largura.
- Altura.
- Visibilidade.
- Estado bloqueado.
- Z-index.
- Participação no cálculo do layout.

O modelo de dados da aplicação deve ser a fonte oficial. Os nós do Konva deverão refletir o resultado calculado pelo motor de layout.

---

# 12\. Motor de Layout para Konva.js

Como o canvas Konva.js não executa CSS Flexbox diretamente, deverá ser criado um motor de layout responsável por calcular posições e dimensões.

## Fluxo de Cálculo

### 1\. Identificação dos Filhos

Separar os elementos em:

- Filhos participantes do fluxo.
- Filhos com posicionamento absoluto.
- Filhos ocultos.
- Filhos bloqueados.
- Containers aninhados.

### 2\. Medição dos Elementos

Para cada filho, obter:

- Largura real.
- Altura real.
- Escala normalizada.
- Dimensões intrínsecas.
- Margens.
- Dimensões mínimas.
- Dimensões calculadas por Auto Layout aninhado.

### 3\. Cálculo da Área Interna

A área disponível será:

- Dimensão do frame.
- Menos padding.
- Menos bordas internas, quando aplicável.

### 4\. Formação das Linhas

Com wrap desativado:

- Criar uma única linha ou coluna.

Com wrap ativado:

- Distribuir os itens até o limite interno.
- Criar uma nova linha quando o próximo item não couber.
- Aplicar gaps de linha e coluna.

### 5\. Distribuição Principal

Aplicar:

- Início.
- Centro.
- Final.
- Espaço entre.
- Espaço ao redor.
- Espaço uniforme.

### 6\. Alinhamento Transversal

Aplicar:

- Início.
- Centro.
- Final.

### 7\. Dimensionamento do Frame

Se o eixo estiver configurado como ajustado ao conteúdo:

- Recalcular a dimensão do container.
- Recalcular a área interna.
- Executar novamente o layout quando necessário.

### 8\. Aplicação no Canvas

- Atualizar as posições dos nós Konva.
- Atualizar as dimensões do frame.
- Atualizar a seleção.
- Atualizar a bounding box.
- Redesenhar somente as layers afetadas.

### 9\. Recursividade

Quando um filho também possuir Auto Layout:

- Calcular primeiro seu conteúdo interno.
- Determinar suas dimensões finais.
- Utilizar essas dimensões no layout do parent.

---

# 13\. Posicionamento dos Filhos

## Posição Estática

A posição estática deve ser o padrão.

Nesse estado:

- O elemento participa do fluxo.
- Sua posição é calculada pelo Auto Layout.
- O usuário não pode movimentá-lo livremente sem alterar sua ordem.
- O arraste deve resultar em reordenação.
- Sua posição manual anterior deixa de ser a fonte oficial.

No Flex Layout do Penpot, elementos estáticos participam do fluxo flexível. ([help.penpot.app](http://help.penpot.app))

## Posição Absoluta

O elemento absoluto:

- Continua pertencendo ao frame.
- Não participa da distribuição automática.
- Pode ser posicionado livremente.
- Não interfere no cálculo do gap.
- Não interfere no tamanho ajustado ao conteúdo.
- Mantém coordenadas relativas ao frame.
- Acompanha o frame durante movimentações.

O Penpot permite retirar um elemento do fluxo flexível por meio do posicionamento absoluto. ([help.penpot.app](http://help.penpot.app))

## Z-index

Elementos absolutos ou sobrepostos deverão possuir controle de z-index independente da ordem visual de layout.

O z-index deverá:

- Controlar a sobreposição.
- Não modificar a posição no fluxo.
- Ser persistido no modelo.
- Ser respeitado na renderização do Konva.

---

# 14\. Reordenação no Canvas

Ao arrastar um elemento estático dentro de um Auto Layout:

- O sistema deve calcular a posição de inserção.
- Os outros filhos devem abrir espaço visualmente.
- Uma linha indicadora deve mostrar onde o item será inserido.
- A ordem deve ser atualizada apenas após a confirmação do drop.
- O elemento deve permanecer dentro do frame.
- A alteração deve ser registrada como uma transação única.

O Penpot permite adicionar e reordenar elementos de um Flex Layout por arraste. ([help.penpot.app](http://help.penpot.app))

## Direções Invertidas

Em direções invertidas:

- A posição visual de inserção deve considerar a direção.
- A ordem do modelo deve permanecer consistente.
- O indicador deve corresponder ao local real em que o objeto será renderizado.

## Wrap

Quando houver múltiplas linhas:

- A posição deve ser calculada pela linha mais próxima.
- O cursor deve determinar o índice dentro da linha.
- O sistema deve evitar saltos entre linhas durante pequenos movimentos.

---

# 15\. Inserção de Novos Elementos

Ao arrastar um objeto externo para um frame com Auto Layout:

- O frame deve receber destaque.
- A posição de inserção deve ser exibida.
- O objeto deve ser anexado ao frame após o drop.
- Suas coordenadas livres devem ser substituídas por uma posição no fluxo.
- O objeto deve aparecer na árvore de camadas na posição correta.
- O layout deve ser recalculado.

Ao criar ou colar um objeto dentro do frame:

- O objeto deverá ser adicionado ao final do fluxo.
- A posição poderá ser ajustada posteriormente por arraste.
- Frames com direção invertida devem preservar uma regra lógica de inserção.

---

# 16\. Redimensionamento do Frame

## Frame com Dimensão Fixa

Durante o redimensionamento manual:

- O tamanho fixo deve ser atualizado.
- Os filhos devem ser recalculados em tempo real.
- Wrap deve reagir à nova dimensão.
- A distribuição deve utilizar o novo espaço disponível.
- O histórico deve registrar apenas o estado inicial e final.

## Frame Ajustado ao Conteúdo

Em um eixo configurado como ajustado ao conteúdo:

- O redimensionamento manual naquele eixo deverá alterar o modo para fixo.
- A interface deve indicar a mudança.
- O usuário poderá retornar posteriormente ao modo ajustado.

## Redimensionamento dos Filhos

Ao redimensionar um filho:

- O layout deve ser recalculado imediatamente.
- Os elementos posteriores devem ser reposicionados.
- Frames ancestrais ajustados ao conteúdo devem ser recalculados.
- A atualização deve ocorrer da camada mais interna para a mais externa.

---

# 17\. Remoção do Auto Layout

Ao remover o Auto Layout:

- O frame permanece existente.
- A posição visual atual de cada filho deve ser preservada.
- Os filhos passam a utilizar posicionamento livre.
- As coordenadas calculadas devem ser convertidas em coordenadas relativas fixas.
- As propriedades de Auto Layout devem ser removidas ou desativadas.
- O usuário deve poder desfazer a operação.

A remoção não deve:

- Desagrupar automaticamente os elementos.
- Remover o frame.
- Alterar a aparência visual.
- Reordenar a árvore de camadas.

---

# 18\. Estados dos Controles

## Estado Padrão

- Ícone visível.
- Fundo neutro.
- Tooltip disponível.

## Estado Hover

- Destaque de fundo.
- Tooltip com nome e descrição.
- Cursor de ação.

## Estado Ativo

- Cor de destaque.
- Fundo selecionado.
- Informação persistente sobre a configuração atual.

## Estado de Foco

- Contorno visível.
- Navegação por teclado.
- Ordem de tabulação lógica.

## Estado Desabilitado

Utilizar quando:

- Não houver seleção.
- A seleção for incompatível.
- O frame estiver bloqueado.
- Houver seleção múltipla com valores incompatíveis.
- A operação não puder ser aplicada ao tipo selecionado.

## Estado Misto

Em seleção múltipla:

- Exibir estado indeterminado.
- Não assumir o valor do primeiro elemento.
- Ao selecionar uma opção, aplicar o valor a todos os containers válidos.

---

# 19\. Feedback no Canvas

Durante a edição do Auto Layout, o canvas deverá fornecer:

- Contorno do container.
- Visualização do padding.
- Indicadores de gap.
- Destaque do eixo principal.
- Indicador de direção.
- Área interna disponível.
- Preview de posição durante reordenação.
- Destaque de linhas geradas pelo wrap.
- Labels temporários com valores de espaçamento.

Os indicadores devem:

- Ser exibidos apenas durante seleção ou edição.
- Não fazer parte da exportação.
- Respeitar zoom e pan.
- Permanecer legíveis em temas claro e escuro.
- Não bloquear interações com os objetos.

---

# 20\. Responsividade

O Auto Layout deve utilizar as dimensões lógicas do documento, independentemente de:

- Zoom do canvas.
- Escala visual do Stage.
- Resolução da tela.
- Densidade de pixels.
- Tamanho do painel lateral.
- Pan do canvas.

## Desktop

- Suporte a mouse e trackpad.
- Tooltips por hover.
- Reordenação precisa.
- Alteração de valores por teclado ou arraste.

## Tablet

- Áreas de toque ampliadas.
- Indicadores visuais mais evidentes.
- Reordenação com gestos.
- Prevenção de conflito com pan.

## Mobile

- Controles distribuídos em múltiplas linhas.
- Seções recolhíveis.
- Campos numéricos adequados ao teclado móvel.
- Reordenação por toque prolongado.
- Auto-scroll próximo às extremidades do frame.

---

# 21\. Desempenho

O motor de Auto Layout deverá evitar recalcular toda a página em cada alteração.

## Estratégia de Atualização

- Recalcular apenas o container alterado.
- Atualizar seus ancestrais quando estiverem ajustados ao conteúdo.
- Atualizar seus descendentes quando houver alteração estrutural.
- Agrupar atualizações por frame de animação.
- Separar estado transitório do estado persistido.
- Redesenhar somente a layer afetada.
- Evitar persistência contínua durante drag e resize.

## Operações que Disparam Recálculo

- Inserção de filho.
- Remoção de filho.
- Reordenação.
- Alteração de direção.
- Alteração de alinhamento.
- Alteração de distribuição.
- Alteração de gap.
- Alteração de padding.
- Alteração de tamanho.
- Alteração de visibilidade.
- Mudança entre estático e absoluto.
- Mudança de conteúdo de texto.
- Redimensionamento de imagem ou forma.
- Alteração de Auto Layout aninhado.

---

# 22\. Histórico e Persistência

Cada interação deve gerar uma transação única.

## Registrar no Histórico

- Ativação do Auto Layout.
- Remoção do Auto Layout.
- Alteração de direção.
- Alteração de alinhamento.
- Alteração de distribuição.
- Ativação de wrap.
- Alteração de gaps.
- Alteração de padding.
- Alteração de dimensionamento.
- Reordenação.
- Inserção ou remoção de elementos.
- Mudança entre posição estática e absoluta.

## Persistência

Ao salvar e recarregar o projeto, deverão ser preservados:

- Tipo de layout.
- Direção.
- Wrap.
- Alinhamentos.
- Distribuição.
- Gaps.
- Padding.
- Modos de dimensionamento.
- Ordem dos filhos.
- Posicionamento absoluto.
- Z-index.
- Hierarquia aninhada.

---

# 23\. Critérios de Aceitação

## Ativação

- É possível ativar Auto Layout em um frame.
- É possível criar um frame com Auto Layout a partir de uma seleção.
- A aparência inicial dos elementos é preservada.
- A operação pode ser desfeita e refeita.

## Direção

- Horizontal organiza da esquerda para a direita.
- Horizontal invertido organiza da direita para a esquerda.
- Vertical organiza de cima para baixo.
- Vertical invertido organiza de baixo para cima.

## Alinhamento

- Início, centro e final funcionam nos dois eixos.
- O alinhamento se adapta automaticamente à direção.
- A troca de direção recalcula o eixo transversal.

## Distribuição

- As seis opções produzem resultados visualmente distintos.
- Gap é respeitado como espaçamento mínimo.
- A distribuição reage ao redimensionamento do frame.

## Wrap

- O wrap cria novas linhas ou colunas quando necessário.
- O gap entre linhas e colunas é aplicado corretamente.
- O número de linhas é recalculado durante resize.

## Padding

- Padding horizontal e vertical podem ser configurados.
- Os quatro lados podem ser editados individualmente.
- O padding afeta corretamente a área interna do frame.

## Dimensionamento

- Largura fixa permanece manual.
- Largura ajustada acompanha o conteúdo.
- Altura fixa permanece manual.
- Altura ajustada acompanha o conteúdo.
- Containers aninhados atualizam seus ancestrais corretamente.

## Reordenação

- Elementos podem ser reordenados por drag-and-drop.
- O indicador de inserção corresponde à posição final.
- A árvore de camadas acompanha a nova ordem.
- Direções invertidas e wrap são respeitados.

## Posicionamento

- Elementos estáticos participam do fluxo.
- Elementos absolutos permanecem dentro do frame, mas fora do fluxo.
- Elementos absolutos acompanham a movimentação do frame.
- Z-index não altera a distribuição.

## Persistência

- O layout permanece correto após salvar e recarregar.
- Undo e redo restauram propriedades, ordem e dimensões.
- O comportamento funciona com Auto Layout aninhado.

---

# 24\. Perguntas Técnicas e Contextuais

## Estrutura

- Os frames atuais já possuem uma lista ordenada de filhos?
- Os elementos estão realmente vinculados ao frame por parentId?
- O frame é representado por [Konva.Group](http://Konva.Group) ou por nós independentes?
- A árvore de camadas é a fonte oficial da ordem dos elementos?
- O estado do projeto é separado do estado interno do Konva?
- Qual profundidade de Auto Layout aninhado deverá ser suportada?

## Ativação

- Qual direção deverá ser aplicada por padrão?
- A direção inicial será inferida pela posição atual dos elementos?
- Ao criar um Auto Layout a partir de uma seleção, qual padding inicial será utilizado?
- O gap inicial será zero ou calculado com base na distância existente?
- A ativação deverá preservar exatamente as posições atuais ou aproximar os elementos ao fluxo?

## Dimensionamento

- O sistema utilizará apenas fixo e ajustado ao conteúdo, conforme a referência?
- Existirão dimensões mínimas e máximas para containers ajustados?
- Um frame ajustado ao conteúdo poderá ser redimensionado manualmente?
- O resize manual deverá transformar automaticamente o eixo em fixo?
- Como textos com tamanho automático serão medidos?

## Direção e Ordem

- A árvore de camadas deverá inverter visualmente em direções reversas?
- A ordem lógica será sempre independente da direção?
- Ao inserir um novo item em uma direção invertida, ele entra no início ou no final da lista?
- Os atalhos de reordenação considerarão a direção visual ou a ordem lógica?

## Wrap

- O wrap estará disponível nas direções horizontal e vertical?
- O usuário poderá controlar a distribuição das linhas?
- Qual será o comportamento quando um item for maior que a área interna?
- Itens muito grandes devem gerar overflow ou expandir o container?
- Haverá limite máximo de linhas ou colunas?

## Gap e Padding

- Os gaps de linha e coluna estarão vinculados por padrão?
- O painel deverá aceitar valores decimais?
- Quais unidades serão suportadas inicialmente?
- Padding e gap poderão ser vinculados a tokens?
- Alterações por arraste deverão utilizar quais modificadores de teclado?
- O sistema permitirá valores negativos em margens dos filhos?

## Posicionamento dos Filhos

- A opção estático ou absoluto ficará na seção do elemento filho?
- Um elemento absoluto poderá ser arrastado novamente para o fluxo?
- Como o usuário indicará o índice em que o elemento absoluto retornará?
- Elementos ocultos participam do cálculo do layout?
- Elementos bloqueados participam do fluxo normalmente?
- O z-index será independente da ordem da árvore?

## Interação

- O canvas exibirá padding e gap enquanto o frame estiver selecionado?
- Haverá manipulação direta dos espaçamentos no canvas?
- O usuário poderá arrastar o valor do gap diretamente entre dois elementos?
- Qual feedback será apresentado durante reordenação?
- O layout será recalculado continuamente durante resize?
- A atualização será aplicada imediatamente ou somente após o término da interação?

## Responsividade

- Os controles deverão quebrar em múltiplas linhas no painel estreito?
- Em mobile, a reordenação será iniciada por toque prolongado?
- O canvas possui diferenças de escala entre desktop e mobile?
- A medição dos elementos utiliza coordenadas lógicas ou coordenadas transformadas do Stage?
- O Auto Layout deverá produzir resultados idênticos independentemente do zoom?

## Histórico

- O histórico atual suporta transações compostas?
- Alterações contínuas de gap serão consolidadas em uma única ação?
- A ativação do Auto Layout deverá preservar um snapshot completo das posições anteriores?
- Undo deverá restaurar dimensões, posições, ordem e hierarquia?
- Alterações em containers aninhados serão registradas em uma única transação?

## Compatibilidade

- Quais elementos poderão atuar como containers flexíveis?
- Frames, grupos e componentes terão o mesmo comportamento?
- Instâncias de componentes poderão receber Auto Layout diretamente?
- Objetos de texto, imagens, SVGs e formas possuem dimensões intrínsecas confiáveis?
- Como serão migrados projetos criados antes da implementação do Auto Layout?