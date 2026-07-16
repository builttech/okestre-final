import argparse
import json
import os
import shutil
import sys
import requests
import tempfile
import webbrowser
import zipfile
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen



CONFIG_DIR = Path.home() / ".gitide"
CONFIG_PATH = CONFIG_DIR / "sync.json"


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


def safe_extract(zip_path: Path, dest_dir: Path, clean: bool = False) -> int:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        for item in dest_dir.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    total = 0
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            if member.filename.startswith(".git/") or "/.git/" in member.filename:
                continue

            target_path = (dest_dir / member.filename).resolve()
            if not str(target_path).startswith(str(dest_dir)):
                raise RuntimeError(f"Tentativa de path traversal detectada no arquivo zip: {member.filename}")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target_path.open("wb") as target:
                shutil.copyfileobj(source, target)
            total += 1
    return total


def command_login(args: argparse.Namespace) -> int:
    config = load_config()
    config["server"] = normalize_server_url(args.server)
    if args.token:
        config["token"] = args.token
    save_config(config)
    print("Configuração salva com sucesso em", CONFIG_PATH)
    return 0


def command_projects(args: argparse.Namespace) -> int:
    config = load_config()
    server = normalize_server_url(args.server or config.get("server", ""))
    token = args.token or config.get("token")
    projects = list_projects(server, token)
    if not projects:
        print("Nenhum projeto encontrado.")
        return 0
    print(f"Encontrados {len(projects)} projeto(s):")
    for project in projects:
        print(f" - ID: {project.get('id'):<3} | {project.get('name')}")
    return 0


def command_pull(args: argparse.Namespace) -> int:
    config = load_config()
    server = normalize_server_url(args.server or config.get("server", ""))
    token = args.token or config.get("token")

    print(f"Conectando ao GitIDE em {server}...")
    project = find_project(server, token, args.project_id, args.project)
    print(f"Projeto selecionado: {project.get('name')} (ID {project.get('id')})")

    dest_dir = Path(args.to).expanduser().resolve()
    print(f"Destino local: {dest_dir}")
    if args.clean:
        print("Atenção: Limpeza da pasta de destino ativada (exceto .git).")

    with tempfile.TemporaryDirectory(prefix="gitide-sync-") as temp_dir:
        zip_path = Path(temp_dir) / "workspace.zip"
        print("Baixando arquivos...")
        filename = download_project_zip(server, token, int(project["id"]), zip_path)
        print(f"Pacote {filename} baixado ({zip_path.stat().st_size / 1024 / 1024:.2f} MB).")

        print("Extraindo...")
        total = safe_extract(zip_path, dest_dir, clean=args.clean)
        print(f"Concluído! {total} arquivos extraídos para {dest_dir}")

    return 0


