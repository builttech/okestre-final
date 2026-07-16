# Imple: Navegação, Zoom e Pan em Canvas Infinito

# Implementação de Navegação, Zoom e Pan em Canvas Infinito

## Objetivo

Evoluir o sistema de navegação do Canvas Design construído com Konva.js, oferecendo uma experiência de exploração espacial mais fluida, previsível e compatível com ferramentas profissionais de design.

A implementação deverá permitir:

- Zoom in e zoom out por atalhos de mouse, trackpad e teclado.
- Zoom centralizado na posição atual do cursor.
- Navegação horizontal e vertical sem limites visuais aparentes.
- Movimentação do viewport para cima, baixo, esquerda e direita.
- Pan por mouse, teclado, trackpad e gestos touch.
- Preservação da posição dos objetos no sistema de coordenadas global.
- Desempenho consistente em canvases com grande quantidade de elementos.

O próprio Konva disponibiliza referências para zoom relativo ao cursor e para a construção de um canvas virtualmente infinito por meio da combinação de escala e deslocamento do `Stage`.

---

## 1\. Arquitetura do Canvas Infinito

### 1.1 Viewport e espaço de trabalho

O Canvas Design deverá separar conceitualmente dois sistemas de coordenadas:

- **Screen Space:** coordenadas físicas da área visível no navegador.
- **World Space:** coordenadas virtuais nas quais frames, textos, imagens e demais objetos são posicionados.
- **Viewport Transform:** transformação responsável por converter coordenadas do World Space para o Screen Space.

O viewport deverá ser controlado por um estado central contendo, no mínimo:

- Posição horizontal do viewport.
- Posição vertical do viewport.
- Escala atual.
- Escala mínima.
- Escala máxima.
- Posição do cursor utilizada como ponto focal do zoom.
- Estado atual de interação: idle, zooming, panning ou dragging.

### 1.2 Canvas virtualmente infinito

A área de trabalho não deverá ser implementada por meio da criação de um `Stage` fisicamente gigantesco.

O comportamento infinito deverá ser simulado por:

- Alteração de `x` e `y` do viewport ou do `Stage`.
- Alteração uniforme de `scaleX` e `scaleY`.
- Manutenção dos objetos em coordenadas globais independentes do tamanho da tela.
- Renderização apenas da área necessária para o viewport atual.
- Ausência de limites rígidos de deslocamento horizontal ou vertical.

A documentação do Konva alerta que canvases fisicamente muito grandes podem causar degradação de desempenho. A abordagem recomendada é manter o canvas próximo ao tamanho do viewport e simular a navegação por transformações.

---

## 2\. Comportamento de Zoom

### 2.1 Zoom pelo mouse

O usuário deverá conseguir controlar o zoom por meio dos seguintes atalhos:

- `Ctrl + Wheel` no Windows e Linux.
- `Command + Wheel` no macOS.
- Movimento da roda para cima: zoom in.
- Movimento da roda para baixo: zoom out.
- Pinch no trackpad: zoom in ou zoom out.
- Botões de zoom na interface, quando disponíveis.

O evento deverá impedir o comportamento nativo do navegador somente quando a interação ocorrer sobre a área do canvas.

Isso evita:

- Zoom da página.
- Scroll da página externa.
- Conflitos entre o Canvas Design e o navegador.

### 2.2 Zoom relativo ao cursor

O zoom deverá utilizar a posição atual do ponteiro como ponto focal.

Ao ampliar ou reduzir:

1. Capturar a posição do cursor no Screen Space.
2. Converter essa posição para World Space utilizando a transformação atual.
3. Aplicar a nova escala.
4. Recalcular o deslocamento do viewport.
5. Manter o mesmo ponto do conteúdo visualmente abaixo do cursor.

Esse comportamento evita que o conteúdo “escape” do ponteiro durante o zoom e oferece uma interação semelhante à de editores gráficos profissionais. O Konva apresenta esse modelo em sua implementação oficial de zoom relativo ao ponteiro.

