# Painel Integrado para Acesso ao GPT / ChatGPT no GitIDE

Este plano visa adicionar uma nova aba "Chat GPT" no painel lateral do GitIDE. Esta aba conterá um campo de texto para inserir uma URL (como o site oficial do ChatGPT ou um cliente GPT personalizado/Action Link) e um botão para carregar o chat diretamente dentro de um painel de iframe na interface do GitIDE, evitando a necessidade de alternar entre o navegador e o editor. A URL configurada será persistida no `localStorage` do navegador para recarregamento automático.

## User Review Required

> [!WARNING]
> Sites que utilizam cabeçalhos rígidos de segurança, como `X-Frame-Options: DENY` ou regras restritivas de `Content-Security-Policy (frame-ancestors)` (por exemplo, o site principal do ChatGPT público `chatgpt.com`), podem bloquear a exibição direta dentro de um iframe por limitações do próprio navegador. Nesses casos, o usuário pode carregar soluções de clientes de chat locais ou páginas de APIs que permitam renderização em frames.

## Proposed Changes

### Frontend Components

---

#### [MODIFY] [index.html](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/index.html)
- Adicionar o botão da aba "Chat GPT" (`tab-gpt-chat`) na barra de navegação lateral (após a aba de Instalação).
- Adicionar o painel correspondente `#tab-gpt-chat` contendo a barra superior para inserção de URL, o botão de carregamento, o iframe `#gpt-chat-iframe` e o painel de instruções/placeholder.
- Incrementar a versão de cache-busting dos arquivos de estáticos para `?v=4`.

---

#### [MODIFY] [style.css](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/style.css)
- Implementar regras de estilo para `#tab-gpt-chat` com `display: flex` quando ativa para garantir o correto redimensionamento do iframe.
- Estilizar o painel de cabeçalho (`.gpt-chat-header`) e o contêiner do iframe (`.gpt-chat-frame-container`) para se alinharem ao layout escuro e glassmorphic do GitIDE.

---

#### [MODIFY] [app.js](file:///c:/Users/augus/.workspace/gitide/gitide_server/static/app.js)
- Implementar listeners para o botão de carregamento de chat, salvando a URL em `localStorage` e inserindo-a no atributo `src` do iframe.
- Tratar a inicialização da aplicação: se houver uma URL anteriormente salva em `localStorage`, preencher o campo e carregar o chat automaticamente no iframe.
- Adicionar suporte a protocolo automático (garantindo que se o usuário digitar `chatgpt.com`, a URL seja convertida para `https://chatgpt.com`).

## Verification Plan

### Manual Verification
1. Abrir o dashboard do GitIDE no navegador.
2. Confirmar que a nova aba "Chat GPT" está disponível na barra lateral.
3. Clicar na aba, digitar uma URL (ex: `https://example.com` ou um cliente local/remoto de chat que permita iframes) e clicar em "Carregar Chat".
4. Validar se o chat carrega corretamente dentro do container e se preenche todo o espaço vertical.
5. Recarregar a página e confirmar se o chat continua carregado e a URL está salva.
