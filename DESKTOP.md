# Okestre Desktop para Windows

Aplicativo independente para projetos locais. Não substitui nem inicia uma segunda ponte MCP. O OkestreLocal.exe existente e a VM mantêm sua função; não há alteração no código do agente.

## Executar

Extraia a pasta inteira do ZIP e abra `OkestreDesktop.exe`. Mantenha `_internal` junto ao executável. O Python está incluído; Windows com Microsoft Edge WebView2 Runtime é necessário. Git e Node/npm devem estar instalados no computador e disponíveis no PATH para os respectivos comandos. Não há instalador, assinatura digital ou atualização automática neste pacote portátil.

## Projetos e arquivos

Clique em + para selecionar uma pasta. Pastas compartilhadas pelo agente aparecem automaticamente, mas projetos adicionados no Desktop não são compartilhados com a VM. Para compartilhar, use o agente existente.

O editor trabalha com textos UTF-8 até 1 MiB, lê o conteúdo completo, verifica o hash antes de salvar e guarda a versão anterior localmente. Arquivos binários, segredos comuns, metadados Git e caminhos fora do projeto são bloqueados no editor. As regras de `.gitideignore` são respeitadas. Novos arquivos exigem pasta pai existente.

O terminal usa a pasta do projeto como diretório inicial, com os privilégios e credenciais do usuário Windows; não é um sandbox. Use `npm.cmd ci`, `npm.cmd run build` ou `npm.cmd run dev`. Processos longos podem ser consultados e encerrados. A saída mostra os últimos 64 KB. Ao fechar o Desktop, seus processos são encerrados; isso não encerra o agente separado. Status e diff Git possuem painel próprio. Commit, branch, pull e push podem ser feitos pelo terminal.

## Diagramas

O botão Editor de diagramas abre uma janela própria com entidades, atributos, cardinalidades, importação e exportação Mermaid `.mmd`/SVG. O modelo inicial segue o exemplo de pedidos. Rascunhos ficam no perfil WebView do Desktop; exporte os arquivos para guardá-los no projeto.

## Pareamento e VM

Na aba Conexão, selecione o `OkestreLocal.exe` existente. Abrir agente / parear abre esse aplicativo, sem modificar sua configuração. Se já estiver rodando, abra a janela pelo ícone da bandeja. O painel da VM abre no navegador normal e mantém seu login próprio.

O status conectado/desconectado é consultado na VM pelo endpoint autenticado `GET /api/local/status`. É necessário publicar a versão do servidor que contém esse endpoint; versões anteriores mostram status indisponível, sem impedir o uso local. A credencial DPAPI do agente é somente lida para essa consulta; não é exposta à interface nem copiada para o cadastro do Desktop.

## Dados separados

- Desktop: `%LOCALAPPDATA%\OkestreDesktop` (cadastro, snapshots de edição, perfil WebView).
- Agente existente: `%LOCALAPPDATA%\OkestreLocal` (preservado).
- Arquivos dos projetos: suas pastas originais, sem cópia para a VM.

O Desktop funciona sem VM para arquivos, terminal, Git e diagramas. Recursos remotos e pacotes npm podem precisar de rede. Fechar o Desktop não desliga a ponte do agente.

## Desenvolvimento e pacote

Instale `requirements-desktop.txt` e PyInstaller no ambiente Python. Execute `python okestre-desktop.py`, ou compile com `scripts/build-desktop.ps1`. Para testes isolados, use `--home` e `--agent-home`. O parâmetro `--smoke-test arquivo.json` abre o renderer oculto, verifica a comunicação da interface e encerra.

Testes: `python -m pytest tests/test_desktop.py -q` e teste nativo do executável com perfis temporários. Documentação técnica do runtime: https://pywebview.flowrl.com/api/.
