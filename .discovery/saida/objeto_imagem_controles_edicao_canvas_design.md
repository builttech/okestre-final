# Objeto de Imagem e Controles de Edição no Canvas Design

## Objetivo

Evoluir o Design Canvas da rota `/design-canvas` para suportar um objeto de imagem real, editável e persistente, substituindo o comportamento atual de placeholder geométrico.

O resultado esperado é permitir que o usuário insira uma imagem, acompanhe seu carregamento, selecione o elemento no canvas e na árvore de camadas, altere fonte, dimensões, enquadramento e aparência, utilize undo e redo, preserve a hierarquia com frames e Auto Layout e recupere o documento após recarregar a página.

A entrega deve completar o fluxo funcional do objeto de imagem dentro da arquitetura atual do Canvas, sem tratar como concluídas funcionalidades adjacentes que hoje possuem apenas controles visuais ou documentação sem correspondência confirmada no código carregado.

## Contexto Atual

A tela `/design-canvas` é uma interface independente, servida pelo projeto FastAPI e construída com HTML, CSS e JavaScript estáticos. A renderização visual usa Konva.js 9, carregado pela página, e os ícones de interface usam Lucide.

O documento do Canvas é mantido em `state.doc`, com páginas e uma lista flat de nós em `state.doc.nodes`. A relação hierárquica entre elementos e frames é representada por `parentId`. As coordenadas dos elementos são armazenadas no modelo e refletidas nos nós Konva.

O Canvas possui:

- `contentLayer` para os elementos do documento;
- `uiLayer` para transformer, labels e feedbacks de seleção;
- árvore de camadas derivada de `parentId`;
- inspector da aba Design;
- persistência do documento em `localStorage`;
- exportação do documento em JSON;
- histórico local de undo e redo por snapshots do documento;
- suporte existente a frames, retângulos, elipses, textos, linhas e ícones representados como texto;
- integração de filhos com Auto Layout por `layoutItem`.

A ferramenta `Imagem` já aparece na barra de ferramentas, porém o fluxo atual não cria um objeto de imagem. Ao utilizar a ferramenta, o código cria um retângulo, altera seu tipo para `rect` e o nomeia como `Imagem placeholder`.

A função de renderização não possui tratamento para `type: image` nem cria `Konva.Image`. O objeto resultante usa a renderização e os controles genéricos de `Konva.Rect`.

Não foram identificados no código atual:

- seleção de arquivo de imagem;
- carregamento por fonte externa;
- decodificação e criação de `Konva.Image`;
- metadados da imagem de origem;
- dimensões naturais;
- estado de carregamento;
- estado de erro;
- substituição da imagem preservando o elemento;
- modos de ajuste ou enquadramento;
- recorte;
- inversão horizontal ou vertical;
- filtros de imagem;
- texto alternativo;
- controles específicos no inspector;
- ícone e label específicos de imagem na árvore de camadas;
- política confirmada para persistência dos dados binários.

O inspector atual exibe controles genéricos de posição, tamanho, fill, stroke, radius e opacity. Controles de texto são ocultados apenas quando a seleção não é um nó de texto. Não existe composição do inspector por tipo de elemento.

A persistência ocorre em `localStorage`, inclusive após alterações do inspector. A estratégia atual de snapshots duplica o documento completo no histórico. Incorporar imagens diretamente ao documento pode aumentar significativamente o volume persistido e o custo do histórico; a estratégia de armazenamento do conteúdo da imagem precisa ser definida antes da implementação.

A documentação Harness registra Canvas Infinito, Hand Tool, zoom relativo ao cursor, pinch, stage responsivo e viewport por página como concluídos. Entretanto, o arquivo `gitide_server/static/konva-designer.js` atualmente presente no workspace inicializa um stage fixo de `2700 × 1500`, limita zoom entre `25%` e `160%` e não contém os handlers documentados de pan, Hand Tool, wheel focal ou touch. O HTML também carrega uma versão de asset anterior à versão registrada nas evidências Harness. Essa divergência deve ser reconciliada antes da execução para que o objeto de imagem seja implementado sobre o baseline efetivamente utilizado em produção.

O CSS do Canvas é desktop-first, com painéis laterais fixos e um breakpoint confirmado em `1280px`. Não foi identificado comportamento completo para tablet ou mobile.

## Escopo da Implementação

### Funcionalidades incluídas

