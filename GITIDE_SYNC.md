# GitIDE Sync Agent

CLI local para puxar e enviar projetos entre uma VM GitIDE e a sua maquina.

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

Ela permite configurar servidor, token, selecionar o projeto remoto, informar a pasta local e executar o pull ou o envio para a VM.

## Puxar um projeto pelo nome

```powershell
.\gitide-sync.bat pull --project git-ide --to C:\Users\augus\.workspace\git-ide
```

## Puxar um projeto pelo ID

```powershell
.\gitide-sync.bat pull --project-id 1 --to C:\Users\augus\.workspace\git-ide
```

## Enviar um projeto pelo nome

```powershell
.\gitide-sync.bat push --project git-ide --from C:\Users\augus\.workspace\act\git-ide
```

## Enviar um projeto pelo ID

```powershell
.\gitide-sync.bat push --project-id 1 --from C:\Users\augus\.workspace\act\git-ide
```

## Simular envio antes de gravar

Use o dry run para validar o pacote e ver quantos arquivos seriam criados, sobrescritos ou bloqueados na VM sem gravar nada no projeto remoto.

```powershell
.\gitide-sync.bat push --project git-ide --from C:\Users\augus\.workspace\act\git-ide --dry-run
```

## Limpar a pasta local antes de extrair

Use somente quando quiser que a pasta local fique igual ao pacote exportado pela VM.

```powershell
.\gitide-sync.bat pull --project git-ide --to C:\Users\augus\.workspace\git-ide --clean
```

## Observacoes

- O modo Puxar usa o endpoint `/api/projects/{id}/files/export.zip`.
- O modo Enviar compacta a pasta local, roda um dry run primeiro e depois usa o endpoint `/api/projects/{id}/files/import.zip`.
- O envio real cria backup automatico dos arquivos sobrescritos em `.gitide/backups/`.
- Cada envio real gera um manifest de auditoria em `.gitide/imports/` com arquivos criados, sobrescritos, ignorados e bloqueados.
- A extracao e a importacao bloqueiam caminhos inseguros dentro do zip.
- O envio ignora `.git`, `node_modules`, `dist`, `build`, `.venv`, `.next`, caches e arquivos temporarios comuns.
- O envio bloqueia secrets por seguranca, incluindo `.env`, `.env.local`, `.npmrc`, `.pypirc`, `.netrc`, chaves privadas e arquivos `.pem`, `.key`, `.p12`, `.pfx`, `.ppk`, `.kdbx` e `.age`. Arquivos de exemplo como `.env.example` continuam permitidos.
- Arquivos ignorados pela arvore do GitIDE tambem nao entram no pacote exportado, como `.git`, `node_modules`, `dist`, `build`, `.venv` e arquivos `.zip`.
