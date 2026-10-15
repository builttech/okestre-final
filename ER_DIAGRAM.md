# Diagramas ER

Abra **Diagramas ER** no menu Workspace ou acesse `/diagrams` após entrar no Okestre. O Design Canvas também possui um link para a tela.

- Entidades: criar, renomear e excluir (a exclusão remove suas relações).
- Atributos: tipo, nome, chaves PK/FK/UK e comentário.
- Relações: origem/destino, cardinalidades nas duas pontas, linha identificadora ou não identificadora e rótulo.
- Código: editar e aplicar Mermaid `erDiagram`. Código inválido não substitui o modelo atual.
- Direções TB, BT, LR e RL; prévia automática, zoom e ajuste à largura.
- Exportação de texto `.mmd`, cópia do código e exportação da prévia SVG.
- Importação de `.mmd`, `.mermaid` ou `.txt` com até 100 KB.

O editor visual aceita a sintaxe produzida pela própria tela: entidades com blocos de atributos, relações com rótulos entre aspas e `direction`. Entidades referenciadas em relações podem ser declaradas implicitamente. Não importa temas/frontmatter, aliases, classes, estilos ou outras linguagens Mermaid: esses recursos geram mensagem de sintaxe não suportada, sem substituir o modelo atual. Nomes usam letras, números, `_` e `-`, sem espaços; rótulos e comentários não aceitam aspas internas ou quebras de linha. Até 100 entidades e 200 relações.

Há um rascunho por origem no armazenamento deste navegador. Ele não é salvo no projeto nem sincronizado entre dispositivos/usuários; exporte antes de limpar dados do navegador ou trocar de computador. Novo, Exemplo e Importar pedem confirmação antes de substituir o rascunho. Código ainda não aplicado apresenta aviso ao sair da página.

O renderizador Mermaid 11.12.0 e sua licença estão incluídos em `gitide_server/static/vendor`; a tela não depende de CDN nem envia o diagrama a um serviço externo. Usa `securityLevel: strict`.

Referência da sintaxe: https://mermaid.js.org/syntax/entityRelationshipDiagram.html

Validação: `python -m pytest tests/test_er_diagram_browser.py tests/test_local_main.py -q` (Microsoft Edge e Playwright). Cobre renderização do exemplo, exportações, importação, edição visual, cardinalidades, nomes, exclusão de relações dependentes, persistência local, código inválido, largura móvel e autenticação da rota real.