- Criar um tipo de nó de documento específico para imagem.
- Renderizar a imagem com um nó Konva compatível com seleção, transformer e camadas existentes.
- Inserir imagem a partir de arquivo local por uma ação acessível da barra de ferramentas.
- Permitir substituir a fonte de uma imagem sem alterar o identificador, a posição, a hierarquia ou a ordem de camada do objeto.
- Permitir excluir o objeto pelo fluxo já existente de exclusão.
- Exibir estado de carregamento enquanto a fonte é decodificada.
- Exibir estado de erro com ação de tentar novamente ou substituir a fonte.
- Manter dimensões naturais como metadado separado das dimensões renderizadas.
- Preservar proporção por padrão na inserção inicial.
- Permitir editar posição, largura, altura, rotação e opacidade.
- Permitir bloquear ou liberar a proporção durante o redimensionamento.
- Permitir modos de ajuste da imagem dentro da bounding box.
- Permitir editar o ponto focal ou enquadramento quando o modo exigir recorte.
- Permitir resetar o enquadramento para o padrão da imagem.
- Permitir aplicar corner radius e stroke sem converter o objeto em retângulo.
- Permitir inversão horizontal e vertical.
- Disponibilizar filtros de brilho, contraste, saturação, escala de cinza e blur em uma seção avançada, condicionados à confirmação de escopo e limites de desempenho.
- Exibir nome, tipo e ícone corretos na árvore de camadas.
- Permitir renomear o layer da imagem por padrão de interação compatível com a árvore existente, após definição do comportamento de renomeação de layers.
- Integrar o objeto de imagem a frames e Auto Layout.
- Persistir as propriedades do objeto e restaurá-las após reload.
- Incluir as propriedades serializáveis no JSON exportado.
- Registrar alterações relevantes no histórico de undo e redo.
- Preservar compatibilidade com documentos antigos que contenham `Imagem placeholder` como retângulo.

### Controles do inspector incluídos

#### Identificação e fonte

- Nome do layer.
- Preview reduzido da fonte carregada.
- Nome do arquivo ou identificador da fonte.
- Ação `Substituir imagem`.
- Ação `Restaurar enquadramento`.
- Estado de carregamento, sucesso ou erro.
- Texto alternativo para uso em inspeção, exportação ou integração futura.

#### Geometria

- X.
- Y.
- Largura.
- Altura.
- Rotação.
- Bloqueio de proporção.
- Inversão horizontal.
- Inversão vertical.

#### Enquadramento

- Modo `Preencher`, equivalente a cobrir a bounding box com recorte.
- Modo `Ajustar`, equivalente a conter toda a imagem na bounding box.
- Modo `Esticar`, permitindo distorção controlada.
- Modo `Tamanho original`, usando as dimensões naturais como referência.
- Ponto focal horizontal e vertical.
- Escala interna do recorte.
- Ação de edição visual do recorte no canvas.
- Ação de reset do recorte.

#### Aparência

- Opacidade.
- Corner radius.
- Cor do stroke.
- Espessura do stroke.
- Brilho.
- Contraste.
- Saturação.
- Escala de cinza.
- Blur.
- Reset dos filtros.

#### Hierarquia e comportamento

- Participação estática ou absoluta quando a imagem for filha de frame com Auto Layout.
- Estado bloqueado, caso o fluxo de bloqueio seja confirmado para o Canvas.
- Estado visível ou oculto, caso o fluxo de visibilidade seja confirmado para a árvore de camadas.
- Duplicar.
- Excluir.

### Comportamentos incluídos

- Inserção por clique na ferramenta e seleção de arquivo.
- Inserção no ponto escolhido no canvas ou no centro do viewport, conforme decisão de produto.
- Drag-and-drop de arquivo sobre o canvas, condicionado à confirmação do fluxo.
- Colar imagem da área de transferência, condicionado à confirmação de segurança e suporte de navegador.
- Seleção pelo canvas e pela árvore de camadas.
- Drag, resize e rotação pelo transformer.
- Edição por inspector.
- Recorte visual com confirmação, cancelamento e reset.
- Substituição da fonte preservando o objeto.
- Persistência, reload, exportação, duplicação, exclusão, undo e redo.
- Participação em Auto Layout sem alterar o conteúdo original da imagem.

### Fora do escopo desta solicitação

- Implementar ou completar Comentários.
- Implementar histórico visual no botão de cabeçalho.
- Implementar o modo Protótipo.
- Implementar bibliotecas de Assets.
- Implementar editor de Tokens.
- Implementar colaboração em tempo real.
- Implementar upload remoto ou biblioteca central de mídia sem definição de backend.
- Implementar edição vetorial ou remoção de fundo.
- Implementar máscaras vetoriais arbitrárias.
- Implementar animação de imagens.
- Considerar Canvas Infinito, Hand Tool ou touch como disponíveis sem reconciliar a divergência entre código e documentação.

## Especificações Técnicas

### Modelo de estado

O nó de imagem deve permanecer no modelo flat de `state.doc.nodes` e utilizar `type: image`, sem ser convertido em `rect`.

O estado conceitual do objeto deve separar:

- identidade e hierarquia;
- geometria renderizada;
- fonte da imagem;
- dimensões naturais;
- enquadramento;
- aparência;
- acessibilidade;
- estado operacional temporário.

As propriedades persistentes devem contemplar, no mínimo:

