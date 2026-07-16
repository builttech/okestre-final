import argparse
import json
import os
import shutil
import sys
import tempfile
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen



CONFIG_DIR = Path.home() / ".gitide"
CONFIG_PATH = CONFIG_DIR / "sync.json"
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}
EXCLUDE_DIRS_LOWER = {item.lower() for item in EXCLUDE_DIRS}
EXCLUDE_FILES_LOWER = {item.lower() for item in EXCLUDE_FILES}
SECRET_ALLOWED_FILES = {".env.example", ".env.sample", ".env.template"}
SECRET_DIRS = {".gitide", ".secrets", "secrets"}
SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".env.staging",
    ".npmrc",
    ".pypirc",
    ".netrc",
    "authorized_keys",
    "known_hosts",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
}
SECRET_FILE_SUFFIXES = (".age", ".kdbx", ".key", ".p12", ".pem", ".pfx", ".ppk")


def normalize_server_url(server: str) -> str:
    server = (server or "").strip()
    if not server:
        raise ValueError("Informe a URL do servidor GitIDE.")
    if not server.startswith(("http://", "https://")):
        server = f"https://{server}"
    return server.rstrip("/") + "/"


def auth_headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def request_json(server: str, path: str, token: str | None) -> object:
    url = urljoin(server, path.lstrip("/"))
    request = Request(url, headers=auth_headers(token), method="GET")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def list_projects(server: str, token: str | None) -> list[dict]:
    data = request_json(server, "/api/projects", token)
    if not isinstance(data, list):
        raise RuntimeError("Resposta inesperada ao listar projetos.")
    return data


def find_project(server: str, token: str | None, project_id: int | None, project_name: str | None) -> dict:
    projects = list_projects(server, token)
    if project_id is not None:
        for project in projects:
            if int(project.get("id", -1)) == project_id:
                return project
        raise RuntimeError(f"Projeto com ID {project_id} não encontrado.")

    if project_name:
        normalized = project_name.strip().lower()
        matches = [project for project in projects if str(project.get("name", "")).strip().lower() == normalized]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            ids = ", ".join(str(project.get("id")) for project in matches)
            raise RuntimeError(f"Mais de um projeto chamado '{project_name}' encontrado. Use --project-id. IDs: {ids}")
        raise RuntimeError(f"Projeto '{project_name}' não encontrado.")

    raise RuntimeError("Informe --project-id ou --project.")


def download_project_zip(server: str, token: str | None, project_id: int, target_zip: Path) -> str:
    url = urljoin(server, f"/api/projects/{project_id}/files/export.zip")
    request = Request(url, headers=auth_headers(token), method="GET")
    with urlopen(request, timeout=120) as response:
        filename = "workspace.zip"
        disposition = response.headers.get("content-disposition", "")
        if "filename=" in disposition:
            filename = disposition.split("filename=", 1)[1].strip().strip('"')

        with target_zip.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                if chunk:
                    handle.write(chunk)
        return filename


def is_secret_path(path: Path) -> bool:
    name = path.name.lower()
    if name in SECRET_ALLOWED_FILES:
        return False
    parts = [part.lower() for part in path.parts]
    return (
        any(part in SECRET_DIRS for part in parts)
        or name in SECRET_FILE_NAMES
        or any(name.endswith(suffix) for suffix in SECRET_FILE_SUFFIXES)
    )


def should_skip_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    return (
        any(part in EXCLUDE_DIRS_LOWER for part in parts)
        or path.name.lower() in EXCLUDE_FILES_LOWER
        or is_secret_path(path)
    )


def create_project_zip(source: Path, target_zip: Path) -> int:
    source = source.expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise RuntimeError(f"Pasta local não encontrada: {source}")

    count = 0
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item in source.rglob("*"):
            rel_path = item.relative_to(source)
            if should_skip_path(rel_path) or should_skip_path(item):
                continue
            if item.is_file():
                archive.write(item, arcname=rel_path.as_posix())
                count += 1

    if count == 0:
        raise RuntimeError("Nenhum arquivo elegível encontrado para envio.")
    return count