SYNC_UI_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>GitIDE Local Sync</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0a0a0a; color: #fff; margin: 0; padding: 2rem; display: flex; justify-content: center; }
    main { background: #141414; border: 1px solid #262626; border-radius: 12px; width: 100%; max-width: 800px; overflow: hidden; box-shadow: 0 16px 40px -12px rgba(0,0,0,0.5); }
    header { padding: 1.5rem 2rem; border-bottom: 1px solid #262626; display: flex; justify-content: space-between; align-items: center; }
    header h2 { margin: 0; font-size: 1.25rem; font-weight: 600; }
    header p { margin: 0.25rem 0 0 0; color: #a1a1aa; font-size: 0.875rem; }
    .tabs { display: flex; gap: 0.5rem; background: #000; padding: 0.25rem; border-radius: 8px; border: 1px solid #262626; }
    .tabs button { background: transparent; color: #a1a1aa; border: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.875rem; cursor: pointer; transition: all 0.2s; }
    .tabs button.active { background: #262626; color: #fff; }
    .body { padding: 2rem; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
    label { display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.875rem; font-weight: 500; color: #e4e4e7; }
    input, select { background: #000; border: 1px solid #3f3f46; color: #fff; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.875rem; transition: border-color 0.2s; outline: none; }
    input:focus, select:focus { border-color: #00d084; }
    .row { display: flex; gap: 1rem; }
    button { background: #262626; color: #fff; border: 1px solid #3f3f46; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
    button:hover { background: #3f3f46; }
    button.primary { background: #fff; color: #000; border: none; font-weight: 600; }
    button.primary:hover { background: #e4e4e7; transform: translateY(-1px); }
    button.primary.push-mode { background: #00d084; color: #000; }
    button.primary.push-mode:hover { background: #00f0a3; }
    .actions { justify-content: flex-end; margin-top: 2rem; }
    .checkbox { flex-direction: row; align-items: center; cursor: pointer; }
    .checkbox input { width: auto; cursor: pointer; margin: 0; accent-color: #00d084; }
    pre { background: #000; padding: 1rem; border-radius: 8px; font-size: 0.75rem; color: #a1a1aa; overflow-x: auto; border: 1px solid #262626; margin-top: 2rem; white-space: pre-wrap; }
    .hidden { display: none !important; }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h2>GitIDE Local Sync</h2>
        <p id="desc">Sincronize projetos entre a VM GitIDE e esta maquina.</p>
      </div>
      <div class="tabs">
        <button id="tabPull" class="active">Puxar (VM -&#62; Local)</button>
        <button id="tabPush">Enviar (Local -&#62; VM)</button>
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
      <br>
      <div class="grid">
        <label>Projeto remoto
          <select id="project"><option value="">Carregue os projetos...</option></select>
        </label>
        <label>Pasta local
          <input id="destination" placeholder="C:\\Users\\augus\\.workspace\\meu-projeto">
        </label>
      </div>
      <label class="checkbox" id="cleanLabel"><input id="clean" type="checkbox"> Limpar pasta local antes de extrair</label>
      <div class="row actions">
        <button class="primary" id="actionBtn">Puxar para minha maquina</button>
      </div>
      <pre id="log">Pronto.</pre>
    </section>
  </main>
  <script>
    const $ = id => document.getElementById(id);
    const log = msg => $('log').textContent = msg;
    
    async function req(url, payload) {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok || data.status === 'error') {
        throw new Error(data.detail || `Erro HTTP ${res.status}`);
      }
      return data;
    }

    async function loadConfig() {
      const res = await fetch('/api/config');
      const data = await res.json();
      if (data.server) $('server').value = data.server;
      if (data.token) $('token').value = data.token;
      if (data.server) await loadProjects();
    }

    async function saveConfig() {
      try {
        await req('/api/config', { server: $('server').value, token: $('token').value });
        log("Configuracao salva com sucesso.");
      } catch (err) {
        log(`Erro ao salvar: ${err.message}`);
      }
    }

    async function loadProjects() {
      const btn = $('loadProjects');
      btn.disabled = true;
      btn.textContent = "Carregando...";
      try {
        const data = await req('/api/projects', { server: $('server').value, token: $('token').value });
        const select = $('project');
        select.innerHTML = '<option value="">Selecione...</option>';
        data.projects.forEach(p => {
          const opt = document.createElement('option');
          opt.value = p.id;
          opt.textContent = `${p.id}: ${p.name}`;
          select.appendChild(opt);
        });
        log(`${data.projects.length} projetos carregados.`);
      } catch (err) {
        log(`Falha ao carregar projetos: ${err.message}`);
      } finally {
        btn.disabled = false;
        btn.textContent = "Carregar projetos";
      }
    }

    let mode = 'pull';

    $('tabPull').addEventListener('click', () => {
      mode = 'pull';
      $('tabPull').classList.add('active');
      $('tabPush').classList.remove('active');
      $('cleanLabel').classList.remove('hidden');
      const btn = $('actionBtn');
      btn.textContent = "Puxar para minha maquina";
      btn.classList.remove('push-mode');
    });

    $('tabPush').addEventListener('click', () => {
      mode = 'push';
      $('tabPush').classList.add('active');
      $('tabPull').classList.remove('active');
      $('cleanLabel').classList.add('hidden');
      const btn = $('actionBtn');
      btn.textContent = "Enviar para a VM";
      btn.classList.add('push-mode');
    });

    async function doAction() {
      const btn = $('actionBtn');
      const payload = {
        server: $('server').value,
        token: $('token').value,
        project_id: $('project').value,
        to: $('destination').value,
        clean: $('clean').checked
      };
      if (!payload.project_id || !payload.to) {
        log("Selecione um projeto e informe a pasta local.");
        return;
      }
      btn.disabled = true;
      
      if (mode === 'pull') {
        btn.textContent = "Puxando...";
        try {
          const data = await req('/api/pull', payload);
          log(`Concluido (Pull).\\nProjeto: ${data.project_name} (ID ${data.project_id})\\nPacote: ${data.filename}\\nDestino: ${data.destination}\\nArquivos extraidos: ${data.files}`);
        } catch (err) {
          log(`Falha no pull: ${err.message}`);
        } finally {
          btn.disabled = false;
          btn.textContent = "Puxar para minha maquina";
        }
      } else {
        btn.textContent = "Enviando...";
        try {
          const data = await req('/api/push', payload);
          log(`Concluido (Push).\\nProjeto remoto atualizado.\\nOrigem: ${data.source}\\nArquivos enviados e extraidos: ${data.remote_extracted}`);
        } catch (err) {
          log(`Falha no push: ${err.message}`);
        } finally {
          btn.disabled = false;
          btn.textContent = "Enviar para a VM";
        }
      }
    }

    $('save').addEventListener('click', saveConfig);
    $('loadProjects').addEventListener('click', loadProjects);
    $('actionBtn').addEventListener('click', doAction);
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


def perform_push(server: str, token: str | None, project_id: int, source: str) -> dict:
    server = normalize_server_url(server)
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists() or not source_path.is_dir():
        raise RuntimeError("Pasta local de origem não encontrada.")

    with tempfile.NamedTemporaryFile(prefix="gitide-sync-", suffix=".zip", delete=False) as temp_zip:
        temp_zip_name = temp_zip.name
    
    total_files = 0
    with zipfile.ZipFile(temp_zip_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", ".venv")]
            for file in files:
                file_path = Path(root) / file
                archive.write(file_path, file_path.relative_to(source_path))
                total_files += 1

    url = urljoin(server, f"/api/projects/{project_id}/files/import.zip")
    headers = auth_headers(token)
    
    try:
        with open(temp_zip_name, "rb") as f:
            files_data = {"file": ("upload.zip", f, "application/zip")}
            response = requests.post(url, headers=headers, files=files_data, timeout=120)
        
        response.raise_for_status()
        res_data = response.json()
    except requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text
        raise RuntimeError(f"Erro HTTP {exc.response.status_code}: {detail}")
    except Exception as exc:
        raise RuntimeError(str(exc))
    finally:
        if os.path.exists(temp_zip_name):
            os.remove(temp_zip_name)

    return {
        "status": "success",
        "project_id": project_id,
        "source": str(source_path),
        "files_zipped": total_files,
        "remote_extracted": res_data.get("extracted", 0)
    }


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
                        payload.get("to") or ""
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