- identificador;
- tipo;
- nome;
- página;
- `parentId`;
- posição;
- largura e altura;
- rotação;
- opacidade;
- fonte persistível;
- tipo da fonte;
- metadados do arquivo;
- largura e altura naturais;
- modo de ajuste;
- dados de recorte ou ponto focal;
- inversão horizontal e vertical;
- corner radius;
- stroke;
- filtros confirmados;
- texto alternativo;
- bloqueio;
- `layoutItem` quando aplicável.

Estados como carregando, erro de decodificação, objeto URL temporário e referência ao elemento HTML de imagem não devem ser serializados como parte do documento.

A fonte oficial das propriedades continua sendo o modelo do Canvas. O nó Konva deve refletir esse estado e não se tornar a única fonte dos dados.

### Carregamento da imagem

A criação do nó visual somente deve ser considerada concluída após a fonte ser validada e decodificada.

Durante o carregamento, o sistema deve manter um estado visual não bloqueante e impedir operações que dependam das dimensões naturais.

Quando o carregamento falhar:

- o documento não deve permanecer com uma referência silenciosamente inválida;
- o usuário deve receber feedback contextual;
- deve existir ação para substituir a fonte;
- undo deve restaurar o estado anterior válido;
- o erro não deve interromper a renderização dos demais nós.

A implementação deve liberar referências temporárias quando a imagem for substituída, removida, desfeita ou quando a página for descarregada.

### Renderização no Konva

O objeto deve ser renderizado por `Konva.Image` ou composição equivalente que preserve a semântica de imagem e permita aplicar recorte, raio, stroke e filtros sem converter o dado em um retângulo genérico.

A bounding box do objeto define a área ocupada no Canvas e no Auto Layout. As dimensões naturais servem como referência para proporção e enquadramento, mas não substituem `width` e `height` do nó no documento.

O recorte deve ser calculado a partir do modo de ajuste e do ponto focal, sem modificar o arquivo de origem.

Corner radius e stroke devem acompanhar resize, zoom e exportação visual. O raio não pode exceder de forma inconsistente a geometria final do objeto.

Filtros que exigirem cache do nó devem ser aplicados apenas quando ativos. Drag, resize e edição de crop não devem reconstruir ou decodificar a imagem em cada evento contínuo.

### Inspector contextual

O inspector deve ser composto conforme o tipo da seleção.

Para imagem, controles de texto devem permanecer ocultos e controles que não tenham significado para imagem não devem aparecer apenas por pertencerem ao inspector genérico.

A seção de fonte deve aparecer antes de geometria e aparência. Controles avançados de filtros devem ser recolhíveis para reduzir densidade visual.

Campos devem refletir o estado real do modelo após drag, resize, substituição, undo, redo e reload.

Alterações contínuas por slider devem fornecer preview imediato, mas devem gerar uma transação coerente de histórico ao concluir a interação, evitando um snapshot por pixel de movimento.

### Eventos e histórico

Devem gerar histórico:

- criação da imagem;
- substituição da fonte;
- resize concluído;
- rotação concluída;
- drag concluído;
- alteração confirmada de crop;
- mudança de modo de ajuste;
- alteração de aparência;
- inversão;
- alteração de hierarquia;
- duplicação;
- exclusão.

Estados temporários de hover, preview, carregamento e edição ainda não confirmada não devem gerar histórico.

Cancelar a edição de recorte deve restaurar o estado anterior sem criar uma nova alteração persistente.

A substituição da imagem deve ser tratada como uma única transação de histórico, incluindo fonte, metadados naturais e enquadramento resultante.

### Persistência

A persistência deve continuar compatível com o documento local atual, porém a fonte binária não deve ser definida por suposição.

Devem ser avaliadas três estratégias antes da implementação:

- incorporar a imagem ao documento local;
- persistir o binário em armazenamento local separado e referenciar um identificador;
- utilizar backend ou repositório de assets.

URLs temporárias de objeto não podem ser consideradas uma fonte persistente após reload.

A estratégia escolhida deve evitar duplicar o binário completo em cada snapshot de histórico e em cada duplicação lógica do objeto quando houver possibilidade de referência compartilhada.

A migração deve preservar documentos existentes. Retângulos nomeados `Imagem placeholder` não devem ser convertidos automaticamente em imagens reais sem confirmação, pois podem ter sido editados como formas comuns.

### Segurança

Arquivos devem ser validados por tipo aceito antes da decodificação.

Formatos vetoriais com conteúdo executável ou referências externas exigem política específica antes de serem aceitos.

Fontes remotas, se permitidas, precisam de regras para origem, CORS, falha de rede e exportação do canvas.

Metadados de arquivo não devem expor caminhos locais do dispositivo do usuário.

## Estrutura e Hierarquia

A imagem é um elemento folha e não deve receber filhos.

Na árvore de camadas:

- deve usar ícone de imagem;
- deve exibir nome próprio;
- deve respeitar profundidade derivada de `parentId`;
- deve responder à seleção;
- deve manter a ordem visual já derivada da lista de nós;
- deve refletir estados confirmados de bloqueio, erro e visibilidade sem depender apenas de cor.