def upload_project_zip(server: str, token: str | None, project_id: int, zip_path: Path, dry_run: bool = False) -> dict:
    boundary = f"----gitide-sync-{os.urandom(12).hex()}"
    file_bytes = zip_path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="workspace-upload.zip"\r\n'
        "Content-Type: application/zip\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = auth_headers(token)
    headers.update({
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    })
    endpoint = f"/api/projects/{project_id}/files/import.zip"
    if dry_run:
        endpoint += "?dry_run=true"
    request = Request(
        urljoin(server, endpoint),
        data=body,
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        data = response.read().decode("utf-8")
        return json.loads(data) if data else {"status": "success"}


def safe_extract(zip_path: Path, destination: Path, clean: bool = False) -> int:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    if clean:
        for item in destination.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    extracted = 0
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            member_name = member.filename.replace("\\", "/")
            if not member_name or member_name.endswith("/"):
                continue

            target = (destination / member_name).resolve()
            if not str(target).startswith(str(destination)):
                raise RuntimeError(f"Arquivo inseguro bloqueado no zip: {member.filename}")

            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted += 1
    return extracted


def command_login(args: argparse.Namespace) -> int:
    server = normalize_server_url(args.server)
    config = load_config()
    config["server"] = server
    if args.token:
        config["token"] = args.token
    save_config(config)
    print(f"GitIDE Sync configurado para {server}")
    return 0


def command_projects(args: argparse.Namespace) -> int:
    config = load_config()
    server = normalize_server_url(args.server or config.get("server", ""))
    token = args.token or config.get("token")
    projects = list_projects(server, token)
    if not projects:
        print("Nenhum projeto encontrado.")
        return 0

    for project in projects:
        print(f"{project.get('id')}\t{project.get('name')}\t{project.get('path')}")
    return 0


def command_pull(args: argparse.Namespace) -> int:
    config = load_config()
    server = normalize_server_url(args.server or config.get("server", ""))
    token = args.token or config.get("token")
    project = find_project(server, token, args.project_id, args.project)
    destination = Path(args.to).expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="gitide-sync-") as temp_dir:
        zip_path = Path(temp_dir) / "workspace.zip"
        filename = download_project_zip(server, token, int(project["id"]), zip_path)
        total = safe_extract(zip_path, destination, clean=args.clean)

    print(f"Projeto: {project.get('name')} (ID {project.get('id')})")
    print(f"Origem: {server}")
    print(f"Pacote: {filename}")
    print(f"Destino: {destination}")
    print(f"Arquivos sincronizados: {total}")
    return 0


def command_push(args: argparse.Namespace) -> int:
    config = load_config()
    server = normalize_server_url(args.server or config.get("server", ""))
    token = args.token or config.get("token")
    project = find_project(server, token, args.project_id, args.project)
    source = Path(args.source).expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="gitide-sync-push-") as temp_dir:
        zip_path = Path(temp_dir) / "workspace-upload.zip"
        local_files = create_project_zip(source, zip_path)
        zip_size = zip_path.stat().st_size
        dry_run_result = upload_project_zip(server, token, int(project["id"]), zip_path, dry_run=True)
        result = dry_run_result
        if not args.dry_run:
            result = upload_project_zip(server, token, int(project["id"]), zip_path, dry_run=False)

    print(f"Projeto: {project.get('name')} (ID {project.get('id')})")
    print(f"Destino: {server}")
    print(f"Origem local: {source}")
    print(f"Arquivos enviados: {local_files}")
    print(f"Tamanho do pacote: {zip_size} bytes")
    print(json.dumps({
        "dry_run_only": bool(args.dry_run),
        "dry_run": dry_run_result,
        "remote": result,
    }, indent=2, ensure_ascii=False))
    return 0