### 2.3 Incremento de escala

O zoom deverá ser progressivo e proporcional, evitando saltos lineares excessivos.

Recomendação inicial:

- Escala mínima: `5%`.
- Escala padrão: `100%`.
- Escala máxima: `6400%`.
- Incremento baseado em fator multiplicativo.
- Fator aproximado por evento: entre `1.05` e `1.15`.

O fator deverá considerar:

- Intensidade do `deltaY`.
- Tipo de dispositivo.
- Roda física do mouse.
- Trackpad de alta precisão.
- Frequência dos eventos recebidos.

### 2.4 Limites de zoom

O zoom deverá ser limitado apenas pela escala mínima e máxima.

Ao atingir um limite:

- O sistema não deverá continuar alterando a posição do viewport.
- Não deverá ocorrer efeito de salto.
- O indicador de zoom deverá permanecer no valor limite.
- Eventos adicionais na mesma direção deverão ser ignorados.

### 2.5 Feedback visual

Durante o zoom, a interface deverá apresentar:

- Indicador percentual de escala.
- Atualização em tempo real.
- Transição visual fluida.
- Opção de restaurar o zoom para `100%`.
- Opção “Ajustar seleção”.
- Opção “Ajustar todos os objetos”.
- Opção “Centralizar conteúdo”.

O indicador poderá ser exibido em uma toolbar inferior ou em um controle flutuante do viewport.

---

## 3\. Comportamento de Pan e Scroll

### 3.1 Navegação vertical

Quando nenhum modificador estiver pressionado:

- `Wheel` deverá mover o viewport verticalmente.
- Scroll para cima deverá deslocar a visualização para cima.
- Scroll para baixo deverá deslocar a visualização para baixo.

O comportamento deverá ser normalizado para reduzir diferenças entre sistemas operacionais, navegadores e dispositivos de entrada.

### 3.2 Navegação horizontal

O usuário deverá conseguir movimentar o viewport horizontalmente por:

- `Shift + Wheel`.
- Gesto horizontal no trackpad.
- Arraste utilizando o botão central do mouse.
- Arraste com a ferramenta Hand.
- `Space + Drag` com o botão principal do mouse.

### 3.3 Pan por arraste

Durante o pan:

- O cursor deverá mudar de `grab` para `grabbing`.
- A seleção atual deverá ser preservada.
- Objetos não deverão ser movimentados.
- Handles de transformação não deverão ser ativados.
- O deslocamento deverá continuar enquanto o ponteiro estiver pressionado.
- A interação deverá ser encerrada em `pointerup`, mesmo que o cursor saia da área do canvas.

O Konva permite que o `Stage` seja arrastável, mas em editores de design é recomendável controlar explicitamente quando o pan está ativo para evitar conflitos com a movimentação de objetos.

### 3.4 Navegação ilimitada

O viewport deverá permitir deslocamento em todas as direções:

- Top.
- Bottom.
- Left.
- Right.

Não deverão existir limites rígidos vinculados à posição dos objetos.

Mesmo quando não houver elementos visíveis, o usuário deverá conseguir continuar navegando pelo espaço virtual.

### 3.5 Scroll próximo às bordas

Durante o arraste de objetos, quando o ponteiro se aproximar das bordas do viewport, o sistema poderá iniciar um auto-pan progressivo.

O comportamento deverá considerar:

- Zona de ativação próxima às bordas.
- Velocidade proporcional à proximidade da borda.
- Interrupção imediata ao afastar o cursor.
- Continuidade do drag do objeto.
- Atualização correta das coordenadas globais.

O Konva possui uma referência específica para auto-scroll durante o arraste próximo às extremidades do Stage.

---

## 4\. Matriz de Interações

### Mouse