Quando inserida dentro de um frame:

- `parentId` deve apontar para o frame correto;
- a bounding box deve permanecer em coordenadas compatíveis com o modelo atual;
- a imagem deve acompanhar o movimento do frame como os demais descendentes;
- a substituição da fonte não deve alterar `parentId`;
- duplicação deve preservar o parent compatível;
- exclusão do frame deve seguir a regra atual de remoção dos descendentes.

Quando filha de Auto Layout:

- deve receber ou preservar `layoutItem`;
- largura e altura renderizadas devem ser usadas na medição do layout;
- modo de ajuste e recorte não devem modificar o tamanho ocupado no fluxo;
- filho estático deve ser reposicionado pelo motor de layout;
- filho absoluto deve permanecer fora do cálculo de fluxo;
- substituição da fonte não deve alterar ordem nem posição do item, salvo quando existir regra aprovada de tamanho original ou ajuste automático.

Overlays de crop, mensagens e handles devem permanecer em `uiLayer` ou camada equivalente de interface, sem entrar na árvore persistida do documento.

## Posicionamento e Layout

O objeto de imagem deve utilizar o mesmo sistema de coordenadas dos demais nós do documento.

No baseline de código atual, `x` e `y` são coordenadas globais do Canvas mesmo quando o elemento possui `parentId`. A implementação não deve introduzir coordenadas relativas apenas para imagens.

A inserção inicial deve considerar:

- posição escolhida pelo usuário;
- frame sob o ponto de inserção;
- seleção de frame compatível;
- viewport efetivamente implementado após a reconciliação do baseline;
- dimensões naturais da imagem;
- limite visual inicial para imagens maiores que a área útil.

A proporção deve iniciar bloqueada. O usuário pode liberar a proporção para redimensionamento livre.

No modo `Preencher`, a imagem ocupa toda a bounding box e o excedente é recortado.

No modo `Ajustar`, toda a imagem permanece visível dentro da bounding box. A área não ocupada precisa respeitar a definição de fundo transparente ou preenchido.

No modo `Esticar`, a imagem acompanha largura e altura independentemente da proporção natural.

No modo `Tamanho original`, a bounding box deve usar dimensões naturais limitadas por regras de escala e viewport a serem aprovadas.

Durante crop:

- a bounding box externa permanece estável;
- o conteúdo pode ser deslocado ou escalado internamente;
- a área externa ao recorte recebe máscara visual;
- Enter confirma;
- Escape cancela;
- clicar fora exige regra explícita de confirmar ou cancelar.

A imagem deve respeitar clipping de frames somente se essa regra for adotada de forma consistente para todos os filhos do Canvas. Não foi identificado clipping de frame no baseline atual.

## Estados

### Padrão

Imagem carregada, não selecionada e renderizada conforme o documento.

### Hover

Cursor e destaque devem indicar que o elemento pode ser selecionado, sem alterar o documento.

### Selecionado

Transformer, bounding box e inspector contextual ficam visíveis. A árvore de camadas reflete a seleção.

### Carregamento

Exibe placeholder visual de carregamento dentro da bounding box. Controles dependentes da imagem ficam desabilitados, mantendo ações de cancelar ou substituir quando aplicável.

### Erro

Exibe ícone e mensagem contextual, ação de substituir ou tentar novamente e identificação do layer. O objeto não deve desaparecer silenciosamente.

### Editando recorte

Exibe máscara, limites da bounding box, conteúdo manipulável e ações de confirmar, cancelar e resetar.

### Bloqueado

Não permite drag, resize, rotação, crop ou edição destrutiva. A seleção e a leitura de propriedades dependem da regra geral de bloqueio a ser confirmada.

### Desabilitado

Controles incompatíveis com o modo atual permanecem visíveis somente quando ajudarem a explicar a indisponibilidade. Devem possuir label e motivo acessível.

### Vazio

O fluxo não deve criar um objeto persistente sem fonte válida, salvo se o produto aprovar explicitamente um estado de frame de imagem vazio.

### Misto

Multi-seleção não está confirmada no Canvas atual. Não devem ser criados estados mistos específicos para imagem até existir contrato de multi-seleção.

## Comportamento da Interação

### Inserção por ferramenta

1. O usuário ativa a ferramenta Imagem.
2. A ferramenta recebe estado visual ativo e foco adequado.
3. O usuário escolhe um ponto no canvas ou aciona diretamente a seleção de arquivo, conforme fluxo aprovado.
4. O seletor de arquivo informa os formatos aceitos.
5. Após escolher o arquivo, o sistema valida e decodifica a imagem.
6. Durante a operação, é exibido feedback de carregamento.
7. Após sucesso, o sistema cria o nó de imagem, determina dimensões iniciais, resolve `parentId`, seleciona o objeto e abre os controles específicos.
8. A ferramenta retorna para Selecionar, seguindo o comportamento atual das demais ferramentas.
9. A criação é persistida e registrada como uma única alteração de histórico.

