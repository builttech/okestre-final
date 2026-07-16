# RF-0001-01 — Modelar e ativar Auto Layout em frames

## Identificação

- ID: `RF-0001-01`
- REQ pai: `REQ-0001`
- Título: Modelar e ativar Auto Layout em frames
- Projeto: `act-ide-teste`

## Objetivo

Permitir que um frame selecionado receba, remova e mantenha propriedades de Auto Layout no modelo local do Design Canvas.

## Contexto funcional

O canvas já possui frames e elementos filhos vinculados por `parentId`. A feature deve estender esse modelo com uma propriedade `layout` no frame e uma propriedade `layoutItem` nos filhos quando necessário, sem backend novo.

## História do usuário

Como usuário da aba Design, quero ativar Auto Layout em um frame selecionado para que os elementos internos passem a ser organizados automaticamente.

## Descrição funcional

Ao selecionar um frame, a seção Auto Layout deve oferecer botão de ativação. Ao ativar, o frame recebe configuração padrão de layout flexível. Seus filhos passam a participar do fluxo, exceto itens marcados como absolutos. Ao remover, a posição visual atual dos filhos é preservada e o frame deixa de recalcular seus filhos automaticamente.

## Fluxo funcional

1. Usuário seleciona um frame.
2. Sistema exibe seção Auto Layout disponível.
3. Usuário clica em ativar.
4. Sistema cria `layout.enabled = true` com defaults seguros.
5. Sistema normaliza `layoutItem` dos filhos.
6. Sistema recalcula layout.
7. Usuário pode remover Auto Layout.
8. Sistema preserva coordenadas visuais e desativa/remova a configuração.

## Regras de negócio

- Auto Layout só é ativável em frames.
- Frames raiz e frames filhos são compatíveis.
- Elementos não-frame não recebem `layout` de container.
- A direção inicial padrão é horizontal.
- Valores numéricos negativos devem ser normalizados para zero.

## Validações funcionais

- Sem seleção: controles indisponíveis.
- Seleção de elemento não-frame: mensagem de incompatibilidade.
- Frame bloqueado: controles podem permanecer desabilitados.
- Frame com Auto Layout: botão de remover disponível.

## Dados necessários

- `node.type`
- `node.parentId`
- `node.layout`
- `node.layoutItem`

## Permissões

Não aplicável. A feature opera no frontend local do canvas.

## Integrações

- Integração com renderização Konva existente.
- Integração com persistência local `localStorage` existente.

## Critérios de aceite

- Um frame selecionado permite ativar Auto Layout.
- Um frame com Auto Layout permite remover Auto Layout.
- Defaults são criados sem quebrar documentos antigos.
- Filhos preservam vínculo por `parentId`.
- Remoção preserva aparência visual atual.

## Fora do escopo

- Criar frame a partir de multi-seleção completa.
- Persistência remota.
- Grid Layout.

## Dependências

- `gitide_server/static/konva-designer.js`.
- Modelo atual `state.doc.nodes`.

## Riscos

- Documentos antigos podem conter dados incompletos; a normalização deve ser defensiva.

## Rastreabilidade

- REQ: `REQ-0001`
- Discovery: seção 3, 11 e 17 do documento de Auto Layout.

## Histórico

- 2026-07-16: RF criado.

## Checklist de qualidade

- [x] Vinculado ao REQ pai.
- [x] Fluxo funcional definido.
- [x] Regras e critérios de aceite definidos.