- `Wheel`: scroll vertical.
- `Shift + Wheel`: scroll horizontal.
- `Ctrl + Wheel`: zoom no Windows e Linux.
- `Command + Wheel`: zoom no macOS.
- Botão central + arraste: pan.
- `Space + botão principal + arraste`: pan.
- Botão principal sobre objeto: seleção ou movimentação do objeto.
- Botão principal sobre área vazia: limpeza de seleção ou início de seleção por área.

### Trackpad

- Movimento com dois dedos: pan horizontal e vertical.
- Pinch: zoom relativo ao centro do gesto.
- Tap: seleção.
- Click-and-drag: movimentação ou seleção por área.

### Teclado

- `+`: zoom in.
- `-`: zoom out.
- `0`: retornar ao zoom de 100%.
- `1`: ajustar todos os objetos ao viewport.
- `2`: ajustar a seleção ao viewport.
- `Space`: ativar temporariamente a ferramenta de pan.
- Setas direcionais: movimentar objetos selecionados.
- Setas direcionais sem seleção, opcionalmente: movimentar o viewport.

Os atalhos não deverão ser executados enquanto o usuário estiver editando:

- Campos de texto.
- Inputs numéricos.
- Elementos `contenteditable`.
- Textos diretamente no canvas.

---

## 5\. Suporte a Dispositivos Touch

Em dispositivos móveis e tablets, o sistema deverá oferecer:

- Pan com um dedo sobre área vazia.
- Pinch-to-zoom com dois dedos.
- Zoom centralizado no ponto médio entre os dois toques.
- Bloqueio da movimentação da página durante gestos dentro do canvas.
- Preservação da seleção durante o pan.
- Distinção entre arraste de objeto e arraste do viewport.

O suporte a pinch deve calcular manualmente a distância e o ponto médio entre os toques, atualizando simultaneamente escala e posição do Stage. A documentação do Konva apresenta essa estratégia para zoom multitouch.

---

## 6\. Gerenciamento de Estado

### 6.1 Estado do viewport

O estado de navegação deverá ser desacoplado do estado dos objetos.

Estrutura conceitual:

- `viewport.x`
- `viewport.y`
- `viewport.scale`
- `viewport.interactionMode`
- `viewport.isPanning`
- `viewport.isZooming`
- `viewport.lastPointerPosition`

### 6.2 Estado dos objetos

Frames e objetos deverão continuar armazenando posições em World Space.

A navegação não deverá modificar:

- Coordenadas persistidas dos objetos.
- Dimensões reais.
- Rotação.
- Hierarquia.
- Relação entre objetos e frames.
- Ordem das camadas.

Somente ações explícitas de edição deverão alterar o estado dos elementos.

### 6.3 Persistência

Deverá ser definido se a posição do viewport será:

- Restaurada ao reabrir o projeto.
- Mantida durante a sessão.
- Compartilhada entre usuários.
- Reiniciada ao trocar de página.
- Armazenada por página ou por documento.

Como padrão, recomenda-se armazenar o viewport por página e por usuário, sem compartilhá-lo como parte do conteúdo colaborativo.

---

## 7\. Conversão de Coordenadas

Todas as interações deverão utilizar funções centralizadas de conversão entre coordenadas.

Operações necessárias:

- Screen Space para World Space.
- World Space para Screen Space.
- Coordenadas do ponteiro para coordenadas relativas a grupos.
- Bounding boxes transformadas.
- Posição absoluta para posição relativa ao parent.
- Compensação de escala durante drag, resize e criação de objetos.

Essa centralização é necessária para evitar inconsistências em funcionalidades como:

- Seleção por área.
- Drag-and-drop.
- Snapping.
- Criação de objetos.
- Guias de alinhamento.
- Menus contextuais.
- Posicionamento de overlays HTML.
- Inserção de objetos dentro de frames.

---

## 8\. Responsividade

O `Stage` deverá acompanhar as dimensões disponíveis no container da aplicação.

A implementação deverá:

- Observar alterações no tamanho do container.
- Atualizar largura e altura do Stage.
- Preservar escala e posição do viewport.
- Não reposicionar objetos ao redimensionar a janela.
- Não utilizar dimensões fixas vinculadas à resolução inicial.
- Considerar barras laterais, toolbar, painéis e áreas recolhíveis.

O Konva disponibiliza estratégias de adaptação do Stage ao tamanho da janela, mas a escala do viewport deverá permanecer independente da responsividade estrutural da interface.

---

## 9\. Performance e Renderização

### 9.1 Atualização de eventos

Eventos de `wheel`, `pointermove` e `touchmove` podem ocorrer em alta frequência.

A implementação deverá:

- Agrupar atualizações por frame de animação.
- Utilizar `requestAnimationFrame`.
- Evitar atualizações globais desnecessárias de estado.
- Evitar recriar todos os objetos durante pan e zoom.
- Atualizar preferencialmente apenas a transformação do Stage ou da camada principal.
- Utilizar batch drawing quando aplicável.

### 9.2 Separação de camadas

Recomenda-se separar:

- Grid e background.
- Conteúdo principal.
- Seleção e transformers.
- Guias e snapping.
- Overlays temporários.
- Cursores colaborativos.

Essa separação permite controlar redraws e eventos de forma mais eficiente.

### 9.3 Área visível

Para documentos complexos, deverá ser considerada uma estratégia de culling:

- Identificar objetos fora do viewport.
- Suspender renderização de elementos muito distantes.
- Preservar os objetos no modelo de dados.
- Reativar a renderização ao retornarem à área visível.

### 9.4 Qualidade visual

Durante o zoom:

- Strokes deverão manter comportamento visual consistente.
- Handles de seleção deverão permanecer utilizáveis.
- Textos não deverão apresentar distorções permanentes.
- O grid deverá adaptar sua densidade ao nível de zoom.
- Overlays HTML deverão acompanhar corretamente a transformação.

---

## 10\. Grid do Canvas

O grid deverá acompanhar o World Space, e não o Screen Space.

Comportamento esperado:

- O grid se desloca junto com o viewport.
- O espaçamento aparente muda conforme o zoom.
- Linhas secundárias podem ser ocultadas em escalas reduzidas.
- Linhas principais podem ser reforçadas em intervalos maiores.
- O grid não deverá apresentar saltos durante o pan.
- O grid deverá permanecer alinhado às coordenadas globais.

Para evitar sobrecarga, o grid deverá ser renderizado apenas na região visível, calculando dinamicamente seu ponto inicial e final.

---

## 11\. Acessibilidade e Usabilidade

A navegação deverá oferecer alternativas aos gestos de mouse.

Requisitos:

- Todos os comandos de zoom devem possuir alternativa por teclado.
- Os atalhos devem estar documentados em uma área de ajuda.
- O nível de zoom deve possuir representação textual.
- O foco do teclado não deve ser capturado permanentemente pelo canvas.
- O usuário deverá conseguir restaurar uma visualização perdida.
- Animações deverão respeitar preferências de redução de movimento.
- O cursor deverá comunicar claramente o modo de interação atual.

---

## 12\. Critérios de Aceite

A implementação será considerada concluída quando:

- `Ctrl + Wheel` executar zoom no Windows e Linux.
- `Command + Wheel` executar zoom no macOS.
- O zoom permanecer centralizado no cursor.
- O usuário puder navegar ilimitadamente nos quatro eixos.
- `Space + Drag` executar pan sem mover objetos.
- O botão central do mouse executar pan.
- Trackpads suportarem pan horizontal e vertical.
- Gestos pinch funcionarem em dispositivos touch.
- O zoom não alterar as coordenadas persistidas dos objetos.
- O redimensionamento da janela não reiniciar o viewport.
- O sistema impedir o zoom nativo da página durante a interação no canvas.
- O pan e o zoom permanecerem fluidos com documentos complexos.
- A seleção e os transformers permanecerem sincronizados.
- Menus contextuais e overlays HTML acompanharem o viewport.
- Os limites mínimo e máximo de zoom forem respeitados.
- O usuário conseguir retornar rapidamente ao conteúdo utilizando “Ajustar todos”.