Cancelar o seletor não deve criar placeholder nem histórico.

### Substituição da fonte

1. O usuário seleciona uma imagem.
2. Aciona `Substituir imagem`.
3. Seleciona nova fonte.
4. O sistema mantém o objeto atual visível até a nova fonte ser validada.
5. Após sucesso, atualiza fonte e metadados naturais.
6. Identificador, nome editado, posição, dimensões, rotação, hierarquia, ordem e propriedades de Auto Layout são preservados.
7. Enquadramento é preservado quando compatível ou normalizado conforme regra aprovada.
8. A alteração é persistida como uma transação única.

Se a nova fonte falhar, a imagem anterior permanece ativa.

### Resize

- Com proporção bloqueada, resize preserva a relação de largura e altura da bounding box.
- Com proporção liberada, resize pode alterar a relação da bounding box.
- O conteúdo interno segue o modo de ajuste.
- O modelo é sincronizado ao concluir a interação.
- Auto Layout é recalculado quando a dimensão ocupada mudar.

### Crop

- Entrar em crop não altera imediatamente o documento.
- Preview é atualizado durante a manipulação.
- Confirmar aplica o novo enquadramento.
- Cancelar restaura o enquadramento anterior.
- Undo após confirmação retorna ao enquadramento anterior.
- Resize externo e crop interno são operações distintas.

### Drag-and-drop e colagem

Quando aprovados:

- o drop válido deve criar a imagem no ponto convertido para o sistema de coordenadas do Canvas;
- drop sobre frame deve respeitar a regra de `parentId`;
- drop inválido deve fornecer mensagem sem criar nó;
- colagem deve ignorar conteúdo não suportado sem bloquear atalhos do Canvas;
- ambos devem possuir alternativa de teclado pelo seletor de arquivo.

### Interações inválidas

- Arquivo não suportado: informar formato inválido.
- Falha de leitura: manter documento consistente e permitir nova tentativa.
- Fonte remota bloqueada: informar problema de origem ou rede.
- Dimensões naturais inválidas: não criar imagem pronta.
- Documento sem espaço de persistência: informar falha e não declarar salvamento concluído.
- Operação em item bloqueado: não modificar o documento e exibir feedback discreto.

## Feedback Visual

A barra de ferramentas deve indicar claramente quando a ferramenta Imagem está ativa.

O Canvas deve utilizar:

- placeholder de carregamento dentro da bounding box;
- indicador de erro com ícone, texto e ação;
- transformer compatível com imagem;
- badge de dimensões quando aplicável;
- máscara de crop;
- handles de crop distintos dos handles de resize;
- cursor de mover conteúdo durante crop;
- cursor de resize nos handles externos;
- indicador visual para proporção bloqueada;
- estado ativo para modo de ajuste;
- preview da fonte no inspector;
- tooltips nos controles iconográficos;
- confirmação visual de salvamento somente após persistência bem-sucedida.

Os novos controles devem reutilizar os padrões visuais existentes do Canvas e os tokens disponíveis, incluindo famílias de tipografia, escala de espaçamento, radius, estados de input, cores semânticas e foco. Não devem ser criados valores visuais arbitrários quando houver equivalentes em `tokens.json`.

O CSS atual do Canvas utiliza valores locais e classes escopadas. A nova interface deve permanecer escopada em `.konva-designer-page`, sem estilos inline novos.

## Responsividade

### Desktop

O fluxo completo deve funcionar na grade atual de três colunas. O inspector deve manter rolagem independente e não ocultar ações de substituição, crop, reset, duplicação ou exclusão.

### Viewport até 1280px

Deve respeitar o breakpoint existente, mantendo o painel direito utilizável. Grids de campos devem reduzir colunas quando a largura disponível não suportar labels e valores sem corte.

### Tablet

Não foi identificado contrato de layout tablet no Canvas atual. Deve ser confirmado se os painéis laterais serão recolhíveis, drawers ou permanecerão fixos. Até essa definição, a entrega não deve declarar suporte completo a tablet.

### Mobile

Não foi identificado fluxo mobile para o editor. Inserção de arquivo por input pode ser suportada pelo navegador, mas crop, transformer e painéis laterais exigem especificação própria. Mobile completo não deve ser considerado aceito sem decisão explícita.

### Zoom e pan

Todos os overlays de imagem devem acompanhar o transform efetivamente utilizado pelo Canvas. A implementação deve ser compatível tanto com o baseline fixo atual quanto com a versão de viewport documentada, após ser definida a fonte de verdade.

### Densidade de tela

A imagem deve permanecer nítida dentro das limitações da fonte, sem alterar as dimensões persistidas por diferença de `devicePixelRatio`. Handles e áreas de interação precisam manter tamanho visual utilizável.

## Acessibilidade

