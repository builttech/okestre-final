# Guia de Configuração de Túneis para o GitIDE

Se você encontrou o erro **403 Forbidden** no painel de debug do ChatGPT/GPT Action, isso ocorre porque o **TryCloudflare** (`*.trycloudflare.com`) possui proteção automática contra bots (Bot Fight Mode / Browser Integrity Check) ativada por padrão e não configurável. Como o ChatGPT funciona como um robô que faz chamadas à API, a Cloudflare bloqueia as requisições antes mesmo delas chegarem ao seu computador.

Aqui estão as alternativas recomendadas para expor o servidor local com sucesso:

---

## Opção 1: Usar Pinggy Pro (Recomendado - Seu Domínio Fixo!)

Como você assinou o Pinggy Pro, você tem um domínio fixo e não precisa mais alterar a URL na GPT Action!

1. Abra um terminal (PowerShell ou Prompt de Comando).
2. Conecte-se usando o seu Token:
   ```bash
   ssh -p 443 -R0:localhost:8000 6I8AbRjMwTr@a.pinggy.io
   ```
3. Digite `yes` para aceitar a chave se solicitado.
4. O Pinggy iniciará o túnel e usará automaticamente o seu domínio fixo:
   **`https://gitide.a.pinggy.link`**
5. Configure permanentemente o endereço `https://gitide.a.pinggy.link` no painel da sua GPT Action.

----

## Opção 2: Usar Localhost.run (Alternativa sem instalação)

O **Localhost.run** é outro serviço baseado em SSH que funciona sem instalação de cliente local e possui suporte para a porta 443 se a porta 22 estiver bloqueada.

1. Abra um terminal.
2. Execute o comando com a porta 443:
   ```bash
   ssh -p 443 -R 80:localhost:8000 ssh.localhost.run
   ```
   *(Caso a porta 22 esteja liberada, você também pode usar: `ssh -R 80:localhost:8000 localhost.run`)*
3. Digite `yes` para aceitar a chave.
4. Ele gerará uma URL `https://...lhrtunnel.link`. Copie e use essa URL no GPT Action.

---

## Opção 3: Usar Ngrok (Com cabeçalho de bypass)

O **Ngrok** é o serviço de túnel mais popular, porém sua conta gratuita exibe uma página de aviso de segurança ("You are about to access a local server...") na primeira requisição, o que faz a chamada da API do ChatGPT falhar.

Para contornar isso:
1. Inicie o Ngrok normalmente:
   ```bash
   ngrok http 8000
   ```
2. O servidor do GitIDE precisa responder a essa requisição pulando o aviso. Nós já suportamos o cabeçalho de bypass do Ngrok. Caso queira configurar a autenticação, certifique-se de configurar o **Bearer Token** na autenticação do GPT.

---

## Opção 4: Usar Cloudflare Tunnel com Domínio Próprio (Melhor para produção/uso frequente)

Se você possui um domínio próprio configurado na Cloudflare (ex: `meudominio.com`), você pode usar um túnel nomeado permanente e desativar o bloqueio de robôs para as requisições do ChatGPT.

1. Crie e configure o túnel associado ao seu domínio no painel do Cloudflare Zero Trust.
2. No painel da Cloudflare do seu domínio:
   - Vá em **Security** -> **WAF** -> **Create Rule**.
   - Crie uma regra para **Bypass** ou **Allow** quando:
     - `User-Agent` contém `ChatGPT-User` ou `ChatGPT`
     - Ou quando o IP de origem estiver na lista oficial de IPs da OpenAI.
   - Desative o **Bot Fight Mode** nas configurações de segurança do domínio.
3. Configure a URL do seu domínio personalizado (ex: `https://gitide.meudominio.com`) na GPT Action.