---

## Perguntas Técnicas e Contextuais

### Estrutura e arquitetura

- O viewport será aplicado diretamente ao `Stage` ou a um `Group` raiz?
- Existem camadas independentes para grid, objetos, seleção e overlays?
- O estado atual do canvas está centralizado ou distribuído entre componentes?
- Qual framework está sendo utilizado com o Konva: React, Vue, JavaScript puro ou outro?
- As coordenadas dos objetos são absolutas ou relativas aos respectivos frames?
- Existe uma camada HTML sobreposta ao canvas?
- Como o estado do viewport será persistido por página?
- O sistema possui colaboração em tempo real?

### Zoom

- Quais serão os valores mínimo e máximo de zoom?
- O zoom deverá utilizar incrementos fixos ou progressivos?
- O centro do zoom será sempre o cursor ou poderá ser o centro do viewport?
- O pinch do trackpad já é diferenciado do scroll convencional?
- O sistema deverá animar comandos como “Ajustar seleção”?
- O nível de zoom será persistido ao reabrir o documento?

### Pan e scroll

- O scroll convencional deverá mover o viewport ou a página da aplicação?
- O pan será permitido ao arrastar qualquer área vazia?
- O botão central do mouse será suportado?
- `Space + Drag` deverá funcionar mesmo com objetos selecionados?
- O pan deverá possuir inércia em trackpads e dispositivos touch?
- Será necessário auto-pan durante o drag de objetos?
- Existem regiões da interface em que os atalhos devem ser desativados?

### Posicionamento

- O ponto inicial do documento será centralizado ou baseado na origem `0,0`?
- A origem global deverá possuir representação visual?
- Objetos poderão utilizar coordenadas negativas?
- O usuário poderá redefinir manualmente a origem do viewport?
- Como menus contextuais serão posicionados quando o canvas estiver escalado?
- Como elementos HTML editáveis serão sincronizados com objetos Konva?

### Responsividade

- O canvas ocupará toda a viewport ou somente uma região da interface?
- Painéis laterais podem ser redimensionados ou recolhidos?
- A alteração do container deverá preservar o ponto central atual?
- Qual será o comportamento ao alternar orientação em tablets?
- O sistema precisará oferecer atalhos alternativos em dispositivos sem teclado?
- A experiência mobile permitirá edição completa ou somente navegação?

### Estado e persistência

- A posição do viewport será editável, persistente ou temporária?
- O viewport será salvo por usuário, página ou documento?
- Alterações de zoom deverão entrar no histórico de undo e redo?
- O pan deverá ser sincronizado entre usuários colaboradores?
- O modo Hand será temporário ou selecionável como ferramenta fixa?
- O último nível de zoom deverá ser restaurado após recarregar a aplicação?

### Interação e feedback

- Onde o percentual de zoom será exibido?
- Haverá controles visuais de zoom além dos atalhos?
- Qual cursor será utilizado em cada modo de navegação?
- Como o sistema comunicará que o limite de zoom foi atingido?
- O usuário poderá bloquear temporariamente o pan?
- Haverá minimapa para documentos extensos?
- O grid deverá mudar de densidade conforme o nível de zoom?
- As animações deverão ser removidas quando “reduzir movimento” estiver ativo?

### Performance

- Qual é a quantidade máxima esperada de objetos por documento?
- Existem imagens de alta resolução dentro do canvas?
- O sistema utiliza cache de shapes ou layers?
- Existe virtualização ou culling de objetos fora do viewport?
- Quais camadas precisam receber eventos de hit detection?
- O pan e o zoom atualmente atualizam estado reativo a cada evento?
- Existe uma meta mínima de FPS para a interação?
- Como o desempenho será medido em dispositivos de menor capacidade?