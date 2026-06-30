# GitIDE Sync Agent

CLI local para puxar projetos de uma VM GitIDE para a sua maquina.

## Configurar servidor padrao

```powershell
.\gitide-sync.bat login https://ide.builtt.com.br --token SEU_TOKEN
```

O arquivo de configuracao fica em:

```text
%USERPROFILE%\.gitide\sync.json
```

## Listar projetos remotos

```powershell
.\gitide-sync.bat projects
```

## Abrir interface local

```powershell
.\gitide-sync.bat ui
```

A interface abre em:

```text
http://127.0.0.1:8765
```

Ela permite configurar servidor, token, selecionar o projeto remoto, informar a pasta local e executar o pull.

## Puxar um projeto pelo nome

```powershell
.\gitide-sync.bat pull --project git-ide --to C:\Users\augus\.workspace\git-ide
```

## Puxar um projeto pelo ID

```powershell
.\gitide-sync.bat pull --project-id 1 --to C:\Users\augus\.workspace\git-ide
```

## Limpar a pasta local antes de extrair

Use somente quando quiser que a pasta local fique igual ao pacote exportado pela VM.

```powershell
.\gitide-sync.bat pull --project git-ide --to C:\Users\augus\.workspace\git-ide --clean
```

## Observacoes

- O sync atual e somente pull: VM para maquina local.
- O pacote usa o endpoint `/api/projects/{id}/files/export.zip`.
- A extracao bloqueia caminhos inseguros dentro do zip.
- Arquivos ignorados pela arvore do GitIDE tambem nao entram no pacote, como `.git`, `node_modules`, `dist`, `build`, `.venv` e arquivos `.zip`.
