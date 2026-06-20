# Gerenciador de Banco de Dados: Explorer de Tabelas no GitIDE

Este plano visa adicionar um painel lateral de **Database Explorer** dentro da aba "Banco de Dados (SQL)". Esse painel listará dinamicamente as tabelas do banco de dados configurado (SQLite, PostgreSQL ou MySQL) e permitirá que o usuário clique em qualquer tabela para carregar e visualizar seus dados de forma instantânea.

## User Review Required

> [!IMPORTANT]
> - As consultas para listar tabelas serão feitas sob o mesmo endpoint `/api/projects/{project_id}/db/query` existente usando SQL nativo conforme o tipo de banco (SQLite, PG ou MySQL).
> - Ao clicar em uma tabela listada no explorer, a query do editor SQL será atualizada para `SELECT * FROM {tabela} LIMIT 50;` e executada automaticamente.

## Proposed Changes

### Frontend Components

---

#### [MODIFY] [index.html](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/index.html)
- Estruturar a aba `#tab-database` em duas colunas:
  - **Coluna Esquerda (Sidebar Explorer)**: Exibição do status da conexão ("Conectado" ou "Não Conectado") com bolinha colorida, botão de atualizar tabelas e lista de tabelas (`#db-tables-list`).
  - **Coluna Direita (Área Principal)**: Agrupa o editor SQL (`.db-editor-panel`) e a tabela de resultados (`.db-results-panel`).
- Adicionar um botão "Conectar & Listar Tabelas" (`#btn-db-connect`) ao lado do botão de executar query no editor SQL.

---

#### [MODIFY] [style.css](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/style.css)
- Implementar a estilização de duas colunas para o layout de banco de dados (`.database-layout`, `.db-explorer-sidebar`, `.db-content-area`).
- Adicionar estilos visuais para os itens da lista de tabelas (`.db-table-item`, `.db-table-item-left`, hover e classe `.active`).
- Estilizar o indicador de status de conexão com animação sutil (glow).

---

#### [MODIFY] [app.js](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/app.js)
- Implementar a função `loadDbTables()`:
  - Identifica o tipo de banco selecionado e sua connection string.
  - Executa uma consulta apropriada (`information_schema.tables` ou `sqlite_master`) via API `/api/projects/{project_id}/db/query`.
  - Atualiza o indicador de status e renderiza a lista de tabelas.
- Implementar `renderDbTablesList(rows)`:
  - Cria elementos HTML clicáveis para cada tabela retornada.
  - Associa o evento de clique para preencher a query `SELECT * FROM {tabela} LIMIT 50;` e rodar a query imediatamente.
- Adicionar gatilho automático ao abrir a aba `tab-database` e quando o projeto ou as credenciais forem selecionadas/alteradas.
- Registrar os ouvintes de eventos para o botão de conexão e atualização.

## Verification Plan

### Manual Verification
1. Ir na aba "Banco de Dados (SQL)".
2. Informar as credenciais ou connection string de teste.
3. Clicar em "Conectar & Listar Tabelas".
4. Confirmar que a lista de tabelas aparece no painel lateral.
5. Clicar em uma das tabelas e atestar que a query `SELECT * FROM {tabela} LIMIT 50;` é gerada e executada de imediato.