- A ferramenta Imagem deve possuir nome acessível e estado ativo compreensível.
- O seletor de arquivo deve ser acionável por teclado.
- Drag-and-drop não pode ser o único método de inserção.
- Controles de ícone devem possuir `aria-label` ou texto acessível.
- Modos de ajuste e toggles devem expor estado com `aria-pressed` ou semântica equivalente.
- Campos devem possuir labels associadas.
- Erros de carregamento devem ser anunciados em região apropriada, sem interromper o foco.
- O foco deve retornar ao controle acionador após cancelar o seletor ou fechar crop.
- Enter e Escape devem funcionar na edição de crop sem conflitar com campos editáveis.
- Estados de erro, bloqueio e seleção não podem depender somente de cor.
- Focus visible deve reutilizar o padrão de foco do Design System.
- Áreas de interação devem respeitar dimensões mínimas compatíveis com os componentes existentes e ser ampliadas em interfaces touch quando houver suporte aprovado.
- Texto alternativo deve fazer parte do modelo, mesmo que o canvas Konva não seja diretamente exposto como imagem semântica para leitores de tela.
- Animações de loading devem respeitar redução de movimento.

## Desempenho

- A fonte deve ser decodificada uma vez por referência válida e reutilizada durante re-renderizações.
- Drag, resize, pan, zoom e crop não devem recriar o elemento de imagem a cada evento.
- Atualizações contínuas devem usar redraw incremental das camadas afetadas.
- Filtros devem ativar cache somente quando necessário.
- O cache deve ser invalidado quando fonte, crop, dimensão ou filtro mudar.
- A duplicação do objeto não deve duplicar desnecessariamente o binário persistido quando a estratégia de assets permitir referência compartilhada.
- Snapshots de undo e redo não devem incorporar repetidamente grandes dados binários sem limite.
- Devem existir limites aprovados de formato, tamanho de arquivo, dimensões naturais e quantidade de imagens por documento.
- Imagens fora da página ativa não devem ser decodificadas ou redesenhadas sem necessidade.
- Substituição e exclusão devem liberar referências temporárias e caches.
- Erro em uma imagem não pode interromper a renderização do restante do documento.

## Compatibilidade com o Projeto

A implementação deve preservar:

- aplicação FastAPI com frontend estático;
- rota `/design-canvas`;
- Konva.js 9 já carregado pela tela;
- Lucide para iconografia;
- `state.doc.nodes` como modelo flat;
- `parentId` como relação hierárquica;
- `contentLayer` e `uiLayer` como separação entre documento e feedback de interface;
- seleção única existente;
- transformer atual;
- árvore de camadas derivada do modelo;
- inspector da aba Design;
- Auto Layout por `layout` e `layoutItem`;
- persistência local e exportação JSON enquanto não houver nova decisão de armazenamento;
- histórico por undo e redo;
- estilos escopados em `rebrand.css`;
- temas e tokens existentes.

Componentes e arquivos diretamente relacionados:

- `gitide_server/static/konva-designer.html`;
- `gitide_server/static/konva-designer.js`;
- seção `Konva Design Canvas` de `gitide_server/static/rebrand.css`;
- `tokens.json`;
- documentos Harness de Auto Layout e Canvas Infinito.

Tokens existentes aplicáveis incluem:

- famílias e pesos tipográficos globais;
- escala de espaçamento global;
- radius de botão, médio e grande;
- cores semânticas de texto, superfície, borda, informação, sucesso, warning e danger;
- contratos de input e button;
- foco global.

Limitações e conflitos confirmados:

- o objeto `image` não existe no modelo renderizado atual;
- a ferramenta cria um retângulo placeholder;
- o inspector não é contextual por tipo;
- não há política de assets para persistência de imagem;
- snapshots completos podem amplificar o consumo de armazenamento;
- suporte a Canvas Infinito está documentado como concluído, mas não está presente no arquivo JS atual;
- o HTML e as evidências Harness referenciam versões diferentes dos assets;
- o CSS atual não oferece suporte completo confirmado para tablet e mobile;
- não há testes existentes para objeto de imagem.

A reconciliação do baseline de viewport é pré-condição para validar posicionamento, drop, crop, overlays e comportamento responsivo.

## Critérios de Aceitação

### Fluxo principal

- [ ] A ferramenta Imagem não cria mais um retângulo renomeado como placeholder.
- [ ] Um arquivo válido cria um nó persistente com tipo de imagem.
- [ ] O nó é renderizado como imagem no Canvas.
- [ ] Cancelar o seletor não cria nó nem histórico.
- [ ] A imagem criada fica selecionada e exibe inspector específico.
- [ ] A árvore de camadas exibe ícone e nome de imagem.
- [ ] A imagem pode ser selecionada pelo Canvas e pela árvore.

### Fonte e carregamento

- [ ] O inspector permite substituir a fonte.
- [ ] Substituir preserva id, geometria, hierarquia e ordem de camada.
- [ ] A fonte anterior permanece ativa quando a substituição falha.
- [ ] Loading é visível durante decodificação.
- [ ] Erro de leitura apresenta mensagem e ação de recuperação.
- [ ] Formato inválido não cria imagem pronta.
- [ ] O documento não declara salvamento bem-sucedido quando a persistência falha.