SYNC_UI_HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitIDE Local Sync</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #0b0b0c; color: #f4f4f5; display: grid; place-items: center; padding: 28px; }
    main { width: min(860px, 100%); border: 1px solid rgba(255,255,255,.1); border-radius: 22px; background: #111113; box-shadow: 0 28px 80px rgba(0,0,0,.45); overflow: hidden; }
    header { padding: 22px 24px; border-bottom: 1px solid rgba(255,255,255,.08); display: flex; justify-content: space-between; gap: 16px; align-items: center; }
    h1 { margin: 0; font-size: 18px; letter-spacing: -.03em; }
    header p { margin: 4px 0 0; color: #a1a1aa; font-size: 13px; }
    .body { padding: 22px 24px 24px; display: grid; gap: 16px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    label { display: grid; gap: 7px; color: #a1a1aa; font-size: 12px; font-weight: 650; }
    input, select { width: 100%; height: 42px; border: 1px solid rgba(255,255,255,.1); border-radius: 12px; background: #18181b; color: #fff; padding: 0 12px; font: inherit; outline: none; }
    input:focus, select:focus { border-color: #fb7185; box-shadow: 0 0 0 3px rgba(251,113,133,.14); }
    .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .actions { justify-content: flex-end; padding-top: 4px; }
    .tabs { display: inline-flex; gap: 4px; padding: 4px; border: 1px solid rgba(255,255,255,.1); border-radius: 12px; background: #080809; }
    .tabs button { height: 32px; border-radius: 8px; border-color: transparent; color: #a1a1aa; }
    .tabs button.active { background: #2a2a2f; color: #fff; border-color: rgba(255,255,255,.08); }
    button { height: 42px; border: 1px solid rgba(255,255,255,.1); border-radius: 12px; background: #1f1f23; color: #fff; padding: 0 14px; font: inherit; font-weight: 700; cursor: pointer; }
    button.primary { background: #fff; color: #111; border-color: #fff; }
    button:hover { border-color: rgba(255,255,255,.24); }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .checkbox { display: flex; align-items: center; gap: 9px; color: #d4d4d8; font-size: 13px; }
    .checkbox input { width: 16px; height: 16px; }
    pre { margin: 0; min-height: 128px; max-height: 260px; overflow: auto; border: 1px solid rgba(255,255,255,.08); border-radius: 14px; background: #080809; padding: 14px; color: #d4d4d8; font: 12px/1.55 "Fira Code", Consolas, monospace; white-space: pre-wrap; }
    .pill { color: #a1a1aa; border: 1px solid rgba(255,255,255,.1); border-radius: 999px; padding: 7px 10px; font-size: 12px; }
    @media (max-width: 720px) { body { padding: 14px; } .grid { grid-template-columns: 1fr; } header { align-items: flex-start; flex-direction: column; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>GitIDE Local Sync</h1>
        <p>Sincronize projetos entre a VM GitIDE e esta maquina.</p>
      </div>
      <div class="tabs" aria-label="Modo de sincronização">
        <button id="modePull" class="active" type="button">Puxar (VM -> Local)</button>
        <button id="modePush" type="button">Enviar (Local -> VM)</button>
      </div>
    </header>
    <section class="body">
      <div class="grid">
        <label>Servidor GitIDE
          <input id="server" placeholder="https://ide.builtt.com.br">
        </label>
        <label>Token
          <input id="token" placeholder="Bearer token opcional" type="password">
        </label>
      </div>
      <div class="row">
        <button id="save">Salvar config</button>
        <button id="loadProjects">Carregar projetos</button>
      </div>
      <div class="grid">
        <label>Projeto remoto
          <select id="project"><option value="">Carregue os projetos...</option></select>
        </label>
        <label id="pathLabel">Pasta local de destino
          <input id="destination" placeholder="C:\Users\augus\.workspace\meu-projeto">
        </label>
      </div>
      <label class="checkbox"><input id="clean" type="checkbox"> Limpar pasta local antes de extrair</label>
      <label class="checkbox" id="dryRunLabel" style="display:none"><input id="dryRun" type="checkbox"> Simular envio sem gravar na VM</label>
      <div class="row actions">
        <button class="primary" id="run">Puxar para minha maquina</button>
      </div>
      <pre id="log">Pronto.</pre>
    </section>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    let mode = 'pull';
    const log = (text) => { $('log').textContent = text; };
    async function api(path, options = {}) {
      const res = await fetch(path, { headers: { 'content-type': 'application/json' }, ...options });
      const data = await res.json();
      if (!res.ok || data.status === 'error') throw new Error(data.detail || 'Erro desconhecido.');
      return data;
    }
    async function loadConfig() {
      const data = await api('/api/config');
      $('server').value = data.server || '';
      $('token').value = data.token || '';
    }
    async function saveConfig() {
      await api('/api/config', { method: 'POST', body: JSON.stringify({ server: $('server').value, token: $('token').value }) });
      log('Configuracao salva.');
    }
    async function loadProjects() {
      log('Carregando projetos...');
      const data = await api('/api/projects', { method: 'POST', body: JSON.stringify({ server: $('server').value, token: $('token').value }) });
      $('project').innerHTML = '';
      for (const project of data.projects) {
        const option = document.createElement('option');
        option.value = project.id;
        option.textContent = `${project.name} - ID ${project.id}`;
        $('project').appendChild(option);
      }
      log(`${data.projects.length} projeto(s) carregado(s).`);
    }
    function setMode(nextMode) {
      mode = nextMode;
      $('modePull').classList.toggle('active', mode === 'pull');
      $('modePush').classList.toggle('active', mode === 'push');
      $('pathLabel').firstChild.textContent = mode === 'pull' ? 'Pasta local de destino' : 'Pasta local de origem';
      $('clean').closest('label').style.display = mode === 'pull' ? 'flex' : 'none';
      $('dryRunLabel').style.display = mode === 'push' ? 'flex' : 'none';
      $('run').textContent = mode === 'pull' ? 'Puxar para minha maquina' : 'Enviar para a VM';
      $('destination').placeholder = mode === 'pull' ? 'C:\\Users\\augus\\.workspace\\meu-projeto' : 'C:\\Users\\augus\\.workspace\\act\\git-ide';
      log(mode === 'pull' ? 'Modo pull selecionado.' : 'Modo push selecionado.');
    }
    async function runSync() {
      const payload = {
        server: $('server').value,
        token: $('token').value,
        project_id: Number($('project').value),
        to: $('destination').value,
        clean: $('clean').checked,
        dry_run: mode === 'push' ? $('dryRun').checked : false
      };
      if (!payload.project_id) return log('Selecione um projeto.');
      if (!payload.to) return log(mode === 'pull' ? 'Informe a pasta local de destino.' : 'Informe a pasta local de origem.');
      $('run').disabled = true;
      log(mode === 'pull' ? 'Baixando e extraindo projeto...' : 'Compactando e enviando projeto...');
      try {
        const data = await api(mode === 'pull' ? '/api/pull' : '/api/push', { method: 'POST', body: JSON.stringify(payload) });
        if (mode === 'pull') {
          log(`Concluido.\nProjeto: ${data.project_name} (ID ${data.project_id})\nPacote: ${data.filename}\nDestino: ${data.destination}\nArquivos sincronizados: ${data.files}`);
        } else {
          const dryRun = data.dry_run || {};
          const remote = data.remote || {};
          const finalResult = data.dry_run_only ? dryRun : remote;
          log(`Concluido.\nProjeto: ${data.project_name} (ID ${data.project_id})\nModo: ${data.dry_run_only ? 'dry run' : 'envio real'}\nOrigem: ${data.source}\nArquivos no pacote: ${data.local_files}\nTamanho do pacote: ${data.zip_size} bytes\nPlanejados na VM: ${dryRun.files_planned ?? 'n/a'}\nCriados na VM: ${finalResult.files_created ?? 0}\nSobrescritos na VM: ${finalResult.files_overwritten ?? 0}\nIgnorados/bloqueados: ${finalResult.files_skipped ?? dryRun.files_skipped ?? 0}\nBackup: ${finalResult.backup_path || 'n/a'}\nManifest: ${finalResult.manifest_path || 'n/a'}`);
        }
      } catch (err) {
        log(`Erro: ${err.message}`);
      } finally {
        $('run').disabled = false;
      }
    }
    $('save').addEventListener('click', saveConfig);
    $('loadProjects').addEventListener('click', loadProjects);
    $('modePull').addEventListener('click', () => setMode('pull'));
    $('modePush').addEventListener('click', () => setMode('push'));
    $('run').addEventListener('click', runSync);
    loadConfig().catch((err) => log(`Erro ao carregar config: ${err.message}`));
  </script>
</body>
</html>"""


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("content-length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("content-length") or "0")
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def perform_pull(server: str, token: str | None, project_id: int, destination: str, clean: bool) -> dict:
    server = normalize_server_url(server)
    projects = list_projects(server, token)
    project = next((item for item in projects if int(item.get("id", -1)) == int(project_id)), None)
    if not project:
        raise RuntimeError(f"Projeto com ID {project_id} não encontrado.")

    destination_path = Path(destination).expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="gitide-sync-") as temp_dir:
        zip_path = Path(temp_dir) / "workspace.zip"
        filename = download_project_zip(server, token, int(project["id"]), zip_path)
        total = safe_extract(zip_path, destination_path, clean=clean)

    return {
        "status": "success",
        "project_id": project.get("id"),
        "project_name": project.get("name"),
        "filename": filename,
        "destination": str(destination_path),
        "files": total,
    }


def perform_push(server: str, token: str | None, project_id: int, source: str, dry_run_only: bool = False) -> dict:
    server = normalize_server_url(server)
    projects = list_projects(server, token)
    project = next((item for item in projects if int(item.get("id", -1)) == int(project_id)), None)
    if not project:
        raise RuntimeError(f"Projeto com ID {project_id} não encontrado.")

    source_path = Path(source).expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="gitide-sync-push-") as temp_dir:
        zip_path = Path(temp_dir) / "workspace-upload.zip"
        local_files = create_project_zip(source_path, zip_path)
        zip_size = zip_path.stat().st_size
        dry_run_result = upload_project_zip(server, token, int(project["id"]), zip_path, dry_run=True)
        remote_result = dry_run_result
        if not dry_run_only:
            remote_result = upload_project_zip(server, token, int(project["id"]), zip_path, dry_run=False)

    return {
        "status": "success",
        "dry_run_only": bool(dry_run_only),
        "project_id": project.get("id"),
        "project_name": project.get("name"),
        "source": str(source_path),
        "local_files": local_files,
        "zip_size": zip_size,
        "dry_run": dry_run_result,
        "remote": remote_result,
    }


def make_ui_handler():
    class SyncUiHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/":
                body = SYNC_UI_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path == "/api/config":
                config = load_config()
                json_response(self, 200, {"status": "success", "server": config.get("server", ""), "token": config.get("token", "")})
                return

            json_response(self, 404, {"status": "error", "detail": "Rota não encontrada."})

        def do_POST(self) -> None:
            try:
                payload = read_json_body(self)
                if self.path == "/api/config":
                    config = load_config()
                    if payload.get("server"):
                        config["server"] = normalize_server_url(payload.get("server"))
                    else:
                        config.pop("server", None)
                    if payload.get("token"):
                        config["token"] = payload.get("token")
                    else:
                        config.pop("token", None)
                    save_config(config)
                    json_response(self, 200, {"status": "success"})
                    return

                if self.path == "/api/projects":
                    server = normalize_server_url(payload.get("server") or load_config().get("server", ""))
                    token = payload.get("token") or load_config().get("token")
                    projects = list_projects(server, token)
                    json_response(self, 200, {"status": "success", "projects": projects})
                    return

                if self.path == "/api/pull":
                    config = load_config()
                    result = perform_pull(
                        payload.get("server") or config.get("server", ""),
                        payload.get("token") or config.get("token"),
                        int(payload.get("project_id")),
                        payload.get("to") or "",
                        bool(payload.get("clean")),
                    )
                    json_response(self, 200, result)
                    return

                if self.path == "/api/push":
                    config = load_config()
                    result = perform_push(
                        payload.get("server") or config.get("server", ""),
                        payload.get("token") or config.get("token"),
                        int(payload.get("project_id")),
                        payload.get("to") or "",
                        dry_run_only=bool(payload.get("dry_run")),
                    )
                    json_response(self, 200, result)
                    return

                json_response(self, 404, {"status": "error", "detail": "Rota não encontrada."})
            except HTTPError as exc:
                try:
                    detail = json.loads(exc.read().decode("utf-8")).get("detail", "")
                except Exception:
                    detail = str(exc)
                json_response(self, 502, {"status": "error", "detail": f"GitIDE remoto respondeu HTTP {exc.code}: {detail}"})
            except Exception as exc:
                json_response(self, 500, {"status": "error", "detail": str(exc)})

    return SyncUiHandler


def command_ui(args: argparse.Namespace) -> int:
    host = args.host
    port = args.port
    server = ThreadingHTTPServer((host, port), make_ui_handler())
    url = f"http://{host}:{port}"
    print(f"GitIDE Sync UI rodando em {url}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando GitIDE Sync UI.")
    finally:
        server.server_close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitide-sync",
        description="Sincroniza projetos entre uma VM GitIDE e uma pasta local.",
    )
    parser.add_argument("--server", help="URL do GitIDE remoto. Ex: https://ide.builtt.com.br")
    parser.add_argument("--token", help="Token Bearer do GitIDE, quando exigido.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    login = subparsers.add_parser("login", help="Salva servidor e token padrão.")
    login.add_argument("server", help="URL do GitIDE remoto.")
    login.add_argument("--token", help="Token Bearer do GitIDE.")
    login.set_defaults(func=command_login)

    projects = subparsers.add_parser("projects", help="Lista projetos disponíveis na VM.")
    projects.set_defaults(func=command_projects)

    pull = subparsers.add_parser("pull", help="Baixa e extrai um projeto remoto para uma pasta local.")
    target = pull.add_mutually_exclusive_group(required=True)
    target.add_argument("--project-id", type=int, help="ID do projeto no GitIDE remoto.")
    target.add_argument("--project", help="Nome exato do projeto no GitIDE remoto.")
    pull.add_argument("--to", required=True, help="Pasta local de destino.")
    pull.add_argument("--clean", action="store_true", help="Limpa a pasta destino antes de extrair.")
    pull.set_defaults(func=command_pull)

    push = subparsers.add_parser("push", help="Compacta uma pasta local e envia para o projeto remoto.")
    push_target = push.add_mutually_exclusive_group(required=True)
    push_target.add_argument("--project-id", type=int, help="ID do projeto no GitIDE remoto.")
    push_target.add_argument("--project", help="Nome exato do projeto no GitIDE remoto.")
    push.add_argument("--from", dest="source", required=True, help="Pasta local de origem.")
    push.add_argument("--dry-run", action="store_true", help="Simula o envio na VM sem gravar arquivos.")
    push.set_defaults(func=command_push)

    ui = subparsers.add_parser("ui", help="Abre uma interface local para sincronizar projetos.")
    ui.add_argument("--host", default="127.0.0.1", help="Host local da interface.")
    ui.add_argument("--port", type=int, default=8765, help="Porta local da interface.")
    ui.add_argument("--no-open", dest="open", action="store_false", help="Não abrir o navegador automaticamente.")
    ui.set_defaults(func=command_ui, open=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except HTTPError as exc:
        try:
            import json

            detail = json.loads(exc.read().decode("utf-8")).get("detail", "")
        except Exception:
            detail = str(exc)
        print(f"Erro HTTP {exc.code}: {detail}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Erro de conexão: {exc.reason}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
