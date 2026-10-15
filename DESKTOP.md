# Okestre Desktop para Windows

O executável abre a interface completa existente da Okestre, com seus 15 módulos e o mesmo layout: arquivos, documentos, UI, terminal, Git, Computer, banco, tokens, QA, métricas, estimativas, histórico, agente, Harness e Discovery. O editor de diagramas continua disponível com exportação Mermaid e SVG.

## Executar

Extraia a pasta inteira do ZIP e abra `OkestreDesktop.exe`. Mantenha `_internal` junto ao executável. Python e os recursos visuais estão incluídos. O Windows precisa do Microsoft Edge WebView2 Runtime. Git, Node/npm e outros executáveis usados pelos projetos devem estar instalados e disponíveis no PATH. Este pacote portátil não possui assinatura digital ou atualização automática.

## Projetos e operação

Use o cadastro e o seletor de projetos da interface original. As pastas já registradas no agente são importadas no primeiro carregamento do aplicativo. Projetos adicionados no Desktop não são automaticamente compartilhados com a VM: use o agente existente para isso.

Arquivos, documentos e Git usam as operações da aplicação original, executadas no computador. O terminal abre comandos na pasta do projeto, usando o usuário Windows e suas credenciais. A interface acompanha processos longos e permite encerrá-los, sem o limite de 30 segundos. A saída conserva os últimos 64 KB. Ao fechar o Desktop, os processos iniciados por esse terminal são encerrados.

Os módulos de IA, banco de dados e integrações continuam com seus formulários originais e exigem a configuração dos respectivos serviços. Credenciais e registros da VM não são migrados automaticamente. Conversão de áudio pode exigir FFmpeg. A presença das telas não significa que cada provedor externo esteja configurado ou validado.

## Agente e VM

A página de dispositivos abre o painel de conexão do Desktop: consulte o status, selecione e abra o `OkestreLocal.exe` existente ou acesse a VM. O agente continua separado, com seu mesmo pareamento e configuração. Se já estiver em execução, use seu ícone na bandeja.

O status usa o endpoint autenticado `GET /api/local/status` da VM. Uma versão antiga do servidor pode mostrar status indisponível. O token do agente é somente lido para essa consulta e não é enviado à interface.

## Dados

- Desktop: `%LOCALAPPDATA%\OkestreDesktop`; banco e configuração da aplicação completa em `server`, perfil do navegador em `webview`.
- Agente: `%LOCALAPPDATA%\OkestreLocal`, preservado.
- Projetos: suas pastas originais no computador.

O servidor embutido escuta somente em `127.0.0.1`, numa porta livre. A janela recebe uma sessão por endereço de uso único. O HOME do Windows não é substituído, preservando os locais das credenciais Git. Fechar o Desktop não encerra o agente separado. A VM continua responsável pela conexão com o ChatGPT.

## Desenvolvimento

Instale `requirements-desktop.txt` e PyInstaller. Execute `python okestre-desktop.py` ou compile com `scripts/build-desktop.ps1`. Para testes isolados, use `--home` e `--agent-home`. `--smoke-test arquivo.json` abre a janela oculta, verifica a interface completa e encerra.

Validação: `python -m pytest tests/test_desktop.py -q`, seguida do smoke test do executável empacotado. O build inclui HTML, JavaScript, fontes, templates e contratos do projeto; não inclui bancos, tokens ou arquivos de projetos do usuário.