### Geometria e enquadramento

- [ ] X, Y, largura, altura, rotação e opacidade refletem o modelo.
- [ ] Resize pelo transformer atualiza o inspector e o documento.
- [ ] Proporção inicia bloqueada.
- [ ] O usuário pode liberar e reativar a proporção.
- [ ] Modos Preencher, Ajustar, Esticar e Tamanho original produzem resultados distintos e verificáveis.
- [ ] Crop altera somente o enquadramento interno.
- [ ] Confirmar crop cria uma alteração de histórico.
- [ ] Cancelar crop restaura o estado anterior sem alteração persistente.
- [ ] Reset de crop retorna ao enquadramento padrão.
- [ ] Flip horizontal e vertical são persistidos.

### Aparência

- [ ] Corner radius é aplicado sem converter a imagem em retângulo.
- [ ] Stroke acompanha a bounding box.
- [ ] Filtros aprovados possuem preview, persistência, reset, undo e redo.
- [ ] Controles incompatíveis ficam desabilitados com motivo compreensível.

### Hierarquia e Auto Layout

- [ ] Inserir imagem dentro de frame atribui `parentId` compatível.
- [ ] Mover frame desloca a imagem descendente conforme a regra atual.
- [ ] Imagem estática participa do fluxo de Auto Layout usando sua bounding box.
- [ ] Imagem absoluta fica fora do cálculo do fluxo.
- [ ] Substituir fonte não altera ordem do Auto Layout.
- [ ] Duplicar preserva hierarquia compatível.
- [ ] Excluir frame trata a imagem descendente conforme a regra atual do Canvas.

### Persistência e histórico

- [ ] Reload restaura fonte, geometria, crop, aparência e hierarquia.
- [ ] Export JSON inclui propriedades serializáveis da imagem.
- [ ] O JSON não inclui elementos HTML, caches ou URLs temporárias inválidas.
- [ ] Undo remove uma imagem recém-criada.
- [ ] Redo restaura a imagem.
- [ ] Undo reverte substituição, crop, resize, aparência e exclusão.
- [ ] Uma alteração contínua de slider não cria histórico excessivo.
- [ ] O binário não é duplicado desnecessariamente em snapshots, conforme estratégia aprovada.

### Acessibilidade

- [ ] Inserção completa pode ser feita sem drag-and-drop.
- [ ] Todos os controles possuem nome acessível.
- [ ] Foco é visível.
- [ ] Estado ativo não depende somente de cor.
- [ ] Erros são anunciados sem perda de foco.
- [ ] Enter e Escape funcionam no crop sem acionar atalhos indevidos.
- [ ] Texto alternativo é persistido no modelo.

### Responsividade e viewport

- [ ] O inspector permanece utilizável no breakpoint existente de `1280px`.
- [ ] Controles não provocam overflow horizontal no painel direito.
- [ ] Overlays permanecem alinhados com a imagem no zoom efetivamente implementado.
- [ ] A validação identifica explicitamente qual baseline de viewport foi utilizado.
- [ ] O suporte não é declarado como tablet ou mobile completo sem contrato específico.

### Performance e resiliência

- [ ] Drag, resize, crop, pan e zoom não decodificam novamente a fonte a cada evento.
- [ ] Filtros inativos não mantêm cache desnecessário.
- [ ] Excluir ou substituir libera referências temporárias.
- [ ] Uma imagem com erro não impede renderização dos demais objetos.
- [ ] Limites de arquivo e dimensões são aplicados conforme decisão aprovada.

### Compatibilidade

- [ ] Documentos antigos sem imagem continuam carregando.
- [ ] Retângulos existentes chamados `Imagem placeholder` não são convertidos automaticamente sem regra aprovada.
- [ ] Auto Layout existente continua funcional.
- [ ] Exportação, seleção, duplicação e exclusão dos demais tipos não sofrem regressão.
- [ ] Não é criado backend novo sem decisão explícita de persistência.
- [ ] Não são adicionados estilos inline novos.

## Perguntas Técnicas e Contextuais

### Estrutura

1. A imagem será sempre um elemento folha ou deverá suportar máscara/container no futuro?
2. O nome inicial do layer deve usar o nome do arquivo, `Imagem` ou uma sequência numerada?
3. A árvore de camadas precisa permitir renomear, bloquear e ocultar layers nesta entrega?
4. A fonte oficial do asset será o documento, um armazenamento local separado ou um serviço de assets?
5. Imagens duplicadas devem compartilhar a mesma referência de asset?
6. Deve existir um estado persistente de imagem vazia ou o nó só pode existir após uma fonte válida?
7. A versão documentada de Canvas Infinito foi revertida, está em outra branch ou precisa ser restaurada antes desta feature?

### Posicionamento

1. A ferramenta deve abrir o seletor imediatamente ou somente após o usuário clicar no ponto de inserção?
2. Ao inserir sem clique explícito, a imagem deve aparecer no centro do viewport, no centro do frame selecionado ou em posição padrão?
3. Qual deve ser o tamanho inicial máximo de imagens maiores que a área visível?
4. O modo inicial deve ser Preencher, Ajustar, Esticar ou Tamanho original?
5. A proporção deve permanecer bloqueada por padrão após substituir a fonte?
6. Frames devem recortar visualmente filhos que ultrapassem seus limites?
7. O modo Ajustar deve usar fundo transparente ou permitir cor de fundo?
8. Ao selecionar Tamanho original dentro de Auto Layout, a mudança de dimensões deve ocorrer automaticamente?
9. Alterar crop deve preservar a bounding box em todos os casos?
10. Qual ação deve ocorrer ao clicar fora durante edição de crop: confirmar, cancelar ou manter o modo ativo?

### Responsividade

1. Tablet e mobile fazem parte da primeira entrega ou o editor permanece desktop-only?
2. Em largura reduzida, o painel direito deve recolher, virar drawer ou sobrepor o Canvas?
3. Quais breakpoints oficiais devem prevalecer: os tokens gerais ou somente o breakpoint atual de `1280px`?
4. Crop por toque precisa ser suportado na primeira entrega?
5. Drag-and-drop deve ser desabilitado em touch e substituído por seletor de arquivo?
6. Qual área mínima de interação deve ser adotada para handles em dispositivos touch?
7. A validação deve usar o viewport fixo atual ou a arquitetura de Canvas Infinito documentada?

### Estado

1. Bloqueio e visibilidade de layer entram no escopo desta entrega?
2. Um item bloqueado pode ser selecionado e inspecionado ou deve ignorar interação no Canvas?
3. O estado de erro deve ser persistido ou recalculado a cada carregamento?
4. O sistema deve manter a imagem anterior visível enquanto uma substituição está carregando?
5. O texto alternativo é obrigatório, opcional ou somente informativo?
6. Filtros devem ser armazenados mesmo quando desativados para permitir restauração posterior?
7. Qual estado deve ser exibido quando o asset persistido não estiver mais disponível?
8. O usuário pode limpar a fonte e manter a bounding box vazia?

### Comportamento Esperado da Interação

1. Drag-and-drop de arquivo sobre o Canvas faz parte da primeira entrega?
2. Colar imagem da área de transferência faz parte da primeira entrega?
3. Fontes por URL devem ser suportadas?
4. Quais formatos de arquivo devem ser aceitos?
5. SVG deve ser permitido, rasterizado ou ficar fora do escopo por segurança?
6. A substituição deve preservar crop ou resetá-lo quando a proporção natural mudar?
7. Filtros devem atualizar em tempo real ou somente após confirmação?
8. Alterações por slider formam uma transação ao soltar o controle?
9. Deve existir atalho de teclado específico para inserir imagem?
10. Duplo clique na imagem deve entrar em crop, substituir a fonte ou não ter ação?
11. Escape durante loading cancela a criação?
12. A ação Excluir remove também a referência de asset quando nenhuma outra imagem a utiliza?

### Design System

1. Os novos controles devem seguir o visual dark/turquesa atual do Canvas ou migrar para a direção oficial mais recente descrita em `design_rebrand.md`?
2. A seção de imagem deve reutilizar o cartão visual de Auto Layout ou adotar grupos simples do inspector?
3. Quais ícones Lucide representam substituir, crop, proporção, flip e reset?
4. Filtros devem aparecer expandidos, recolhidos ou em popover?
5. Existe necessidade de novos tokens específicos para máscara de crop, loading e erro?
6. O foco do Canvas deve usar o token global de foco ou o destaque turquesa local?
7. Temas claro e escuro precisam funcionar no Design Canvas nesta entrega?

### Persistência e Histórico

1. A imagem será armazenada como dado incorporado, asset local separado ou referência remota?
2. Qual é o limite de tamanho por arquivo?
3. Qual é o limite de dimensões naturais?
4. Qual é o limite de imagens por documento?
5. O histórico deve referenciar assets por id para evitar duplicação do binário?
6. A duplicação de imagem deve compartilhar ou copiar o asset persistido?
7. Como recuperar documentos antigos quando o asset referenciado não existir?
8. A persistência deve acontecer automaticamente em cada alteração ou somente no botão Salvar?
9. O botão Salvar deve exibir erro quando `localStorage` não comportar o documento?
10. Projetos antigos com `Imagem placeholder` devem receber ação manual de conversão?
11. Fontes por URL devem ser incorporadas no save para evitar indisponibilidade futura?
12. A substituição da fonte deve ser uma única transação de undo e redo?
13. Crop e filtros devem ser incluídos no mesmo snapshot quando alterados em sequência dentro de uma sessão de edição?
