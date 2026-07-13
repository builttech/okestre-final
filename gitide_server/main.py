import os
import re
import shutil
import json
import base64
import hashlib
import hmac
import io
import socket
import secrets
import subprocess
import sqlite3
import string
import tempfile
import unicodedata
import zipfile
from typing import Optional
from datetime import datetime, timedelta
from xml.sax.saxutils import escape as xml_escape

from fastapi import FastAPI, Request, Depends, HTTPException, Security, status, Query, Response, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from gitide_server.database import init_db, get_db, SessionLocal, Project, ActivityLog, FileSnapshot, PendingCommand, User
import gitide_server.vcs as vcs
import gitide_server.git_bridge as git_bridge
import gitide_server.agent as agent
from fastapi.responses import StreamingResponse
from typing import List

import requests
from gitide_server.documents import generate_docx, parse_docx_to_json

# Cria diretórios e inicializa o DB
init_db()

# Carrega ou gera a chave de API de segurança em ~/.gitide/config.json
CONFIG_DIR = os.path.expanduser("~/.gitide")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def load_or_create_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                if "api_key" in config:
                    return config
        except Exception:
            pass
            
    # Se não existir ou estiver corrompido, gera uma chave nova
    new_key = secrets.token_hex(24)
    config = {"api_key": new_key}
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    return config

def get_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return load_or_create_config()

def save_config(new_config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(new_config, f, indent=4)

config = load_or_create_config()
API_KEY = config["api_key"]
SESSION_SECRET = config.get("session_secret")
if not SESSION_SECRET:
    SESSION_SECRET = secrets.token_hex(32)
    config["session_secret"] = SESSION_SECRET
    save_config(config)
ROOT_EMAIL = os.getenv("GITIDE_ROOT_EMAIL", "contato@builtt.com.br").strip().lower()
ROOT_PASSWORD_ENV = os.getenv("GITIDE_ROOT_PASSWORD")
ROOT_CREDENTIALS_PATH = os.path.join(CONFIG_DIR, "root_credentials.txt")

app = FastAPI(
    title="Act IA software engineer API",
    description="Interface para GPT Actions interagirem livremente com código, comandos e bancos de dados locais.",
    version="1.0.0"
)

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Habilita compressao Gzip
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

security = HTTPBearer()

def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"pbkdf2_sha256${salt}${base64.b64encode(digest).decode('ascii')}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hash_password(password, salt).split("$", 2)[2]
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False

def sign_session(user_id: int) -> str:
    payload = str(user_id)
    signature = hmac.new(SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("ascii")

def read_session_user_id(token: Optional[str]) -> Optional[int]:
    if not token:
        return None
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        payload, signature = decoded.split(":", 1)
        expected = hmac.new(SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        return int(payload)
    except Exception:
        return None

def has_valid_bearer(request: Request) -> bool:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return False
    return hmac.compare_digest(auth.split(" ", 1)[1], API_KEY)

def get_current_user_from_request(request: Request) -> Optional[User]:
    user_id = read_session_user_id(request.cookies.get("gitide_session"))
    if not user_id:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return None
        db.expunge(user)
        return user
    finally:
        db.close()

def ensure_root_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ROOT_EMAIL).first()
        if existing:
            if ROOT_PASSWORD_ENV:
                existing.password_hash = hash_password(ROOT_PASSWORD_ENV)
                existing.is_active = True
                existing.role = "root"
                existing.updated_at = datetime.utcnow()
                db.commit()
                print(f"[Act IA Auth] Senha do usuário root atualizada via GITIDE_ROOT_PASSWORD: {ROOT_EMAIL}")
            return
        password = ROOT_PASSWORD_ENV or secrets.token_urlsafe(18)
        user = User(
            email=ROOT_EMAIL,
            password_hash=hash_password(password),
            role="root",
            is_active=True,
            must_change_password=False,
        )
        db.add(user)
        db.commit()
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(ROOT_CREDENTIALS_PATH, "w", encoding="utf-8") as f:
            f.write(
                "Act IA root user\n"
                "URL local: http://127.0.0.1:8000/login\n"
                f"Usuário: {ROOT_EMAIL}\n"
                f"Senha: {password if not ROOT_PASSWORD_ENV else '[definida via GITIDE_ROOT_PASSWORD]'}\n"
            )
        print(f"[Act IA Auth] Usuário root criado: {ROOT_EMAIL}")
        if ROOT_PASSWORD_ENV:
            print("[Act IA Auth] Senha inicial definida via GITIDE_ROOT_PASSWORD.")
        else:
            print(f"[Act IA Auth] Senha inicial salva em: {ROOT_CREDENTIALS_PATH}")
    finally:
        db.close()

ensure_root_user()

@app.middleware("http")
async def require_authenticated_session(request: Request, call_next):
    path = request.url.path
    public_paths = {"/login", "/api/auth/login", "/favicon.ico"}
    if request.method == "OPTIONS":
        return await call_next(request)
    if path in public_paths:
        return await call_next(request)
    if has_valid_bearer(request) or get_current_user_from_request(request):
        return await call_next(request)
    if path.startswith("/api/"):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED, content='{"detail":"Autenticação obrigatória."}', media_type="application/json")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Valida o token enviado pela GPT Action."""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de API Act IA inválido ou não fornecido."
        )
    return credentials.credentials

# Pydantic Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., description="Nome descritivo do projeto")
    path: str = Field(..., description="Caminho absoluto da pasta do projeto no computador")
    git_remote: Optional[str] = Field(None, description="URL do repositório Git remoto (GitHub/GitLab)")


class GitignoreUpdate(BaseModel):
    entries: List[str] = Field(default_factory=list, description="Regras ativas do .gitignore, uma por linha")


class LoginRequest(BaseModel):
    email: str = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")

class CommandExecute(BaseModel):
    command: str = Field(..., description="Comando do terminal a ser executado na pasta do projeto")

class DbQuery(BaseModel):
    db_type: str = Field("sqlite", description="Tipo de banco: sqlite, postgresql, mysql")
    connection_string: str = Field(..., description="Caminho do arquivo SQLite ou Connection String de Produção (Postgres/MySQL)")
    query: str = Field(..., description="Query SQL a ser executada")

class DbTableSchemaRequest(BaseModel):
    db_type: str = Field("sqlite", description="sqlite, postgresql, mysql")
    connection_string: str = Field(..., description="Arquivo SQLite ou connection string")

class DbTableRowsRequest(BaseModel):
    db_type: str
    connection_string: str
    limit: int = 50
    offset: int = 0

class DbUpdateRowRequest(BaseModel):
    db_type: str
    connection_string: str
    keys: dict
    values: dict

class DbInsertRowRequest(BaseModel):
    db_type: str
    connection_string: str
    values: dict

class DbDeleteRowRequest(BaseModel):
    db_type: str
    connection_string: str
    keys: dict

class FileWrite(BaseModel):
    filepath: str = Field(..., description="Caminho do arquivo relativo à pasta do projeto")
    content: str = Field(..., description="Conteúdo completo a ser escrito no arquivo")

class FilePatch(BaseModel):
    filepath: str = Field(..., description="Caminho do arquivo relativo à pasta do projeto")
    target_content: str = Field(..., description="Trecho de texto exato a ser substituído")
    replacement_content: str = Field(..., description="Conteúdo substituto")
    allow_multiple: bool = Field(False, description="Permitir múltiplas substituições caso o trecho ocorra mais de uma vez")

class GitDeployRequest(BaseModel):
    commit_message: str = Field(..., description="Mensagem de commit para descrever as alterações")
    branch: Optional[str] = Field(None, description="Branch Git de destino (caso omitido, usa a branch atual)")

class GitInitRequest(BaseModel):
    remote_url: Optional[str] = Field(None, description="URL do repositório remoto para configurar como origin")

class GitCommitMessageSuggestion(BaseModel):
    message: str = Field(..., description="Mensagem de commit sugerida")

class DeviceAuthRequest(BaseModel):
    client_id: Optional[str] = None

class PollRequest(BaseModel):
    device_code: str
    client_id: Optional[str] = None

class CreateBranchRequest(BaseModel):
    name: str

class GitMergeRequest(BaseModel):
    branch: str = Field(..., description="Nome da branch a ser mesclada na branch ativa")

class GitPushRequest(BaseModel):
    branch: Optional[str] = Field(None, description="Nome da branch para dar push (opcional)")

class GitSetTokenRequest(BaseModel):
    token: str = Field(..., description="Personal Access Token do GitHub")

class GitConflictResolveBlock(BaseModel):
    index: int = Field(..., description="Índice do bloco de conflito no arquivo")
    resolution: str = Field(..., description="Estratégia: ours, theirs ou manual")
    content: Optional[str] = Field(None, description="Conteúdo manual para substituir o bloco")

class GitConflictResolveRequest(BaseModel):
    filepath: str = Field(..., description="Caminho relativo do arquivo em conflito")
    resolutions: List[GitConflictResolveBlock] = Field(..., description="Resoluções por bloco")
    stage_file: bool = Field(True, description="Adicionar o arquivo ao index após resolver")

class GitPullRequestCreate(BaseModel):
    title: str = Field(..., description="Título do Pull Request")
    base: str = Field(..., description="Branch de destino (ex: main, master)")
    body: Optional[str] = Field(None, description="Descrição do Pull Request")

class AgentConfigInput(BaseModel):
    provider: str
    model: str
    api_key: str
    enabled_tools: List[str]
    ollama_base_url: Optional[str] = Field("http://127.0.0.1:11434", description="URL local do servidor Ollama")
    ollama_performance_mode: Optional[str] = Field("balanced", description="Modo do Ollama: fast, balanced ou deep")
    ollama_num_ctx: Optional[int] = Field(4096, description="Janela de contexto do Ollama")
    ollama_num_predict: Optional[int] = Field(768, description="Limite de tokens gerados pelo Ollama")

class AgentChatRequest(BaseModel):
    prompt: str
    history: Optional[List[dict]] = Field(default_factory=list, description="Histórico recente do chat do agente")

class AgentHistorySaveRequest(BaseModel):
    messages: List[dict] = Field(default_factory=list, description="Mensagens visíveis do chat")
    workflow: List[dict] = Field(default_factory=list, description="Eventos recentes do workflow do agente")

class DocumentSection(BaseModel):
    heading: Optional[str] = Field("", description="Título da seção")
    text: str = Field(..., description="Conteúdo de texto da seção")
    type: str = Field("paragraph", description="Tipo de formatação (paragraph, bullet, highlight, code, table)")

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., description="Título principal do documento")
    sections: List[DocumentSection] = Field(..., description="Lista de seções ordenadas do documento")

class BusinessDocumentGenerateRequest(BaseModel):
    kind: str = Field("all", description="Documento a gerar: charter, specify, design, dri, tasks ou all")

class CreateDirectoryRequest(BaseModel):
    parent_path: str = Field(..., description="Caminho do diretório pai")
    name: str = Field(..., description="Nome da nova pasta a ser criada")

# SDD Models
class SddSpecSaveRequest(BaseModel):
    filename: str = Field(..., description="Nome do arquivo da especificação (ex: auth.md)")
    content: str = Field(..., description="Conteúdo em Markdown da especificação")
    overwrite: bool = Field(True, description="Permite sobrescrever arquivo existente")

class SddSpecGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt descrevendo a feature a ser especificada")
    title: Optional[str] = Field(None, description="Título opcional para a especificação")
    kind: str = Field("req", description="Tipo de documento a gerar: 'req' ou 'rf'")
    parent_id: Optional[str] = Field(None, description="ID do REQ pai, caso kind='rf'")

class SddCharterSaveRequest(BaseModel):
    content: str = Field(..., description="Conteúdo em Markdown do Project Charter/TAP")

class SddCharterGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Contexto do projeto para gerar o TAP")
    title: Optional[str] = Field(None, description="Nome opcional do projeto")

class SddCriteriaItem(BaseModel):
    line_no: int = Field(..., description="Número da linha (1-indexed) do critério no Markdown")
    checked: bool = Field(..., description="Estado de verificação do critério")

class SddCriteriaUpdateRequest(BaseModel):
    criteria: List[SddCriteriaItem] = Field(..., description="Lista de critérios a serem atualizados")

class SddTaskBulkDeleteRequest(BaseModel):
    line_nos: List[int] = Field(..., min_length=1, description="Linhas (1-indexed) das tasks a excluir")

class SddTestGenerateRequest(BaseModel):
    filename: str = Field(..., description="Nome do arquivo de especificação (.md)")
    framework: str = Field(..., description="Framework de teste (ex: pytest, jest, phpunit, mocha)")

class OpsInfraPlanRequest(BaseModel):
    environment: str = Field("prod", description="Ambiente alvo: dev, homolog ou prod")
    domain: Optional[str] = Field(None, description="Domínio desejado para a aplicação")
    database: Optional[str] = Field(None, description="Banco desejado: postgres, mysql, redis ou nenhum")

class OpsInfraArtifactRequest(BaseModel):
    environment: str = Field("prod", description="Ambiente alvo")
    domain: Optional[str] = None
    database: Optional[str] = None
    overwrite: bool = Field(False, description="Sobrescrever arquivos existentes")

class OpsInfraCommandRequest(BaseModel):
    action: str = Field(..., description="Ação: build, up, down, restart, logs ou ps")

class OpsInfraHealthRequest(BaseModel):
    url: Optional[str] = Field(None, description="URL para health check. Se vazio, usa o domínio informado ou host/porta.")
    domain: Optional[str] = Field(None, description="Domínio esperado")

class OpsInfraDnsRequest(BaseModel):
    domain: str = Field(..., description="Domínio a validar")

class OpsInfraVmDirectoryRequest(BaseModel):
    path: str = Field("/", description="Diretório remoto a listar ou criar")

class OpsInfraVmAccessRequest(BaseModel):
    host: str = Field("", description="IP ou host da VM")
    user: str = Field("", description="Usuário SSH")
    port: int = Field(22, description="Porta SSH")
    app_path: str = Field("", description="Diretório do app na VM")
    auth_method: str = Field("key", description="Método de autenticação: agent, key ou password")
    private_key: str = Field("", description="Chave privada SSH")
    password: str = Field("", description="Senha SSH")

class OpsInfraDomainRequest(BaseModel):
    domain: str = Field(..., description="Domínio que apontará para a aplicação")
    environment: str = Field("prod", description="Ambiente alvo")
    overwrite: bool = Field(True, description="Sobrescrever Caddyfile existente")

class OpsInfraEnvItem(BaseModel):
    key: str
    value: str = ""
    secret: bool = False

class OpsInfraEnvRequest(BaseModel):
    environment: str = Field("prod", description="Ambiente alvo")
    variables: List[OpsInfraEnvItem] = Field(default_factory=list)
    write_env_file: bool = Field(True, description="Gerar arquivo .env.<ambiente>")

class QaAnnotationInput(BaseModel):
    title: str = Field(..., description="Resumo curto da anotação")
    description: str = Field("", description="Descrição, evidência ou observação do QA")
    url: str = Field("", description="URL onde a anotação foi criada")
    category: str = Field("functional", description="functional, interface, content, interaction, design, structure ou visual")
    severity: str = Field("medium", description="low, medium, high ou critical")
    status: str = Field("open", description="open, reviewing ou resolved")
    selector: str = Field("", description="Seletor CSS aproximado do elemento anotado")
    viewport: dict = Field(default_factory=dict)
    browser: str = Field("", description="User agent do navegador")
    screenshot: Optional[str] = Field(None, description="Data URL da captura, quando enviada")
    metadata: dict = Field(default_factory=dict)

class QaTextPolishRequest(BaseModel):
    mode: str = Field("description", description="description ou title")
    text: str = Field(..., description="Texto original a ser reescrito")
    context: Optional[str] = Field("", description="Contexto opcional da anotação")

class QaAnnotationStatusUpdate(BaseModel):
    status: str = Field(..., description="open, reviewing ou resolved")

# Dependência para buscar projeto do DB
def get_project_or_404(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Projeto com ID {project_id} não encontrado.")
    return project

# --- ENDPOINTS DA API PARA O GPT / DASHBOARD ---

@app.get("/login", response_class=HTMLResponse, tags=["Autenticação"])
def get_login_page(request: Request):
    """Tela de autenticação do Act IA."""
    if get_current_user_from_request(request):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse(
        content=f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Act IA Login</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ min-height: 100vh; margin: 0; display: grid; place-items: center; background: #0b0b0c; color: #f8fafc; }}
    main {{ width: min(420px, calc(100vw - 32px)); padding: 28px; border: 1px solid rgba(255,255,255,.12); border-radius: 22px; background: #151517; box-shadow: 0 24px 70px rgba(0,0,0,.36); }}
    span {{ color: #9ca3af; font-size: 12px; }}
    h1 {{ margin: 4px 0 6px; font-size: 24px; }}
    p {{ margin: 0 0 22px; color: #a1a1aa; font-size: 13px; line-height: 1.45; }}
    label {{ display: block; margin: 14px 0 7px; color: #cbd5e1; font-size: 12px; font-weight: 700; }}
    input {{ width: 100%; min-height: 44px; padding: 0 13px; border: 1px solid rgba(255,255,255,.12); border-radius: 12px; background: #0f0f10; color: #f8fafc; outline: none; }}
    input:focus {{ border-color: rgba(255,107,138,.62); box-shadow: 0 0 0 3px rgba(255,107,138,.12); }}
    button {{ width: 100%; min-height: 46px; margin-top: 20px; border: 0; border-radius: 999px; background: #fff; color: #111827; font-weight: 800; cursor: pointer; }}
    #login-error {{ min-height: 18px; margin-top: 12px; color: #fb7185; font-size: 12px; }}
    .hint {{ margin-top: 18px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,.10); color: #71717a; font-size: 11px; }}
  </style>
</head>
<body>
  <main>
    <span>Act IA software engineer</span>
    <h1>Acessar ferramenta</h1>
    <p>Informe o usuário root da instalação para acessar o ambiente.</p>
    <form id="login-form">
      <label for="email">Usuário</label>
      <input id="email" name="email" type="email" value="{ROOT_EMAIL}" autocomplete="username" required>
      <label for="password">Senha</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
      <button type="submit">Entrar</button>
      <div id="login-error"></div>
    </form>
    <div class="hint">Cadastro e redefinição pública de senha estão desativados.</div>
  </main>
  <script>
    document.getElementById('login-form').addEventListener('submit', async (event) => {{
      event.preventDefault();
      const error = document.getElementById('login-error');
      error.textContent = '';
      const response = await fetch('/api/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          email: document.getElementById('email').value,
          password: document.getElementById('password').value
        }})
      }});
      const data = await response.json().catch(() => ({{}}));
      if (!response.ok || data.status !== 'success') {{
        error.textContent = data.detail || 'Usuário ou senha inválidos.';
        return;
      }}
      window.location.href = '/';
    }});
  </script>
</body>
</html>""",
        status_code=200,
    )

@app.post("/api/auth/login", tags=["Autenticação"])
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Autentica usuário local e cria cookie de sessão sem expiração por tempo."""
    user = db.query(User).filter(User.email == req.email.strip().lower(), User.is_active == True).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")
    user.last_login_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    db.commit()
    response.set_cookie(
        "gitide_session",
        sign_session(user.id),
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return {"status": "success", "user": {"email": user.email, "role": user.role}}

@app.post("/api/auth/logout", tags=["Autenticação"])
def logout(response: Response):
    response.delete_cookie("gitide_session", path="/")
    return {"status": "success"}

@app.get("/api/auth/me", tags=["Autenticação"])
def auth_me(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida.")
    return {"email": user.email, "role": user.role}

# Config
@app.get("/api/info", tags=["Configuração"])
def get_server_info():
    """Retorna informações públicas do servidor."""
    import platform
    return {
        "status": "online",
        "api_key_path": CONFIG_PATH,
        "database_path": os.path.join(CONFIG_DIR, "gitide.db"),
        # Retornamos a chave apenas para o localhost Dashboard
        "api_key": API_KEY,
        "os": platform.system()
    }

@app.get("/api/prod-readiness-validator", tags=["Configuração"])
def get_prod_readiness_validator():
    """Retorna o System Prompt do auditor Production-Ready."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    prompt_path = os.path.join(repo_root, "PROD_READINESS_VALIDATOR.md")
    if not os.path.exists(prompt_path):
        raise HTTPException(status_code=404, detail="PROD_READINESS_VALIDATOR.md não encontrado.")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/markdown; charset=utf-8")


@app.get("/api/security-rules", tags=["Configuração"])
def get_security_rules():
    """Retorna o System Prompt do auditor AppSec/Security Review."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    prompt_path = os.path.join(repo_root, "SECURITY_RULES.md")
    if not os.path.exists(prompt_path):
        raise HTTPException(status_code=404, detail="SECURITY_RULES.md não encontrado.")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/markdown; charset=utf-8")


@app.get("/api/ops-infra-operator", tags=["Configuração"])
def get_ops_infra_operator():
    """Retorna o System Prompt do operador Ops Infra."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    prompt_path = os.path.join(repo_root, "OPS_INFRA_OPERATOR.md")
    if not os.path.exists(prompt_path):
        raise HTTPException(status_code=404, detail="OPS_INFRA_OPERATOR.md não encontrado.")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/markdown; charset=utf-8")


def sync_project_system_files(project_path: str) -> list[str]:
    """Garante os prompts de sistema necessários na raiz do workspace do projeto."""
    server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = [
        ("GPT_INSTRUCTIONS.md", True),
        ("PROD_READINESS_VALIDATOR.md", True),
        ("SECURITY_RULES.md", True),
        ("OPS_INFRA_OPERATOR.md", True),
    ]
    synced = []
    if not os.path.isdir(project_path):
        return synced

    for rel_dir in (
        os.path.join(".documents", "prod-readiness"),
        os.path.join(".documents", "security"),
        os.path.join(".documents", "ops-infra"),
        os.path.join(".documents", "agent"),
        os.path.join(".documents", "design"),
        os.path.join(".documents", "dri"),
        os.path.join(".documents", "requirements"),
        os.path.join(".documents", "functional-requirements"),
        os.path.join(".documents", "spec"),
        os.path.join(".documents", "task"),
    ):
        try:
            os.makedirs(os.path.join(project_path, rel_dir), exist_ok=True)
        except Exception as e:
            print(f"Erro ao criar diretório {rel_dir} no workspace: {str(e)}")

    try:
        task_dir = os.path.join(project_path, ".documents", "task")
        task_md = os.path.join(task_dir, "task.md")
        task_details_md = os.path.join(task_dir, "task.details.md")
        
        design_dir = os.path.join(project_path, ".documents", "design")
        design_md = os.path.join(design_dir, "design.md")
        
        dri_dir = os.path.join(project_path, ".documents", "dri")
        dri_md = os.path.join(dri_dir, "dri.md")
        
        req_dir = os.path.join(project_path, ".documents", "requirements")
        req_md = os.path.join(req_dir, "REQ-01-template.md")
        
        func_req_dir = os.path.join(project_path, ".documents", "functional-requirements")
        rf_md = os.path.join(func_req_dir, "RF-01-01-template.md")
        
        if not os.path.exists(func_req_dir):
            os.makedirs(func_req_dir, exist_ok=True)
            
        import shutil
        templates_dir = os.path.join(server_root, "gitide_server", "templates")
        project_charter_md = os.path.join(project_path, ".documents", "project-charter.md")
        
        estimativa_path = os.path.join(project_path, ".documents", "estimativa.md")
        if not os.path.exists(estimativa_path):
            with builtins.open(estimativa_path, "w", encoding="utf-8") as f:
                f.write(
                    "# Estimativa Global do Projeto\n\n"
                    "Acesse **Estimativas** no menu principal e selecione **Gerar estimativa** "
                    "para analisar REQs, RFs, Task List e Task Details."
                )

        template_map = {
            "REQ-01-template.md": req_md,
            "RF-01-01-template.md": rf_md,
            "task.md": task_md,
            "task.details.md": task_details_md,
            "design.md": design_md,
            "dri.md": dri_md,
            "project-charter.md": project_charter_md
        }
        
        for tpl_name, target_path in template_map.items():
            tpl_path = os.path.join(templates_dir, tpl_name)
            if os.path.exists(tpl_path):
                # Se for arquivo de template (termina com template.md), sempre sobrescreve para manter a parametrização atualizada.
                # Se for arquivo de trabalho (design.md, task.md), só cria se não existir para não apagar o trabalho da IA.
                if "template.md" in tpl_name:
                    shutil.copy2(tpl_path, target_path)
                elif not os.path.exists(target_path):
                    shutil.copy2(tpl_path, target_path)
                
    except Exception as e:
        print(f"Erro ao criar arquivos de template: {str(e)}")

    for filename, overwrite in files:
        src = os.path.join(server_root, filename)
        dest = os.path.join(project_path, filename)
        if not os.path.exists(src):
            continue
        if os.path.abspath(src) == os.path.abspath(dest):
            continue
        if os.path.exists(dest) and not overwrite:
            continue
        try:
            shutil.copy2(src, dest)
            synced.append(filename)
        except Exception as e:
            print(f"Erro ao sincronizar {filename} para o workspace: {str(e)}")
    return synced


# Projetos
@app.get("/api/projects", tags=["Projetos"])
def list_projects(db: Session = Depends(get_db)):
    """Lista todos os projetos cadastrados."""
    projects = db.query(Project).all()
    for project in projects:
        sync_project_system_files(project.path)
    return projects

@app.post("/api/projects", tags=["Projetos"])
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    """Cadastra um novo projeto (workspace) e clona do Git se um remoto for especificado."""
    # Normaliza caminhos
    project_in.path = os.path.abspath(project_in.path)
    
    # Se a pasta não existir, cria
    os.makedirs(project_in.path, exist_ok=True)

    # Verifica se já está cadastrado com o mesmo caminho
    existing = db.query(Project).filter(Project.path == project_in.path).first()
    if existing:
        sync_project_system_files(existing.path)
        project_data = {
            "id": existing.id,
            "name": existing.name,
            "path": existing.path,
            "git_remote": existing.git_remote,
            "created_at": existing.created_at.isoformat() if existing.created_at else None
        }
        return {"status": "success", "message": "Projeto já cadastrado", "project": project_data}
        
    # Verifica se o nome já está em uso por outro caminho
    existing_name = db.query(Project).filter(Project.name == project_in.name).first()
    if existing_name:
        raise HTTPException(
            status_code=400,
            detail=f"Já existe um projeto cadastrado com o nome '{project_in.name}' no caminho '{existing_name.path}'."
        )
        
    clone_status = None
    # Se foi fornecido um remoto Git, realiza a clonagem ou vinculação
    if project_in.git_remote:
        # Se a pasta estiver vazia (ou tiver apenas arquivos ocultos), clona
        is_empty = True
        try:
            if any(not f.startswith('.') for f in os.listdir(project_in.path)):
                is_empty = False
        except Exception:
            pass

        if is_empty:
            try:
                git_bridge.clone_git(project_in.git_remote, project_in.path)
                clone_status = "cloned"
            except Exception as e:
                # Se falhar a clonagem, remove a pasta criada (se vazia)
                try:
                    if os.path.exists(project_in.path) and not os.listdir(project_in.path):
                        os.rmdir(project_in.path)
                except Exception:
                    pass
                raise HTTPException(
                    status_code=400,
                    detail=f"Falha ao clonar repositório Git: {str(e)}"
                )
        else:
            # Se não estiver vazia, apenas tenta inicializar e vincular o remoto
            try:
                git_bridge.init_git(project_in.path, project_in.git_remote)
                clone_status = "linked"
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Pasta de destino não está vazia e falhou ao vincular repositório Git: {str(e)}"
                )
                
    # Garante os prompts de sistema na raiz do projeto.
    sync_project_system_files(project_in.path)

    db_project = Project(
        name=project_in.name,
        path=project_in.path,
        git_remote=project_in.git_remote
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Registra no log
    details = f"Projeto '{db_project.name}' cadastrado no caminho '{db_project.path}'"
    if clone_status:
        details += f" (Git status: {clone_status})"
        
    log = ActivityLog(
        project_id=db_project.id,
        action_type="PROJECT_CREATED",
        details=details
    )
    db.add(log)
    db.commit()
    
    project_data = {
        "id": db_project.id,
        "name": db_project.name,
        "path": db_project.path,
        "git_remote": db_project.git_remote,
        "created_at": db_project.created_at.isoformat() if db_project.created_at else None
    }
    
    return {"status": "success", "project": project_data, "git_clone_status": clone_status}

@app.delete("/api/projects/{project_id}", tags=["Projetos"])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Remove o cadastro do projeto do Act IA (não apaga os arquivos do computador)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    db.delete(project)
    db.commit()
    return {"status": "success", "message": "Projeto descadastrado com sucesso"}

# Arquivos (Protegidos por API Key para chamadas da GPT Action)
@app.get("/api/projects/{project_id}/files", tags=["Arquivos"])
def list_files(project: Project = Depends(get_project_or_404)):
    """Lista recursivamente os arquivos do projeto, ignorando pastas de build/dependências."""
    try:
        sync_project_system_files(project.path)
        files = vcs.list_project_files(project.path)
        return {"status": "success", "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/files/export.zip", tags=["Arquivos"])
def export_project_zip(project: Project = Depends(get_project_or_404)):
    """Exporta os arquivos navegáveis do projeto ativo em um arquivo .zip."""
    try:
        files = vcs.list_project_files(project.path)
        safe_project_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", project.name or "workspace").strip("-") or "workspace"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_filename = f"{safe_project_name}-{timestamp}.zip"
        temp_file = tempfile.NamedTemporaryFile(prefix="gitide-export-", suffix=".zip", delete=False)
        temp_file.close()

        with zipfile.ZipFile(temp_file.name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                rel_path = item.get("path")
                if not rel_path:
                    continue
                full_path = vcs.get_safe_path(project.path, rel_path)
                if os.path.isfile(full_path):
                    archive.write(full_path, arcname=rel_path)

        return FileResponse(
            temp_file.name,
            media_type="application/zip",
            filename=zip_filename,
            background=BackgroundTask(lambda path: os.path.exists(path) and os.remove(path), temp_file.name)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/files/read", tags=["Arquivos"])
def read_file(filepath: str = Query(..., description="Caminho relativo do arquivo"), 
              start_line: Optional[int] = Query(None, description="Linha inicial (1-indexed) para leitura parcial"),
              end_line: Optional[int] = Query(None, description="Linha final (1-indexed) para leitura parcial"),
              project: Project = Depends(get_project_or_404)):
    """
    Lê o conteúdo de um arquivo do projeto.
    Suporta paginação por intervalo de linhas para evitar erros de limite de resposta.
    """
    try:
        if filepath in {"GPT_INSTRUCTIONS.md", "PROD_READINESS_VALIDATOR.md", "SECURITY_RULES.md", "OPS_INFRA_OPERATOR.md"}:
            sync_project_system_files(project.path)
        content = vcs.read_project_file(project.path, filepath)
        lines = content.split('\n')
        total_lines = len(lines)
        
        # A interface precisa carregar o arquivo completo, então o limite deve ser alto
        MAX_READ_LINES = 100000
        
        warning = None
        s_line = start_line or 1
        
        # Determina o e_line com base no limite
        if start_line is None and end_line is None:
            e_line = min(MAX_READ_LINES, total_lines)
            if total_lines > MAX_READ_LINES:
                warning = f"O arquivo possui {total_lines} linhas. Para evitar erros de limite de tamanho de resposta do ChatGPT, foram retornadas apenas as primeiras {MAX_READ_LINES} linhas. Use os parâmetros start_line e end_line para paginar e ler trechos específicos."
        elif end_line is None:
            e_line = min(s_line + MAX_READ_LINES - 1, total_lines)
            if e_line < total_lines:
                warning = f"Leitura limitada a {MAX_READ_LINES} linhas a partir da linha {s_line}. O arquivo possui {total_lines} linhas no total. Use paginação solicitando lotes adicionais (ex: start_line={e_line + 1})."
        else:
            requested_lines = end_line - s_line + 1
            if requested_lines > MAX_READ_LINES:
                e_line = s_line + MAX_READ_LINES - 1
                warning = f"A faixa solicitada ({requested_lines} linhas) excede o limite recomendado. Retornando apenas {MAX_READ_LINES} linhas a partir da linha {s_line}. Use paginação (ex: start_line={e_line + 1}) para ler o restante do arquivo."
            else:
                e_line = min(end_line, total_lines)
                
        # Garante limites válidos
        s_line = max(1, min(s_line, total_lines))
        e_line = max(s_line, min(e_line, total_lines))
        
        # Obtém a fatia das linhas (1-indexed)
        sliced_lines = lines[s_line - 1 : e_line]
        sliced_content = '\n'.join(sliced_lines)
        
        response = {
            "status": "success",
            "filepath": filepath,
            "total_lines": total_lines,
            "start_line": s_line,
            "end_line": e_line,
            "content": sliced_content
        }
        if warning:
            response["warning"] = warning
            
        return response
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filepath}")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/files/write", tags=["Arquivos"])
def write_file(file_in: FileWrite, 
               project: Project = Depends(get_project_or_404),
               db: Session = Depends(get_db),
               _ = Depends(get_api_key)):
    """
    Grava ou edita o conteúdo de um arquivo. 
    Gera automaticamente um snapshot local para rollback.
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        # Cria log da ação antes
        log = ActivityLog(
            project_id=project.id,
            action_type="FILE_WRITE",
            details=f"Escrita/Edição no arquivo: {file_in.filepath}"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        result = vcs.write_project_file(db, project, file_in.filepath, file_in.content, activity_log_id=log.id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/projects/{project_id}/files/patch", tags=["Arquivos"])
def patch_file(file_patch: FilePatch, 
               project: Project = Depends(get_project_or_404),
               db: Session = Depends(get_db),
               _ = Depends(get_api_key)):
    """
    Substitui um trecho específico de um arquivo (atualização parcial)
    sem a necessidade de enviar o arquivo completo.
    Gera automaticamente um snapshot local.
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        log = ActivityLog(
            project_id=project.id,
            action_type="FILE_PATCH",
            details=f"Atualização parcial (patch) no arquivo: {file_patch.filepath}"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        result = vcs.patch_project_file(
            db=db,
            project=project,
            filepath=file_patch.filepath,
            target_content=file_patch.target_content,
            replacement_content=file_patch.replacement_content,
            allow_multiple=file_patch.allow_multiple,
            activity_log_id=log.id
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}/files/delete", tags=["Arquivos"])
def delete_file(filepath: str = Query(..., description="Caminho relativo do arquivo"), 
                project: Project = Depends(get_project_or_404),
                db: Session = Depends(get_db),
                _ = Depends(get_api_key)):
    """
    Exclui um arquivo ou pasta do workspace. Arquivos recebem snapshot de backup antes da exclusão.
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        log = ActivityLog(
            project_id=project.id,
            action_type="FILE_DELETE",
            details=f"Exclusão de arquivo/pasta: {filepath}"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        result = vcs.delete_project_file(db, project, filepath, activity_log_id=log.id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo ou pasta não encontrado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Execução de Comandos
@app.post("/api/projects/{project_id}/execute", tags=["Execução"])
def execute_command(cmd_in: CommandExecute, 
                    request: Request,
                    project: Project = Depends(get_project_or_404),
                    db: Session = Depends(get_db),
                    _ = Depends(get_api_key)):
    """
    Executa um comando de terminal (Shell) dentro da pasta do projeto.
    Requer autenticação Bearer Token para chamadas externas.
    Se a requisição for externa, exige aprovação prévia do usuário via Dashboard.
    """
    is_dashboard = request.headers.get("x-gitide-source") == "dashboard" or request.headers.get("x-gitide-source") == "dashboard"
    
    if not is_dashboard:
        cmd_str = cmd_in.command.strip()
        
        # Verifica se o comando já foi aprovado
        pending = db.query(PendingCommand).filter(
            PendingCommand.project_id == project.id,
            PendingCommand.command == cmd_str,
            PendingCommand.status == "approved"
        ).first()
        
        if pending:
            # Consome a aprovação
            pending.status = "executed"
            db.commit()
        else:
            # Verifica se já existe um pendente idêntico para evitar duplicados
            existing = db.query(PendingCommand).filter(
                PendingCommand.project_id == project.id,
                PendingCommand.command == cmd_str,
                PendingCommand.status == "pending"
            ).first()
            
            if not existing:
                new_cmd = PendingCommand(
                    project_id=project.id,
                    command=cmd_str,
                    status="pending"
                )
                db.add(new_cmd)
                db.commit()
                db.refresh(new_cmd)
                cmd_id = new_cmd.id
            else:
                cmd_id = existing.id
                
            return {
                "status": "pending_approval",
                "command_id": cmd_id,
                "message": (
                    f"A execução do comando '{cmd_str}' foi retida por motivos de segurança e requer aprovação manual. "
                    "Por favor, peça ao usuário para aprovar a execução deste comando no painel Web do Act IA. "
                    "Assim que o usuário aprovar, ele te avisará no chat para que você execute o comando novamente."
                )
            }

    # Registra a execução no log
    log = ActivityLog(
        project_id=project.id,
        action_type="SHELL_EXEC",
        details=f"Executando comando: {cmd_in.command}"
    )
    db.add(log)
    db.commit()
    
    try:
        # Roda o comando com um limite de 30 segundos
        result = subprocess.run(
            cmd_in.command,
            cwd=project.path,
            shell=True,
            text=True,
            capture_output=True,
            timeout=30
        )
        
        # Salva o resultado no log para consulta posterior
        log.details += f"\n[Exit Code: {result.returncode}]\nStdout: {result.stdout[:500]}...\nStderr: {result.stderr[:500]}..."
        db.commit()
        
        # Rastreia e gera snapshots de qualquer alteração de arquivos decorrente do comando
        changes = vcs.detect_and_snapshot_workspace_changes(db, project, activity_log_id=log.id)
        if changes:
            log.details += "\n[Arquivos alterados: " + ", ".join([f"{c['filepath']} ({c['type']})" for c in changes]) + "]"
            db.commit()
        
        return {
            "status": "success",
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        log.details += "\n[TIMEOUT (30s)]"
        db.commit()
        return {
            "status": "error",
            "detail": "O comando excedeu o tempo limite de 30 segundos."
        }
    except Exception as e:
        log.details += f"\n[ERRO: {str(e)}]"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Erro ao executar comando: {str(e)}")

@app.get("/api/projects/{project_id}/execute/pending", tags=["Execução"])
def list_pending_commands(project: Project = Depends(get_project_or_404),
                          db: Session = Depends(get_db),
                          _ = Depends(get_api_key)):
    """Lista todos os comandos pendentes de aprovação para o projeto."""
    commands = db.query(PendingCommand).filter(
        PendingCommand.project_id == project.id,
        PendingCommand.status == "pending"
    ).all()
    return [{"id": c.id, "command": c.command, "status": c.status, "created_at": c.created_at.isoformat()} for c in commands]

@app.post("/api/projects/{project_id}/execute/pending/{command_id}/approve", tags=["Execução"])
def approve_pending_command(command_id: int,
                            project: Project = Depends(get_project_or_404),
                            db: Session = Depends(get_db),
                            _ = Depends(get_api_key)):
    """Aprova um comando pendente de execução."""
    cmd = db.query(PendingCommand).filter(
        PendingCommand.id == command_id,
        PendingCommand.project_id == project.id
    ).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Comando pendente não encontrado.")
    
    cmd.status = "approved"
    db.commit()
    return {"status": "success", "message": "Comando aprovado com sucesso."}

@app.post("/api/projects/{project_id}/execute/pending/{command_id}/reject", tags=["Execução"])
def reject_pending_command(command_id: int,
                           project: Project = Depends(get_project_or_404),
                           db: Session = Depends(get_db),
                           _ = Depends(get_api_key)):
    """Rejeita um comando pendente de execução."""
    cmd = db.query(PendingCommand).filter(
        PendingCommand.id == command_id,
        PendingCommand.project_id == project.id
    ).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Comando pendente não encontrado.")
    
    cmd.status = "rejected"
    db.commit()
    return {"status": "success", "message": "Comando rejeitado com sucesso."}
# Banco de Dados do Projeto
@app.post("/api/projects/{project_id}/db/query", tags=["Banco de Dados"])
def execute_db_query(db_in: DbQuery, 
                      project: Project = Depends(get_project_or_404),
                      db: Session = Depends(get_db),
                      _ = Depends(get_api_key)):
    """
    Executa uma query SQL em um banco de dados local (SQLite) ou de produção (Postgres/MySQL).
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        from sqlalchemy import create_engine, text

        # 1. Determina a URL de conexão do SQLAlchemy
        db_url = db_in.connection_string
        if db_in.db_type == "sqlite":
            if not db_url.startswith("sqlite:///"):
                db_path = vcs.get_safe_path(project.path, db_url)
                db_url = f"sqlite:///{db_path}"
        elif db_in.db_type == "mysql":
            if db_url.startswith("mysql://"):
                db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
            elif db_url.startswith("mariadb://"):
                db_url = db_url.replace("mariadb://", "mysql+pymysql://", 1)
            elif db_url.startswith("mariadb+pymysql://"):
                db_url = db_url.replace("mariadb+pymysql://", "mysql+pymysql://", 1)
        elif db_in.db_type == "postgresql":
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)

        # Registra no log do Act IA
        log = ActivityLog(
            project_id=project.id,
            action_type="DB_QUERY",
            details=f"SQL executado no banco {db_in.db_type} ({db_in.connection_string[:40]}...): {db_in.query}"
        )
        db.add(log)
        db.commit()
        
        # 2. Executa a query usando SQLAlchemy
        temp_engine = create_engine(db_url, echo=False)
        rows = []
        affected = 0
        
        with temp_engine.connect() as conn:
            result = conn.execute(text(db_in.query))
            
            if result.returns_rows:
                rows = [dict(row._mapping) for row in result.all()]
            
            affected = result.rowcount
            conn.commit()
            
        temp_engine.dispose()
        
        return {
            "status": "success",
            "rows_count": len(rows),
            "rows": rows,
            "rows_affected": affected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na execução da query SQL: {str(e)}")

def get_db_url(db_type: str, connection_string: str, project_path: str) -> str:
    db_url = connection_string
    if db_type == "sqlite":
        if not db_url.startswith("sqlite:///"):
            db_path = vcs.get_safe_path(project_path, db_url)
            db_url = f"sqlite:///{db_path}"
    elif db_type == "mysql":
        if db_url.startswith("mysql://"):
            db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
        elif db_url.startswith("mariadb://"):
            db_url = db_url.replace("mariadb://", "mysql+pymysql://", 1)
        elif db_url.startswith("mariadb+pymysql://"):
            db_url = db_url.replace("mariadb+pymysql://", "mysql+pymysql://", 1)
    elif db_type == "postgresql":
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url

def get_quoted_identifier(name: str, db_type: str) -> str:
    if db_type == "mysql":
        return f"`{name}`"
    return f'"{name}"'

@app.post("/api/projects/{project_id}/db/tables/{table_name}/schema", tags=["Banco de Dados"])
def get_table_schema(table_name: str,
                     req: DbTableSchemaRequest,
                     project: Project = Depends(get_project_or_404),
                     db: Session = Depends(get_db),
                     _ = Depends(get_api_key)):
    """Retorna o esquema de uma tabela (colunas, tipos, chaves primárias)."""
    try:
        from sqlalchemy import create_engine, inspect
        db_url = get_db_url(req.db_type, req.connection_string, project.path)
        temp_engine = create_engine(db_url, echo=False)
        
        inspector = inspect(temp_engine)
        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_cols = pk_constraint.get("constrained_columns", []) or []
        
        cols_info = []
        for col in columns:
            cols_info.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "primary_key": col["name"] in pk_cols
            })
            
        temp_engine.dispose()
        return {
            "status": "success",
            "columns": cols_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao obter esquema da tabela: {str(e)}")

@app.post("/api/projects/{project_id}/db/tables/{table_name}/rows", tags=["Banco de Dados"])
def get_table_rows(table_name: str,
                   req: DbTableRowsRequest,
                   project: Project = Depends(get_project_or_404),
                   db: Session = Depends(get_db),
                   _ = Depends(get_api_key)):
    """Busca os registros de uma tabela de forma paginada e retorna o total geral."""
    try:
        from sqlalchemy import create_engine, text
        db_url = get_db_url(req.db_type, req.connection_string, project.path)
        temp_engine = create_engine(db_url, echo=False)
        
        total_count = 0
        rows = []
        
        table_quoted = get_quoted_identifier(table_name, req.db_type)
        
        with temp_engine.connect() as conn:
            count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table_quoted}"))
            total_count = count_res.scalar()
            
            select_query = f"SELECT * FROM {table_quoted} LIMIT :limit OFFSET :offset"
            result = conn.execute(text(select_query), {"limit": req.limit, "offset": req.offset})
            
            if result.returns_rows:
                rows = [dict(row._mapping) for row in result.all()]
                
        temp_engine.dispose()
        return {
            "status": "success",
            "total_count": total_count,
            "rows": rows
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao buscar linhas da tabela: {str(e)}")

@app.post("/api/projects/{project_id}/db/tables/{table_name}/update-row", tags=["Banco de Dados"])
def update_table_row(table_name: str,
                     req: DbUpdateRowRequest,
                     project: Project = Depends(get_project_or_404),
                     db: Session = Depends(get_db),
                     _ = Depends(get_api_key)):
    """Atualiza uma linha do banco de dados de maneira segura e parametrizada."""
    try:
        from sqlalchemy import create_engine, text
        db_url = get_db_url(req.db_type, req.connection_string, project.path)
        temp_engine = create_engine(db_url, echo=False)
        
        set_clauses = []
        params = {}
        
        for i, (col, val) in enumerate(req.values.items()):
            param_name = f"val_{i}"
            quoted_col = get_quoted_identifier(col, req.db_type)
            set_clauses.append(f"{quoted_col} = :{param_name}")
            params[param_name] = val
            
        where_clauses = []
        for i, (col, val) in enumerate(req.keys.items()):
            param_name = f"key_{i}"
            quoted_col = get_quoted_identifier(col, req.db_type)
            if val is None:
                where_clauses.append(f"{quoted_col} IS NULL")
            else:
                where_clauses.append(f"{quoted_col} = :{param_name}")
                params[param_name] = val
                
        if not set_clauses:
            raise HTTPException(status_code=400, detail="Nenhum valor fornecido para atualização.")
        if not where_clauses:
            raise HTTPException(status_code=400, detail="Nenhuma chave fornecida para identificar a linha.")
            
        table_quoted = get_quoted_identifier(table_name, req.db_type)
        query_str = f"UPDATE {table_quoted} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        
        with temp_engine.connect() as conn:
            result = conn.execute(text(query_str), params)
            conn.commit()
            rows_affected = result.rowcount
            
        temp_engine.dispose()
        
        log = ActivityLog(
            project_id=project.id,
            action_type="DB_UPDATE",
            details=f"UPDATE na tabela {table_name}: alterou {list(req.values.keys())} onde {req.keys}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "rows_affected": rows_affected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar linha: {str(e)}")

@app.post("/api/projects/{project_id}/db/tables/{table_name}/insert-row", tags=["Banco de Dados"])
def insert_table_row(table_name: str,
                     req: DbInsertRowRequest,
                     project: Project = Depends(get_project_or_404),
                     db: Session = Depends(get_db),
                     _ = Depends(get_api_key)):
    """Insere um novo registro de forma segura e parametrizada."""
    try:
        from sqlalchemy import create_engine, text
        db_url = get_db_url(req.db_type, req.connection_string, project.path)
        temp_engine = create_engine(db_url, echo=False)
        
        cols = []
        placeholders = []
        params = {}
        
        for i, (col, val) in enumerate(req.values.items()):
            param_name = f"val_{i}"
            cols.append(get_quoted_identifier(col, req.db_type))
            placeholders.append(f":{param_name}")
            params[param_name] = val
            
        if not cols:
            raise HTTPException(status_code=400, detail="Nenhum valor fornecido para inserção.")
            
        table_quoted = get_quoted_identifier(table_name, req.db_type)
        query_str = f"INSERT INTO {table_quoted} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        
        with temp_engine.connect() as conn:
            result = conn.execute(text(query_str), params)
            conn.commit()
            rows_affected = result.rowcount
            
        temp_engine.dispose()
        
        log = ActivityLog(
            project_id=project.id,
            action_type="DB_INSERT",
            details=f"INSERT na tabela {table_name}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "rows_affected": rows_affected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao inserir linha: {str(e)}")

@app.post("/api/projects/{project_id}/db/tables/{table_name}/delete-row", tags=["Banco de Dados"])
def delete_table_row(table_name: str,
                     req: DbDeleteRowRequest,
                     project: Project = Depends(get_project_or_404),
                     db: Session = Depends(get_db),
                     _ = Depends(get_api_key)):
    """Remove um registro da tabela de forma segura e parametrizada."""
    try:
        from sqlalchemy import create_engine, text
        db_url = get_db_url(req.db_type, req.connection_string, project.path)
        temp_engine = create_engine(db_url, echo=False)
        
        where_clauses = []
        params = {}
        
        for i, (col, val) in enumerate(req.keys.items()):
            param_name = f"key_{i}"
            quoted_col = get_quoted_identifier(col, req.db_type)
            if val is None:
                where_clauses.append(f"{quoted_col} IS NULL")
            else:
                where_clauses.append(f"{quoted_col} = :{param_name}")
                params[param_name] = val
                
        if not where_clauses:
            raise HTTPException(status_code=400, detail="Nenhuma chave fornecida para identificar a linha.")
            
        table_quoted = get_quoted_identifier(table_name, req.db_type)
        query_str = f"DELETE FROM {table_quoted} WHERE {' AND '.join(where_clauses)}"
        
        with temp_engine.connect() as conn:
            result = conn.execute(text(query_str), params)
            conn.commit()
            rows_affected = result.rowcount
            
        temp_engine.dispose()
        
        log = ActivityLog(
            project_id=project.id,
            action_type="DB_DELETE",
            details=f"DELETE na tabela {table_name}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "rows_affected": rows_affected
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao deletar linha: {str(e)}")

# Ponte Git
@app.get("/api/projects/{project_id}/git/status", tags=["Git Bridge"])
def git_status(project: Project = Depends(get_project_or_404)):
    """Retorna o status atual do Git no projeto."""
    return git_bridge.get_git_status(project.path)

@app.get("/api/projects/{project_id}/git/graph", tags=["Git Bridge"])
def git_graph(project: Project = Depends(get_project_or_404)):
    """Retorna o gráfico de commits (git log --graph) do projeto."""
    return git_bridge.get_git_graph(project.path)


def _normalize_gitignore_entry(entry: str) -> str:
    value = (entry or "").strip().replace("\\", "/")
    value = value.lstrip("/")
    return value


@app.get("/api/projects/{project_id}/git/gitignore", tags=["Git Bridge"])
def get_gitignore(project: Project = Depends(get_project_or_404)):
    """Retorna as regras atuais do .gitignore do projeto."""
    path = vcs.get_safe_path(project.path, ".gitignore")
    if not os.path.exists(path):
        return {"status": "success", "exists": False, "entries": [], "comments": [], "content": ""}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = []
    comments = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            comments.append(stripped)
            continue
        entries.append(stripped)

    return {
        "status": "success",
        "exists": True,
        "entries": entries,
        "comments": comments,
        "content": content,
    }


@app.put("/api/projects/{project_id}/git/gitignore", tags=["Git Bridge"])
def update_gitignore(payload: GitignoreUpdate,
                     project: Project = Depends(get_project_or_404),
                     db: Session = Depends(get_db)):
    """Atualiza o .gitignore do projeto com regras informadas pela interface."""
    normalized_entries = []
    seen = set()
    for item in payload.entries:
        entry = _normalize_gitignore_entry(item)
        if not entry or entry.startswith("#"):
            continue
        if "\n" in entry or "\r" in entry:
            raise HTTPException(status_code=400, detail="Cada regra deve ocupar apenas uma linha.")
        if entry not in seen:
            normalized_entries.append(entry)
            seen.add(entry)

    content = "# Gerenciado pelo Act IA - arquivos ignorados pelo Git\n"
    if normalized_entries:
        content += "\n".join(normalized_entries) + "\n"
    else:
        content += "\n"

    result = vcs.write_project_file(db, project, ".gitignore", content)
    return {
        "status": "success",
        "entries": normalized_entries,
        "filepath": result.get("filepath", ".gitignore"),
        "content": content,
    }


@app.post("/api/projects/{project_id}/git/commit-message/suggest", tags=["Git Bridge"])
def git_suggest_commit_message(project: Project = Depends(get_project_or_404),
                               _ = Depends(get_api_key)):
    """Gera uma mensagem de commit no padrão Conventional Commits usando IA."""
    context = git_bridge.get_commit_context(project.path)
    if not context.get("has_changes"):
        raise HTTPException(status_code=400, detail="Não há alterações para gerar uma mensagem de commit.")

    def fallback_message() -> str:
        files = context.get("staged", []) + context.get("modified", []) + context.get("untracked", [])
        filenames = " ".join(files)
        lowered = filenames.lower()
        basenames = [os.path.splitext(os.path.basename(file))[0].replace("_", " ").replace("-", " ") for file in files[:3]]
        subject = " e ".join(name for name in basenames if name).strip()

        if "gpt_instructions" in lowered:
            return "docs: orientar fluxo de requisitos do GPT Action"
        if "sdd" in lowered or "spec" in lowered or "harness" in lowered:
            return "feat: aprimorar fluxo de especificacoes"
        if any(token in lowered for token in ["commit", "git_bridge", "git bridge"]):
            return "feat: melhorar sugestao de commit"
        if any(token in lowered for token in ["css", "style", "ui", "html", "component", "modal"]):
            return f"feat: ajustar {subject[:40].strip()}" if subject else "feat: ajustar interface"
        if any(token in lowered for token in ["test", "spec"]):
            return "test: atualizar testes"
        if any(token in lowered for token in ["fix", "bug"]):
            return "fix: corrigir comportamento do sistema"
        return f"chore: atualizar {subject[:42].strip()}" if subject else "chore: atualizar projeto"

    conf = agent.load_agent_config()
    provider = conf.get("provider")
    model = conf.get("model")
    api_key = conf.get("api_key")

    if not provider or not model or not api_key:
        return {"status": "fallback", "message": fallback_message()}

    system_prompt = (
        "Voce gera mensagens de commit no padrao Conventional Commits.\n"
        "Responda EXCLUSIVAMENTE em JSON valido no formato {\"message\":\"tipo: descricao curta\"}.\n"
        "Regras:\n"
        "- Use um destes tipos: feat, fix, refactor, chore, docs, style, test, perf.\n"
        "- A mensagem deve ter no maximo 72 caracteres.\n"
        "- Use portugues simples, sem ponto final.\n"
        "- Nao inclua markdown, aspas extras, escopo, corpo ou explicacao.\n"
        "- A descricao DEVE citar a mudanca concreta inferida pelos arquivos/diff.\n"
        "- Evite frases genericas como 'ajustar interface do usuario', 'atualizar projeto' ou 'melhorar sistema'.\n"
        "- Se houver mudancas em GPT_INSTRUCTIONS.md, prefira tipo docs.\n"
        "- Se houver mudancas em endpoints ou JS de commit, mencione commit ou Git.\n"
    )
    user_prompt = (
        "Gere uma unica mensagem de commit para estas alteracoes:\n\n"
        f"Branch: {context.get('branch')}\n"
        f"Arquivos staged: {context.get('staged')}\n"
        f"Arquivos modificados: {context.get('modified')}\n"
        f"Arquivos deletados: {context.get('deleted')}\n"
        f"Arquivos novos: {context.get('untracked')}\n"
        f"Name status:\n{context.get('name_status')}\n\n"
        f"Diff stat:\n{context.get('diff_stat')}\n\n"
        f"Diff resumido:\n{context.get('diff')}"
    )

    try:
        raw_resp = agent.call_llm(provider, model, api_key, [{"role": "user", "content": user_prompt}], system_prompt)
        parsed = agent.extract_json(raw_resp)
        message = (parsed.get("message") or "").strip()
        if not re.match(r"^(feat|fix|refactor|chore|docs|style|test|perf): .+", message):
            message = fallback_message()
        return {"status": "success", "message": message[:120]}
    except Exception as e:
        return {"status": "fallback", "message": fallback_message(), "detail": str(e)}

@app.post("/api/projects/{project_id}/git/init", tags=["Git Bridge"])
def git_init(req: Optional[GitInitRequest] = None,
             project: Project = Depends(get_project_or_404),
             db: Session = Depends(get_db),
             _ = Depends(get_api_key)):
    """Inicializa um repositório Git local e opcionalmente configura/persiste o origin remoto."""
    try:
        remote_url = (req.remote_url.strip() if req and req.remote_url else "") or project.git_remote
        result = git_bridge.init_git(project.path, remote_url)
        if remote_url and project.git_remote != remote_url:
            project.git_remote = remote_url
            db.add(project)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_INIT",
            details=f"Git inicializado/configurado com remoto: {remote_url or '-'}"
        )
        db.add(log)
        db.commit()
        db.refresh(project)

        result["remote_url"] = project.git_remote or remote_url or ""
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/pull", tags=["Git Bridge"])
def git_pull(branch: Optional[str] = Query(None), 
             project: Project = Depends(get_project_or_404),
             db: Session = Depends(get_db),
             _ = Depends(get_api_key)):
    """Executa o git pull no repositório remoto."""
    try:
        result = git_bridge.pull_git(project.path, branch)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_PULL",
            details=f"Git pull executado na branch {branch or 'atual'}"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        conflicts = git_bridge.list_conflicts(project.path)
        if conflicts.get("files"):
            raise HTTPException(status_code=409, detail={
                "message": str(e),
                "has_conflicts": True,
                "conflicts": conflicts.get("files", [])
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/deploy", tags=["Git Bridge"])
def git_deploy(deploy_in: GitDeployRequest, 
               project: Project = Depends(get_project_or_404),
               db: Session = Depends(get_db),
               _ = Depends(get_api_key)):
    """
    Executa o deploy do projeto (Git commit + Git push) na branch remota.
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        result = git_bridge.deploy_git(project.path, deploy_in.commit_message, deploy_in.branch)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_DEPLOY",
            details=f"Deploy executado. Commit: '{deploy_in.commit_message}' na branch: '{deploy_in.branch or 'atual'}'"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao realizar deploy via Git: {str(e)}")

@app.get("/api/projects/{project_id}/git/branches", tags=["Git Bridge"])
def git_list_branches(fetch: bool = Query(False, description="Forçar git fetch antes de listar"),
                      project: Project = Depends(get_project_or_404)):
    """Lista as branches locais e remotas do repositório Git."""
    try:
        return git_bridge.list_branches(project.path, force_fetch=fetch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/branches", tags=["Git Bridge"])
def git_create_branch(req: CreateBranchRequest, 
                      project: Project = Depends(get_project_or_404),
                      db: Session = Depends(get_db),
                      _ = Depends(get_api_key)):
    """Cria uma nova branch e realiza o checkout."""
    try:
        result = git_bridge.create_branch(project.path, req.name)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_BRANCH_CREATE",
            details=f"Criada e alternada para a branch: '{req.name}'"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/merge", tags=["Git Bridge"])
def git_merge_branch(req: GitMergeRequest,
                     project: Project = Depends(get_project_or_404),
                     db: Session = Depends(get_db),
                     _ = Depends(get_api_key)):
    """Mescla uma branch na branch ativa."""
    try:
        result = git_bridge.merge_branch(project.path, req.branch)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_MERGE",
            details=f"Branch '{req.branch}' mesclada na branch ativa"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        conflicts = git_bridge.list_conflicts(project.path)
        if conflicts.get("files"):
            raise HTTPException(status_code=409, detail={
                "message": str(e),
                "has_conflicts": True,
                "conflicts": conflicts.get("files", [])
            })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/git/conflicts", tags=["Git Bridge"])
def git_list_conflicts(project: Project = Depends(get_project_or_404)):
    """Lista arquivos e blocos com marcadores de conflito Git."""
    try:
        return git_bridge.list_conflicts(project.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/git/conflicts/file", tags=["Git Bridge"])
def git_get_conflict_file(filepath: str = Query(...),
                          project: Project = Depends(get_project_or_404)):
    """Retorna o conteúdo e os blocos de conflito de um arquivo."""
    try:
        return git_bridge.get_conflict_file(project.path, filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/conflicts/resolve", tags=["Git Bridge"])
def git_resolve_conflict(req: GitConflictResolveRequest,
                         project: Project = Depends(get_project_or_404),
                         db: Session = Depends(get_db),
                         _ = Depends(get_api_key)):
    """Resolve blocos de conflito em um arquivo e adiciona ao stage quando não restarem conflitos."""
    try:
        payload = [item.model_dump() for item in req.resolutions]
        result = git_bridge.resolve_conflict_file(project.path, req.filepath, payload, req.stage_file)
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_CONFLICT_RESOLVE",
            details=f"Conflitos resolvidos em {req.filepath}. Restantes: {result.get('remaining_blocks')}"
        )
        db.add(log)
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/push", tags=["Git Bridge"])
def git_push(req: GitPushRequest,
             project: Project = Depends(get_project_or_404),
             db: Session = Depends(get_db),
             _ = Depends(get_api_key)):
    """Executa um Git push para enviar commits locais para o repositório remoto."""
    try:
        result = git_bridge.push_git(project.path, req.branch)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_PUSH",
            details=f"Git push executado na branch {req.branch or 'atual'}"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/merge/abort", tags=["Git Bridge"])
def git_abort_merge(project: Project = Depends(get_project_or_404),
                    db: Session = Depends(get_db),
                    _ = Depends(get_api_key)):
    """Aborta a mesclagem em andamento no repositório Git."""
    try:
        result = git_bridge.abort_merge(project.path)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_MERGE_ABORT",
            details="Mesclagem (merge) abortada pelo usuário"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/git/token", tags=["Git Bridge"])
def git_set_token(req: GitSetTokenRequest,
                  project: Project = Depends(get_project_or_404),
                  db: Session = Depends(get_db),
                  _ = Depends(get_api_key)):
    """Configura o token de acesso GitHub na URL remota de origin."""
    try:
        result = git_bridge.set_remote_token(project.path, req.token)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_TOKEN_SET",
            details="Token do GitHub configurado na URL remota de origin."
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import re
def parse_github_remote(url: str):
    """Retorna (owner, repo) de uma URL de controle remoto do GitHub."""
    if not url:
        return None
    # Matches:
    # https://github.com/owner/repo.git
    # https://github.com/owner/repo
    # git@github.com:owner/repo.git
    # git@github.com:owner/repo
    pattern = r'(?:https://github\.com/|git@github\.com:)([^/]+)/([^/.]+)(?:\.git)?'
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None

@app.post("/api/projects/{project_id}/git/pullrequest", tags=["Git Bridge"])
def git_create_pull_request(req: GitPullRequestCreate,
                            project: Project = Depends(get_project_or_404),
                            db: Session = Depends(get_db),
                            _ = Depends(get_api_key)):
    """Cria um Pull Request no repositório remoto do GitHub para o projeto ativo."""
    conf = get_config()
    token = conf.get("github_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Usuário não autenticado no GitHub. Por favor, conecte sua conta do GitHub na aba de configurações.")
        
    remote_url = project.git_remote
    if not remote_url:
        try:
            remote_url = git_bridge.get_remote_url(project.path)
        except Exception:
            pass
            
    if not remote_url:
        raise HTTPException(status_code=400, detail="Este projeto não possui um repositório remoto configurado.")
        
    parsed = parse_github_remote(remote_url)
    if not parsed:
        raise HTTPException(status_code=400, detail=f"A URL remota '{remote_url}' não é um repositório do GitHub válido.")
        
    owner, repo = parsed
    
    try:
        active_branch = git_bridge.get_active_branch(project.path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter a branch ativa: {str(e)}")
        
    if active_branch == "DETACHED":
        raise HTTPException(status_code=400, detail="O repositório está em estado DETACHED HEAD. Não é possível criar um Pull Request.")
        
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Act IA"
    }
    payload = {
        "title": req.title,
        "head": active_branch,
        "base": req.base,
        "body": req.body or ""
    }
    
    try:
        github_res = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if github_res.status_code == 201:
            data = github_res.json()
            
            log = ActivityLog(
                project_id=project.id,
                action_type="GIT_PR_CREATE",
                details=f"Pull Request #{data.get('number')} criado no GitHub: '{req.title}'"
            )
            db.add(log)
            db.commit()
            
            return {
                "status": "success",
                "pr_number": data.get("number"),
                "html_url": data.get("html_url"),
                "title": data.get("title"),
                "state": data.get("state")
            }
        else:
            try:
                err_data = github_res.json()
                msg = err_data.get("message", github_res.text)
                errors = err_data.get("errors", [])
                if errors:
                    import json
                    msg += f" Details: {json.dumps(errors)}"
            except Exception:
                msg = github_res.text
            raise HTTPException(status_code=github_res.status_code, detail=f"Erro do GitHub: {msg}")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com a API do GitHub: {str(e)}")



# --- ENDPOINTS DE AUTENTICAÇÃO DO GITHUB ---

GITHUB_CLIENT_ID_DEFAULT = "Ov23liWV2HdC0RBLecWx"

@app.post("/api/github/auth/device", tags=["GitHub Auth"])
def github_auth_device(req: DeviceAuthRequest = DeviceAuthRequest()):
    """Inicia o fluxo de autenticação por dispositivo (OAuth Device Flow)."""
    client_id = GITHUB_CLIENT_ID_DEFAULT
    if req and req.client_id:
        client_id = req.client_id
    else:
        conf = get_config()
        client_id = conf.get("github_client_id", GITHUB_CLIENT_ID_DEFAULT)
        
    try:
        res = requests.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            json={
                "client_id": client_id,
                "scope": "repo,user,workflow"
            },
            timeout=10
        )
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=f"Erro do GitHub: {res.text}")
        return res.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao conectar com o GitHub: {str(e)}")

@app.post("/api/github/auth/poll", tags=["GitHub Auth"])
def github_auth_poll(req: PollRequest):
    """Verifica se o usuário autorizou o dispositivo no GitHub."""
    client_id = req.client_id
    if not client_id:
        conf = get_config()
        client_id = conf.get("github_client_id", GITHUB_CLIENT_ID_DEFAULT)
        
    try:
        res = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": client_id,
                "device_code": req.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            },
            timeout=10
        )
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=f"Erro do GitHub: {res.text}")
            
        data = res.json()
        if "access_token" in data:
            conf = get_config()
            conf["github_access_token"] = data["access_token"]
            if req.client_id:
                conf["github_client_id"] = req.client_id
            save_config(conf)
            return {"status": "success", "access_token": "Saved securely"}
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao consultar token: {str(e)}")

@app.get("/api/github/auth/status", tags=["GitHub Auth"])
def github_auth_status():
    """Retorna o status da autenticação com o GitHub e informações básicas do usuário."""
    conf = get_config()
    token = conf.get("github_access_token")
    if not token:
        return {"authenticated": False}
        
    try:
        res = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "Act IA"
            },
            timeout=10
        )
        if res.status_code == 200:
            return {"authenticated": True, "user": res.json()}
        elif res.status_code == 401:
            conf.pop("github_access_token", None)
            save_config(conf)
            return {"authenticated": False}
        else:
            raise HTTPException(status_code=res.status_code, detail=f"Erro do GitHub: {res.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao checar status do GitHub: {str(e)}")

@app.post("/api/github/auth/token", tags=["GitHub Auth"])
def github_auth_set_token(req: GitSetTokenRequest):
    """Configura manualmente o token de acesso global do GitHub (PAT)."""
    token = req.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="O token não pode estar vazio.")
    
    conf = get_config()
    conf["github_access_token"] = token
    save_config(conf)
    return {"status": "success"}

@app.post("/api/github/auth/logout", tags=["GitHub Auth"])
def github_auth_logout():
    """Desconecta a conta do GitHub e apaga o token salvo."""
    conf = get_config()
    conf.pop("github_access_token", None)
    save_config(conf)
    return {"status": "success"}

@app.get("/api/github/repos", tags=["GitHub Auth"])
def github_list_repos():
    """Retorna os repositórios do usuário autenticado."""
    conf = get_config()
    token = conf.get("github_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Usuário não autenticado no GitHub.")
        
    try:
        res = requests.get(
            "https://api.github.com/user/repos?visibility=all&per_page=100&sort=updated",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "Act IA"
            },
            timeout=10
        )
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=f"Erro do GitHub ao buscar repos: {res.text}")
            
        repos = res.json()
        result = []
        for repo in repos:
            result.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "clone_url": repo.get("clone_url")
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao buscar repositórios do GitHub: {str(e)}")

# Logs de Atividade e Rollbacks
@app.get("/api/projects/{project_id}/logs", tags=["VCS Logs"])
def list_logs(project_id: int, db: Session = Depends(get_db)):
    """Retorna o histórico de atividades recentes do projeto com informação de diff."""
    logs = db.query(ActivityLog).filter(ActivityLog.project_id == project_id).order_by(ActivityLog.timestamp.desc()).limit(100).all()
    
    result = []
    for log in logs:
        has_snapshot = db.query(FileSnapshot).filter(FileSnapshot.activity_log_id == log.id).first() is not None
        result.append({
            "id": log.id,
            "project_id": log.project_id,
            "timestamp": log.timestamp.isoformat(),
            "action_type": log.action_type,
            "details": log.details,
            "has_snapshot": has_snapshot
        })
    return result

@app.get("/api/projects/{project_id}/logs/{log_id}/diff", tags=["VCS Logs"])
def get_log_diff(project_id: int, log_id: int, db: Session = Depends(get_db)):
    """Retorna o diff da alteração associada a um log específico."""
    log = db.query(ActivityLog).filter(ActivityLog.project_id == project_id, ActivityLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado")
        
    # Busca o snapshot associado a este log
    snapshot = db.query(FileSnapshot).filter(
        FileSnapshot.project_id == project_id,
        FileSnapshot.activity_log_id == log_id
    ).first()
    
    if not snapshot:
        return {
            "has_diff": False,
            "message": "Nenhuma alteração de arquivo registrada para esta atividade."
        }
        
    filepath = snapshot.filepath
    if log.action_type == "FILE_DELETE":
        old_content = snapshot.content
        new_content = ""
    else:
        new_content = snapshot.content
        # Busca o snapshot imediatamente anterior deste mesmo arquivo
        prev_snapshot = db.query(FileSnapshot).filter(
            FileSnapshot.project_id == project_id,
            FileSnapshot.filepath == filepath,
            FileSnapshot.id < snapshot.id
        ).order_by(FileSnapshot.id.desc()).first()
        old_content = prev_snapshot.content if prev_snapshot else ""
        
    # Gera o diff
    import difflib
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff_generator = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    )
    diff_text = "\n".join(diff_generator)
    
    return {
        "has_diff": True,
        "filepath": filepath,
        "action_type": log.action_type,
        "diff": diff_text
    }

@app.get("/api/projects/{project_id}/snapshots", tags=["VCS Logs"])
def list_snapshots(project_id: int, filepath: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista todos os snapshots criados para um arquivo específico ou todo o projeto."""
    query = db.query(FileSnapshot).filter(FileSnapshot.project_id == project_id)
    if filepath:
        query = query.filter(FileSnapshot.filepath == filepath.replace('\\', '/'))
    return query.order_by(FileSnapshot.timestamp.desc()).all()

@app.post("/api/projects/{project_id}/snapshots/{snapshot_id}/rollback", tags=["VCS Logs"])
def rollback_snapshot(snapshot_id: int, 
                      project: Project = Depends(get_project_or_404),
                      db: Session = Depends(get_db),
                      _ = Depends(get_api_key)):
    """
    Restaura um arquivo para o conteúdo salvo em um snapshot.
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        result = vcs.rollback_project_file(db, project, snapshot_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINTS DE DOCUMENTOS ---

@app.post("/api/projects/{project_id}/documents/word", tags=["Documentos"])
def create_word_document(
    req: DocumentCreateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Gera um documento Word (.docx) no diretório .documents do projeto."""
    try:
        sections_list = [sec.model_dump() for sec in req.sections]
        result = generate_docx(project.path, req.title, sections_list)
        
        # Salva o arquivo JSON de metadados correspondente para carregamento rápido do preview
        json_filename = result["filename"].replace(".docx", ".json")
        json_filepath = os.path.join(project.path, ".documents", json_filename)
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump({
                "title": req.title,
                "sections": sections_list
            }, f, indent=4, ensure_ascii=False)
        
        # Log da ação no banco de dados
        log = ActivityLog(
            project_id=project.id,
            action_type="DOCUMENT_GENERATED",
            details=f"Documento Word gerado: {result.get('filename')}"
        )
        db.add(log)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar documento Word: {str(e)}")

BUSINESS_DOCUMENTS = {
    "charter": {
        "filename": "termo-de-abertura-do-projeto.docx",
        "title": "Termo de Abertura do Projeto",
        "source": ".documents/project-charter.md",
        "description": "Documento executivo de abertura, contexto, escopo, riscos e critérios de sucesso.",
    },
    "specify": {
        "filename": "specify-especificacao.docx",
        "title": "Specify - Especificação",
        "source": ".documents/requirements/**/*.md",
        "description": "Todos os REQs e RFs funcionais criados no projeto, com cada especificação em uma nova página.",
    },
    "design": {
        "filename": "design-planejamento.docx",
        "title": "Design - Planejamento",
        "source": ".documents/design/design.md",
        "description": "Planejamento técnico, arquitetura proposta, dados, integrações e validações.",
    },
    "dri": {
        "filename": "dri-documento-de-requisito-de-interface.docx",
        "title": "DRI - Documento de Requisito de Interface",
        "source": ".documents/dri/dri.md",
        "description": "Documento de interfaces, componentes, estados, microcopy, responsividade e aceite visual.",
    },
    "tasks": {
        "filename": "task-list-tarefas-e-detalhes.docx",
        "title": "Task List - Tarefas + Task Details",
        "source": ".documents/task/task.md + .documents/task/task.details.md",
        "description": "Tarefas do projeto e planos detalhados acumulados para execução e rastreabilidade.",
    },
}

def _read_text_if_exists(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _markdown_to_word_sections(markdown: str, fallback_heading: str = "") -> list:
    sections = []
    current_heading = fallback_heading
    buffer = []

    def flush():
        nonlocal current_heading, buffer
        text = "\n".join(buffer).strip()
        if current_heading or text:
            sections.append({
                "heading": current_heading,
                "text": text,
                "type": "paragraph"
            })
        current_heading = ""
        buffer = []

    for raw_line in (markdown or "").splitlines():
        line = raw_line.rstrip()
        heading_match = re.match(r"^#{1,6}\s+(.+)$", line.strip())
        if heading_match:
            flush()
            current_heading = heading_match.group(1).strip()
            continue
        buffer.append(line)
    flush()

    return [sec for sec in sections if sec.get("heading") or sec.get("text")]

def _write_business_doc_preview(project: Project, result: dict, title: str, sections: list):
    json_filepath = os.path.join(project.path, ".documents", result["filename"].replace(".docx", ".json"))
    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump({"title": title, "sections": sections}, f, indent=4, ensure_ascii=False)

def _business_doc_status(project: Project, kind: str) -> dict:
    config = BUSINESS_DOCUMENTS[kind]
    filepath = os.path.join(project.path, ".documents", config["filename"])
    exists = os.path.exists(filepath)
    stat = os.stat(filepath) if exists else None
    return {
        "kind": kind,
        "filename": config["filename"],
        "title": config["title"],
        "source": config["source"],
        "description": config["description"],
        "exists": exists,
        "size_bytes": stat.st_size if stat else 0,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else None,
    }

def _build_business_document_sections(project: Project, kind: str) -> list:
    docs_dir = _sdd_documents_dir(project)
    if kind == "charter":
        content = _read_text_if_exists(_sdd_charter_path(project)) or _default_sdd_charter(project)
        return _markdown_to_word_sections(content)

    if kind == "specify":
        documents_dir = os.path.join(project.path, ".documents")
        dirs_to_check = [
            os.path.join(documents_dir, "requirements"),
            os.path.join(documents_dir, "spec"),
            os.path.join(documents_dir, "specs")
        ]
        sections = []
        spec_files = []
        
        for d in dirs_to_check:
            if os.path.exists(d):
                for root, _, files in os.walk(d):
                    for filename in files:
                        if filename.lower().endswith(".md"):
                            spec_files.append(os.path.join(root, filename))
                            
        spec_files.sort(key=lambda p: os.path.basename(p).lower())
        
        if not spec_files:
            return [{"heading": "Nenhum REQ encontrado", "text": "Crie REQs em .documents/requirements ou .documents/spec para compor este documento.", "type": "highlight"}]
            
        for index, filepath in enumerate(spec_files):
            if index > 0:
                sections.append({"heading": "", "text": "", "type": "page_break"})
            content = _read_text_if_exists(filepath)
            filename = os.path.basename(filepath)
            req_sections = _markdown_to_word_sections(content, os.path.splitext(filename)[0])
            sections.extend(req_sections or [{"heading": filename, "text": "REQ sem conteúdo.", "type": "paragraph"}])
        return sections

    if kind == "design":
        content = _read_text_if_exists(os.path.join(docs_dir, "design", "design.md")) or _default_sdd_project_document(project, "design")
        return _markdown_to_word_sections(content)

    if kind == "dri":
        content = _read_text_if_exists(os.path.join(docs_dir, "dri", "dri.md")) or _default_sdd_project_document(project, "dri")
        return _markdown_to_word_sections(content)

    if kind == "tasks":
        task_content = _read_text_if_exists(os.path.join(docs_dir, "task", "task.md")) or _default_sdd_project_document(project, "task")
        details_content = _read_text_if_exists(os.path.join(docs_dir, "task", "task.details.md")) or _default_sdd_project_document(project, "task_details")
        return (
            _markdown_to_word_sections(task_content, "Task List - Tarefas")
            + [{"heading": "", "text": "", "type": "page_break"}]
            + _markdown_to_word_sections(details_content, "Task Details - Planos Detalhados")
        )

    raise HTTPException(status_code=400, detail="Documento de negócio inválido.")

def _generate_business_document(project: Project, kind: str) -> dict:
    if kind not in BUSINESS_DOCUMENTS:
        raise HTTPException(status_code=400, detail="Documento de negócio inválido.")
    config = BUSINESS_DOCUMENTS[kind]
    sections = _build_business_document_sections(project, kind)
    result = generate_docx(project.path, config["title"], sections, filename=config["filename"])
    _write_business_doc_preview(project, result, config["title"], sections)
    return _business_doc_status(project, kind)

@app.get("/api/projects/{project_id}/documents/business", tags=["Documentos"])
def list_business_documents(project: Project = Depends(get_project_or_404)):
    """Lista os documentos Word oficiais derivados dos arquivos Harness vivos."""
    return [_business_doc_status(project, kind) for kind in BUSINESS_DOCUMENTS]

@app.post("/api/projects/{project_id}/documents/business/generate", tags=["Documentos"])
def generate_business_documents(
    req: BusinessDocumentGenerateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Gera ou atualiza documentos Word oficiais para a área de negócio."""
    kinds = list(BUSINESS_DOCUMENTS.keys()) if req.kind == "all" else [req.kind]
    try:
        generated = [_generate_business_document(project, kind) for kind in kinds]
        log = ActivityLog(
            project_id=project.id,
            action_type="BUSINESS_DOCUMENTS_GENERATED",
            details=f"Documentos Word de negócio atualizados: {', '.join(item['filename'] for item in generated)}"
        )
        db.add(log)
        db.commit()
        return {"status": "success", "documents": generated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar documentos de negócio: {str(e)}")

@app.post("/api/projects/{project_id}/documents/upload", tags=["Documentos"])
def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Realiza o upload de um documento Word (.docx) no diretório .documents do projeto."""
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Somente arquivos .docx (Word) são permitidos.")
        
    docs_dir = os.path.join(project.path, ".documents")
    os.makedirs(docs_dir, exist_ok=True)
    
    # Previne directory traversal no nome do arquivo
    safe_filename = os.path.basename(file.filename)
    filepath = os.path.join(docs_dir, safe_filename)
    
    try:
        # Lê o conteúdo do upload
        contents = file.file.read()
        
        with open(filepath, "wb") as f:
            f.write(contents)
            
        # Log da ação no banco de dados
        log = ActivityLog(
            project_id=project.id,
            action_type="DOCUMENT_UPLOADED",
            details=f"Documento Word enviado: {safe_filename}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "filename": safe_filename,
            "filepath": filepath,
            "size_bytes": os.path.getsize(filepath)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")

@app.get("/api/projects/{project_id}/documents", tags=["Documentos"])
def list_documents(project: Project = Depends(get_project_or_404)):
    """Lista todos os documentos Word (.docx) gerados no diretório .documents do projeto."""
    docs_dir = os.path.join(project.path, ".documents")
    if not os.path.exists(docs_dir):
        return []
    
    documents = []
    try:
        for entry in os.scandir(docs_dir):
            if entry.is_file() and entry.name.endswith(".docx"):
                stat = entry.stat()
                documents.append({
                    "filename": entry.name,
                    "filepath": entry.path,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        # Ordena pelos mais recentes
        documents.sort(key=lambda x: x["modified_at"], reverse=True)
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {str(e)}")

@app.get("/api/projects/{project_id}/documents/{filename}/download", tags=["Documentos"])
def download_document(filename: str, project: Project = Depends(get_project_or_404)):
    """Faz o download do documento Word especificado."""
    # Garante segurança de caminho impedindo navegação de diretório
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    filepath = os.path.join(project.path, ".documents", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
        
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@app.get("/api/projects/{project_id}/documents/{filename}/preview", tags=["Documentos"])
def preview_document(filename: str, project: Project = Depends(get_project_or_404)):
    """Retorna a estrutura JSON do documento (parágrafos, tabelas, etc.) para visualização na UI."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    docx_filepath = os.path.join(project.path, ".documents", filename)
    if not os.path.exists(docx_filepath):
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
        
    # Caminho alternativo do JSON cache
    json_filepath = docx_filepath.replace(".docx", ".json")
    if os.path.exists(json_filepath):
        try:
            with open(json_filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Se não houver cache de JSON, analisa o .docx de forma heurística
    try:
        return parse_docx_to_json(docx_filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar prévia do documento: {str(e)}")

@app.delete("/api/projects/{project_id}/documents/{filename}", tags=["Documentos"])
def delete_document(
    filename: str,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Deleta o documento Word especificado e seu arquivo JSON de preview correspondente."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    docx_filepath = os.path.join(project.path, ".documents", filename)
    if not os.path.exists(docx_filepath):
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
        
    try:
        os.remove(docx_filepath)
        
        # Deleta também o JSON correspondente se existir
        json_filepath = docx_filepath.replace(".docx", ".json")
        if os.path.exists(json_filepath):
            os.remove(json_filepath)
            
        # Log da ação no banco de dados
        log = ActivityLog(
            project_id=project.id,
            action_type="DOCUMENT_DELETED",
            details=f"Documento Word deletado: {filename}"
        )
        db.add(log)
        db.commit()
        
        return {"status": "success", "message": "Documento deletado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar documento: {str(e)}")

# --- ENDPOINTS OPS INFRA ---

def _ops_detect_stack(project_path: str) -> dict:
    files = set(os.listdir(project_path)) if os.path.isdir(project_path) else set()

    def exists(name: str) -> bool:
        return name in files or os.path.exists(os.path.join(project_path, name))

    if exists("package.json"):
        scripts = {}
        try:
            with open(os.path.join(project_path, "package.json"), "r", encoding="utf-8") as f:
                scripts = json.load(f).get("scripts", {})
        except Exception:
            pass
        stack = "nextjs" if exists("next.config.js") or exists("next.config.mjs") else "vite" if exists("vite.config.js") or exists("vite.config.ts") else "node"
        return {
            "stack": stack,
            "runtime": "node",
            "port": 3000 if stack == "nextjs" else 5173 if stack == "vite" else 3000,
            "build_command": "npm run build" if "build" in scripts else "npm install",
            "start_command": "npm run start" if "start" in scripts else "npm run dev",
            "evidence": ["package.json"]
        }
    if exists("requirements.txt") or exists("pyproject.toml"):
        if exists("main.py"):
            app_module = "main:app"
        elif exists("app.py"):
            app_module = "app:app"
        elif exists(os.path.join("gitide_server", "main.py")):
            app_module = "gitide_server.main:app"
        else:
            app_module = "main:app"
        return {
            "stack": "python",
            "runtime": "python",
            "port": 8000,
            "build_command": "pip install -r requirements.txt" if exists("requirements.txt") else "pip install .",
            "start_command": f"uvicorn {app_module} --host 0.0.0.0 --port 8000",
            "evidence": ["requirements.txt" if exists("requirements.txt") else "pyproject.toml"]
        }
    return {"stack": "unknown", "runtime": "unknown", "port": 8080, "build_command": "", "start_command": "", "evidence": []}

def _ops_artifacts(project_path: str, env: str, domain: Optional[str], database: Optional[str]) -> dict:
    detected = _ops_detect_stack(project_path)
    port = detected["port"]
    clean_domain = (domain or "").strip()
    if detected["runtime"] == "python":
        dockerfile = (
            "FROM python:3.12-slim\nWORKDIR /app\n"
            "COPY requirements.txt* pyproject.toml* ./\n"
            "RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir .; fi\n"
            "COPY . .\n"
            f"EXPOSE {port}\n"
            f'CMD ["sh", "-c", "{detected["start_command"]}"]\n'
        )
    else:
        dockerfile = (
            "FROM node:20-alpine\nWORKDIR /app\nCOPY package*.json ./\n"
            "RUN npm ci || npm install\nCOPY . .\n"
            f"RUN {detected['build_command']}\n"
            f"EXPOSE {port}\n"
            f'CMD ["sh", "-c", "{detected["start_command"]}"]\n'
        )

    services = [
        "services:",
        "  app:",
        "    build: .",
        f"    container_name: ${{APP_NAME:-act-ia-app}}-{env}",
        "    restart: unless-stopped",
        "    env_file:",
        "      - .env",
    ]
    uses_postgres = (database or "").lower().strip() == "postgres"
    if uses_postgres:
        services += [
            "    depends_on:",
            "      - postgres",
        ]
    if clean_domain:
        services += [
            "    expose:",
            f"      - \"{port}\"",
            "  caddy:",
            "    image: caddy:2-alpine",
            f"    container_name: ${{APP_NAME:-act-ia-app}}-{env}-caddy",
            "    restart: unless-stopped",
            "    depends_on:",
            "      - app",
            "    ports:",
            "      - \"80:80\"",
            "      - \"443:443\"",
            "    volumes:",
            "      - ./Caddyfile:/etc/caddy/Caddyfile:ro",
            "      - caddy_data:/data",
            "      - caddy_config:/config",
        ]
    else:
        services += [
            "    ports:",
            f"      - \"${{APP_PORT:-{port}}}:{port}\"",
        ]
    env_lines = [f"APP_ENV={env}", "APP_NAME=act-ia-app", f"APP_PORT={port}", f"APP_DOMAIN={domain or ''}"]
    volumes = []
    if clean_domain:
        volumes += ["  caddy_data:", "  caddy_config:"]

    if uses_postgres:
        services += [
            "  postgres:",
            "    image: postgres:16-alpine",
            "    restart: unless-stopped",
            "    environment:",
            "      POSTGRES_DB: ${POSTGRES_DB:-app}",
            "      POSTGRES_USER: ${POSTGRES_USER:-app}",
            "      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_me}",
            "    volumes:",
            "      - postgres_data:/var/lib/postgresql/data",
        ]
        volumes.append("  postgres_data:")
        env_lines += ["POSTGRES_DB=app", "POSTGRES_USER=app", "POSTGRES_PASSWORD=change_me", "DATABASE_URL=postgresql://app:change_me@postgres:5432/app"]

    if volumes:
        services += ["volumes:", *volumes]
    else:
        services += ["volumes: {}"]

    compose = "\n".join(services) + "\n"
    env_example = "\n".join(env_lines) + "\n"
    caddyfile = _ops_caddyfile(clean_domain or "example.com", port)
    return {"detected": detected, "files": {"Dockerfile": dockerfile, "docker-compose.yml": compose, ".env.example": env_example, "Caddyfile": caddyfile}}

def _ops_caddyfile(domain: str, app_port: int) -> str:
    return (
        f"{domain} {{\n"
        "    encode gzip zstd\n"
        f"    reverse_proxy app:{app_port}\n"
        "}\n"
    )

def _ops_domain_preview(project_path: str, domain: str) -> dict:
    detected = _ops_detect_stack(project_path)
    clean_domain = domain.strip().lower()
    root_domain = ".".join(clean_domain.split(".")[-2:]) if "." in clean_domain else clean_domain
    return {
        "domain": clean_domain,
        "stack": detected,
        "caddyfile": _ops_caddyfile(clean_domain, detected["port"]),
        "dns": [
            f"Crie um registro A para {clean_domain} apontando para o IP publico do servidor.",
            f"Se usar subdominio, voce tambem pode criar CNAME de {clean_domain} para {root_domain}.",
            "Libere as portas 80 e 443 no firewall do servidor.",
            "O Caddy emitira e renovara SSL automaticamente quando o DNS estiver propagado."
        ],
        "compose_notes": [
            "O servico caddy publica 80:80 e 443:443.",
            f"O app fica interno no Docker e o Caddy encaminha para app:{detected['port']}.",
            "Os volumes caddy_data e caddy_config preservam certificados e configuracoes."
        ]
    }

def _ops_env_dir(project_path: str) -> str:
    path = os.path.join(project_path, ".gitide", "ops-infra")
    os.makedirs(path, exist_ok=True)
    return path

def _ops_secret_key() -> bytes:
    key_path = os.path.join(CONFIG_DIR, "ops_secret.key")
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
    except Exception:
        key = secrets.token_urlsafe(32).encode("utf-8")
    with open(key_path, "wb") as f:
        f.write(key)
    return key

def _ops_encrypt_secret(value: str) -> str:
    try:
        from cryptography.fernet import Fernet
        return "fernet:" + Fernet(_ops_secret_key()).encrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        import base64
        return "b64:" + base64.b64encode(value.encode("utf-8")).decode("utf-8")

def _ops_decrypt_secret(value: str) -> str:
    try:
        if value.startswith("fernet:"):
            from cryptography.fernet import Fernet
            return Fernet(_ops_secret_key()).decrypt(value.replace("fernet:", "", 1).encode("utf-8")).decode("utf-8")
        if value.startswith("b64:"):
            import base64
            return base64.b64decode(value.replace("b64:", "", 1)).decode("utf-8")
    except Exception:
        return ""
    return value

def _ops_env_path(project_path: str, environment: str) -> str:
    safe_env = re.sub(r"[^a-zA-Z0-9_-]", "", environment or "prod") or "prod"
    return os.path.join(_ops_env_dir(project_path), f"{safe_env}.json")

def _ops_vm_access_path(project_path: str) -> str:
    return os.path.join(_ops_env_dir(project_path), "vm-access.json")

def _ops_normalize_vm_access(req: OpsInfraVmAccessRequest) -> dict:
    host = (req.host or "").strip()
    user = (req.user or "").strip()
    app_path = (req.app_path or "").strip()
    auth_method = (req.auth_method or "key").strip().lower()
    port = req.port or 22
    if not host:
        raise HTTPException(status_code=400, detail="Informe o IP ou host da VM.")
    if not re.match(r"^[a-zA-Z0-9._:-]+$", host):
        raise HTTPException(status_code=400, detail="Host da VM contém caracteres inválidos.")
    if not user:
        raise HTTPException(status_code=400, detail="Informe o usuário SSH.")
    if not re.match(r"^[a-zA-Z0-9._-]+$", user):
        raise HTTPException(status_code=400, detail="Usuário SSH contém caracteres inválidos.")
    if port < 1 or port > 65535:
        raise HTTPException(status_code=400, detail="Porta SSH inválida.")
    if app_path and not app_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Diretório do app deve ser um caminho absoluto na VM.")
    if auth_method not in ["agent", "key", "password"]:
        raise HTTPException(status_code=400, detail="Método de autenticação SSH inválido.")
    private_key = (req.private_key or "").strip()
    if auth_method == "key" and private_key:
        if private_key.startswith(("ssh-rsa ", "ssh-ed25519 ", "ecdsa-sha2-")):
            raise HTTPException(status_code=400, detail="Você colou uma chave pública. Cole a chave privada SSH completa, iniciando com -----BEGIN OPENSSH PRIVATE KEY-----.")
        if "PRIVATE KEY" not in private_key:
            raise HTTPException(status_code=400, detail="Chave privada SSH inválida. Cole o conteúdo completo da chave privada.")
    return {
        "host": host,
        "user": user,
        "port": port,
        "app_path": app_path,
        "auth_method": auth_method,
        "private_key": private_key,
        "password": req.password or "",
    }

def _ops_read_vm_access(project_path: str, public: bool = True) -> dict:
    path = _ops_vm_access_path(project_path)
    if not os.path.exists(path):
        return {"host": "", "user": "", "port": 22, "app_path": "", "auth_method": "key", "private_key": "", "password": "", "has_private_key": False, "has_password": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        has_private_key = bool(data.get("private_key"))
        has_password = bool(data.get("password"))
        return {
            "host": data.get("host", ""),
            "user": data.get("user", ""),
            "port": int(data.get("port", 22) or 22),
            "app_path": data.get("app_path", ""),
            "auth_method": data.get("auth_method", "key"),
            "private_key": "" if public else data.get("private_key", ""),
            "password": "" if public else data.get("password", ""),
            "public_key": data.get("public_key", ""),
            "has_private_key": has_private_key,
            "has_password": has_password,
        }
    except Exception:
        return {"host": "", "user": "", "port": 22, "app_path": "", "auth_method": "key", "private_key": "", "password": "", "has_private_key": False, "has_password": False}

def _ops_write_vm_access(project_path: str, req: OpsInfraVmAccessRequest) -> dict:
    payload = _ops_normalize_vm_access(req)
    existing = {}
    path = _ops_vm_access_path(project_path)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    if payload["private_key"]:
        payload["private_key"] = _ops_encrypt_secret(payload["private_key"])
    else:
        payload["private_key"] = existing.get("private_key", "")
    if payload["password"]:
        payload["password"] = _ops_encrypt_secret(payload["password"])
    else:
        payload["password"] = existing.get("password", "")
    with open(_ops_vm_access_path(project_path), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return _ops_read_vm_access(project_path, public=False)

def _ops_generate_keypair(project_path: str, comment: str = "act-ia-ops-infra") -> dict:
    if not shutil.which("ssh-keygen"):
        raise HTTPException(status_code=500, detail="ssh-keygen não encontrado no servidor do Act IA.")
    key_path = None
    public_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=True) as marker:
            key_path = marker.name
        public_path = f"{key_path}.pub"
        result = subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-C", comment, "-f", key_path],
            text=True,
            capture_output=True,
            timeout=20,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr or "Falha ao gerar chave SSH.")
        with open(key_path, "r", encoding="utf-8") as f:
            private_key = f.read().strip()
        with open(public_path, "r", encoding="utf-8") as f:
            public_key = f.read().strip()
        existing = _ops_read_vm_access(project_path, public=False)
        payload = {
            "host": existing.get("host", ""),
            "user": existing.get("user", ""),
            "port": existing.get("port", 22),
            "app_path": existing.get("app_path", ""),
            "auth_method": "key",
            "private_key": _ops_encrypt_secret(private_key),
            "password": existing.get("password", ""),
            "public_key": public_key,
        }
        with open(_ops_vm_access_path(project_path), "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return {"public_key": public_key, **_ops_read_vm_access(project_path, public=True)}
    finally:
        for path in [key_path, public_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

def _ops_shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"

def _ops_lock_private_key_file(path: str) -> None:
    if os.name == "nt":
        try:
            current_user = os.environ.get("USERNAME") or os.environ.get("USER") or "Administrators"
            subprocess.run(["icacls", path, "/inheritance:r"], text=True, capture_output=True, timeout=10)
            for principal in ["Users", "Authenticated Users", "Everyone", "CodexSandboxUsers"]:
                subprocess.run(["icacls", path, "/remove:g", principal], text=True, capture_output=True, timeout=10)
            subprocess.run(["icacls", path, "/grant:r", f"{current_user}:R"], text=True, capture_output=True, timeout=10)
        except Exception:
            pass
        return
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass

def _ops_ssh_base_args(access: dict, batch_mode: bool = True) -> List[str]:
    args = [
        "-o", "ConnectTimeout=12",
        "-o", "StrictHostKeyChecking=accept-new",
        "-p", str(access.get("port") or 22),
        f"{access.get('user')}@{access.get('host')}",
    ]
    if batch_mode:
        args = ["-o", "BatchMode=yes"] + args
    return args

def _ops_run_ssh(access: dict, remote_command: str, timeout: int = 120) -> dict:
    auth_method = access.get("auth_method", "key")
    temp_key_path = None
    prefix = []
    ssh_args = _ops_ssh_base_args(access)
    stored_key = access.get("private_key", "")
    stored_password = access.get("password", "")
    try:
        if auth_method == "key":
            private_key = _ops_decrypt_secret(stored_key) if stored_key else ""
            if private_key:
                key_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", newline="\n")
                key_file.write(private_key.replace("\r\n", "\n").strip() + "\n")
                key_file.close()
                temp_key_path = key_file.name
                _ops_lock_private_key_file(temp_key_path)
                ssh_args = ["-i", temp_key_path] + ssh_args
        elif auth_method == "password":
            password = _ops_decrypt_secret(stored_password) if stored_password else ""
            if not password:
                raise HTTPException(status_code=400, detail="Informe a senha SSH ou troque o método de autenticação.")
            if not shutil.which("sshpass"):
                raise HTTPException(status_code=400, detail="Autenticação por senha requer sshpass instalado no servidor do Act IA. Use chave privada SSH ou configure chave pública na VM.")
            prefix = ["sshpass", "-p", password]
            ssh_args = ["-o", "PreferredAuthentications=password"] + _ops_ssh_base_args(access, batch_mode=False)
        cmd = prefix + ["ssh"] + ssh_args + [remote_command]
        safe_cmd = cmd.copy()
        if prefix:
            safe_cmd[2] = "********"
        if temp_key_path:
            safe_cmd = ["[ssh-key-file] " + item if item == temp_key_path else item for item in safe_cmd]
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "status": "success" if result.returncode == 0 else "error",
            "command": " ".join(safe_cmd[:-1] + [remote_command]),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Cliente SSH não encontrado no servidor do Act IA.")
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "command": "ssh",
            "exit_code": 124,
            "stdout": "",
            "stderr": "Timeout ao conectar/executar comando via SSH.",
        }
    finally:
        if temp_key_path:
            try:
                os.remove(temp_key_path)
            except Exception:
                pass

def _ops_require_vm_access(project_path: str) -> dict:
    access = _ops_read_vm_access(project_path, public=False)
    if not access.get("host") or not access.get("user"):
        raise HTTPException(status_code=400, detail="Configure VM / Acesso antes de executar esta operação.")
    return access

def _ops_require_app_path(access: dict) -> str:
    app_path = access.get("app_path", "")
    if not app_path:
        raise HTTPException(status_code=400, detail="Informe o diretório do app na VM.")
    return app_path

def _ops_bootstrap_script() -> str:
    return r"""set -e
echo "ACTIA_BOOTSTRAP_START"
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl gnupg git ufw
  install -m 0755 -d /etc/apt/keyrings
  if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg || true
    chmod a+r /etc/apt/keyrings/docker.gpg || true
  fi
  if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
    . /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME:-jammy} stable" > /etc/apt/sources.list.d/docker.list
  fi
  apt-get update -y
  DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y dnf-plugins-core git curl
  dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || true
  dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
elif command -v yum >/dev/null 2>&1; then
  yum install -y yum-utils git curl
  yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || true
  yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
  echo "Gerenciador de pacotes nao suportado. Instale Docker, Compose e Git manualmente."
  exit 2
fi
systemctl enable docker || true
systemctl start docker || true
if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 80/tcp || true
  ufw allow 443/tcp || true
fi
docker --version
docker compose version || docker-compose version
git --version
echo "ACTIA_BOOTSTRAP_OK"
"""

def _ops_sync_script(app_path: str, git_remote: Optional[str]) -> str:
    if not git_remote:
        raise HTTPException(status_code=400, detail="O projeto precisa ter um repositório Git remoto configurado para sincronizar na VM.")
    remote = _ops_shell_quote(git_remote)
    path = _ops_shell_quote(app_path)
    return (
        "set -e\n"
        f"mkdir -p {path}\n"
        f"if [ -d {path}/.git ]; then\n"
        f"  cd {path} && git fetch --all --prune && git pull --ff-only || git pull --rebase;\n"
        "else\n"
        f"  git clone {remote} {path};\n"
        "fi\n"
        f"cd {path} && git rev-parse --abbrev-ref HEAD && git log -1 --oneline\n"
    )

def _ops_health_url(project_path: str, access: dict, req: OpsInfraHealthRequest) -> str:
    detected = _ops_detect_stack(project_path)
    if req.url:
        return req.url.strip()
    domain = (req.domain or "").strip()
    if domain:
        return f"https://{domain}"
    return f"http://{access.get('host')}:{detected.get('port', 8080)}"

def _ops_normalize_remote_path(path: str) -> str:
    value = (path or "/").strip() or "/"
    if not value.startswith("/"):
        raise HTTPException(status_code=400, detail="O caminho remoto deve ser absoluto.")
    if "\n" in value or "\r" in value or "\x00" in value:
        raise HTTPException(status_code=400, detail="Caminho remoto inválido.")
    return os.path.normpath(value).replace("\\", "/") or "/"

def _ops_list_remote_directories(access: dict, path: str) -> dict:
    target = _ops_normalize_remote_path(path)
    quoted = _ops_shell_quote(target)
    command = (
        f"target={quoted}; "
        "if [ ! -d \"$target\" ]; then echo ACTIA_PATH_NOT_FOUND; exit 4; fi; "
        "printf 'ACTIA_PATH\\t%s\\n' \"$target\"; "
        "parent=$(dirname \"$target\"); printf 'ACTIA_PARENT\\t%s\\n' \"$parent\"; "
        "for d in \"$target\"/* \"$target\"/.[!.]* \"$target\"/..?*; do "
        "[ -d \"$d\" ] || continue; "
        "base=$(basename \"$d\"); "
        "case \"$base\" in .|..) continue;; esac; "
        "printf 'DIR\\t%s\\t%s\\n' \"$base\" \"$d\"; "
        "done"
    )
    result = _ops_run_ssh(access, command, timeout=45)
    directories = []
    current = target
    parent = os.path.dirname(target.rstrip("/")) or "/"
    for line in (result.get("stdout") or "").splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        if parts[0] == "ACTIA_PATH" and len(parts) > 1:
            current = parts[1]
        elif parts[0] == "ACTIA_PARENT" and len(parts) > 1:
            parent = parts[1] or "/"
        elif parts[0] == "DIR" and len(parts) > 2:
            directories.append({"name": parts[1], "path": parts[2]})
    directories.sort(key=lambda item: item["name"].lower())
    return {**result, "path": current, "parent": parent, "directories": directories}

def _ops_read_env(project_path: str, environment: str, reveal: bool = False) -> dict:
    path = _ops_env_path(project_path, environment)
    if not os.path.exists(path):
        return {"environment": environment, "variables": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    variables = []
    for item in data.get("variables", []):
        value = item.get("value", "")
        is_secret = bool(item.get("secret"))
        variables.append({
            "key": item.get("key", ""),
            "value": _ops_decrypt_secret(value) if is_secret and reveal else "********" if is_secret else value,
            "secret": is_secret
        })
    return {"environment": data.get("environment", environment), "variables": variables}

def _ops_write_env(project_path: str, req: OpsInfraEnvRequest) -> dict:
    variables = []
    for item in req.variables:
        key = re.sub(r"[^A-Z0-9_]", "_", item.key.strip().upper())
        if not key:
            continue
        variables.append({
            "key": key,
            "value": _ops_encrypt_secret(item.value) if item.secret else item.value,
            "secret": item.secret
        })
    payload = {"environment": req.environment, "variables": variables}
    with open(_ops_env_path(project_path, req.environment), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    env_file = None
    if req.write_env_file:
        env_file = f".env.{req.environment}"
        with open(os.path.join(project_path, env_file), "w", encoding="utf-8") as f:
            for item in variables:
                value = _ops_decrypt_secret(item["value"]) if item["secret"] else item["value"]
                f.write(f"{item['key']}={value}\n")
    return {"environment": req.environment, "variables": _ops_read_env(project_path, req.environment)["variables"], "env_file": env_file}

@app.get("/api/projects/{project_id}/ops-infra/detect", tags=["Ops Infra"])
def ops_infra_detect(project: Project = Depends(get_project_or_404), _ = Depends(get_api_key)):
    return {"status": "success", **_ops_detect_stack(project.path)}

@app.get("/api/projects/{project_id}/ops-infra/vm-access", tags=["Ops Infra"])
def ops_infra_get_vm_access(project: Project = Depends(get_project_or_404), _ = Depends(get_api_key)):
    return {"status": "success", **_ops_read_vm_access(project.path, public=True)}

@app.post("/api/projects/{project_id}/ops-infra/vm-access", tags=["Ops Infra"])
def ops_infra_save_vm_access(req: OpsInfraVmAccessRequest,
                             project: Project = Depends(get_project_or_404),
                             db: Session = Depends(get_db),
                             _ = Depends(get_api_key)):
    result = _ops_write_vm_access(project.path, req)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_VM_ACCESS", details=f"VM configurada: {result['user']}@{result['host']}:{result['port']}"))
    db.commit()
    return {"status": "success", **_ops_read_vm_access(project.path, public=True)}

@app.post("/api/projects/{project_id}/ops-infra/vm-access/generate-key", tags=["Ops Infra"])
def ops_infra_generate_vm_key(project: Project = Depends(get_project_or_404),
                              db: Session = Depends(get_db),
                              _ = Depends(get_api_key)):
    result = _ops_generate_keypair(project.path, f"act-ia-{project.name or project.id}")
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_SSH_KEY", details="Par de chaves SSH gerado para Ops Infra."))
    db.commit()
    return {"status": "success", **result}

@app.post("/api/projects/{project_id}/ops-infra/vm-access/test", tags=["Ops Infra"])
def ops_infra_test_vm_access(req: OpsInfraVmAccessRequest,
                             project: Project = Depends(get_project_or_404),
                             db: Session = Depends(get_db),
                             _ = Depends(get_api_key)):
    access = _ops_write_vm_access(project.path, req)
    remote_parts = ["printf ACTIA_SSH_OK", "pwd", "command -v docker || true", "docker compose version || docker-compose version || true"]
    if access.get("app_path"):
        remote_parts.insert(1, f"test -d {_ops_shell_quote(access['app_path'])} && printf '\\nAPP_PATH_OK\\n' || printf '\\nAPP_PATH_NOT_FOUND\\n'")
    result = _ops_run_ssh(access, " && ".join(remote_parts), timeout=30)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_SSH_TEST", details=f"SSH testado em {access['user']}@{access['host']}:{access['port']} | Exit: {result['exit_code']}"))
    db.commit()
    return {"status": result["status"], **_ops_read_vm_access(project.path, public=True), "test": result}

@app.post("/api/projects/{project_id}/ops-infra/vm/directories", tags=["Ops Infra"])
def ops_infra_list_vm_directories(req: OpsInfraVmDirectoryRequest,
                                  project: Project = Depends(get_project_or_404),
                                  _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    result = _ops_list_remote_directories(access, req.path)
    return {"status": result.get("status"), "path": result.get("path"), "parent": result.get("parent"), "directories": result.get("directories", []), "stderr": result.get("stderr", "")}

@app.post("/api/projects/{project_id}/ops-infra/vm/directories/create", tags=["Ops Infra"])
def ops_infra_create_vm_directory(req: OpsInfraVmDirectoryRequest,
                                  project: Project = Depends(get_project_or_404),
                                  db: Session = Depends(get_db),
                                  _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    target = _ops_normalize_remote_path(req.path)
    result = _ops_run_ssh(access, f"mkdir -p {_ops_shell_quote(target)} && test -d {_ops_shell_quote(target)} && printf ACTIA_DIR_CREATED", timeout=45)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_VM_DIR", details=f"Diretório VM criado/validado: {target} | Exit: {result.get('exit_code')}"))
    db.commit()
    if result.get("status") == "error":
        return result
    listing = _ops_list_remote_directories(access, target)
    return {"status": "success", "created": target, "path": listing.get("path"), "parent": listing.get("parent"), "directories": listing.get("directories", [])}

@app.post("/api/projects/{project_id}/ops-infra/plan", tags=["Ops Infra"])
def ops_infra_plan(req: OpsInfraPlanRequest, project: Project = Depends(get_project_or_404), _ = Depends(get_api_key)):
    detected = _ops_detect_stack(project.path)
    plan = {
        "status": "success",
        "detected": detected,
        "steps": [
            "Validar variáveis de ambiente e secrets",
            "Gerar Dockerfile, docker-compose.yml, .env.example e Caddyfile",
            "Executar docker compose build",
            "Executar docker compose up -d",
            "Validar containers, logs e health check",
            "Configurar proxy/SSL no servidor quando a camada SSH estiver cadastrada"
        ]
    }
    conf = agent.load_agent_config()
    if conf.get("api_key"):
        try:
            raw = agent.call_llm(
                conf.get("provider"),
                conf.get("model"),
                conf.get("api_key"),
                [{"role": "user", "content": f"Planeje deploy para {detected}, env={req.environment}, dominio={req.domain}, banco={req.database}."}],
                "Voce e um especialista DevOps. Responda JSON com summary, risks e steps."
            )
            plan["ai"] = agent.extract_json(raw)
        except Exception as e:
            plan["ai_error"] = str(e)
    return plan

@app.post("/api/projects/{project_id}/ops-infra/artifacts", tags=["Ops Infra"])
def ops_infra_artifacts(req: OpsInfraArtifactRequest,
                        project: Project = Depends(get_project_or_404),
                        db: Session = Depends(get_db),
                        _ = Depends(get_api_key)):
    artifacts = _ops_artifacts(project.path, req.environment, req.domain, req.database)
    written, skipped = [], []
    for rel_path, content in artifacts["files"].items():
        full_path = os.path.join(project.path, rel_path)
        if os.path.exists(full_path) and not req.overwrite:
            skipped.append(rel_path)
            continue
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(rel_path)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_ARTIFACTS", details=f"Arquivos gerados: {', '.join(written)}"))
    db.commit()
    return {"status": "success", "written": written, "skipped": skipped, **artifacts}

@app.post("/api/projects/{project_id}/ops-infra/bootstrap", tags=["Ops Infra"])
def ops_infra_bootstrap(project: Project = Depends(get_project_or_404),
                        db: Session = Depends(get_db),
                        _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    result = _ops_run_ssh(access, _ops_bootstrap_script(), timeout=600)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_BOOTSTRAP", details=f"Bootstrap VM {access.get('host')} | Exit: {result.get('exit_code')}"))
    db.commit()
    return result

@app.post("/api/projects/{project_id}/ops-infra/sync", tags=["Ops Infra"])
def ops_infra_sync_project(project: Project = Depends(get_project_or_404),
                           db: Session = Depends(get_db),
                           _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    app_path = _ops_require_app_path(access)
    result = _ops_run_ssh(access, _ops_sync_script(app_path, project.git_remote), timeout=240)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_SYNC", details=f"Sync {project.git_remote or '-'} -> {access.get('host')}:{app_path} | Exit: {result.get('exit_code')}"))
    db.commit()
    return result

@app.post("/api/projects/{project_id}/ops-infra/dns/check", tags=["Ops Infra"])
def ops_infra_dns_check(req: OpsInfraDnsRequest,
                        project: Project = Depends(get_project_or_404),
                        _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    domain = req.domain.strip().lower()
    if not domain:
        raise HTTPException(status_code=400, detail="Informe o domínio.")
    try:
        records = sorted({item[4][0] for item in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
    except Exception as e:
        return {"status": "error", "domain": domain, "expected": access.get("host"), "records": [], "matches": False, "detail": str(e)}
    expected = access.get("host")
    return {"status": "success", "domain": domain, "expected": expected, "records": records, "matches": expected in records}

@app.post("/api/projects/{project_id}/ops-infra/health", tags=["Ops Infra"])
def ops_infra_health(req: OpsInfraHealthRequest,
                     project: Project = Depends(get_project_or_404),
                     _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    url = _ops_health_url(project.path, access, req)
    try:
        response = requests.get(url, timeout=15, allow_redirects=True)
        return {
            "status": "success" if response.status_code < 500 else "error",
            "url": url,
            "status_code": response.status_code,
            "final_url": response.url,
            "ok": response.ok,
            "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
            "content_type": response.headers.get("content-type", ""),
            "body_preview": response.text[:500],
        }
    except Exception as e:
        return {"status": "error", "url": url, "ok": False, "detail": str(e)}

@app.post("/api/projects/{project_id}/ops-infra/database/check", tags=["Ops Infra"])
def ops_infra_database_check(project: Project = Depends(get_project_or_404),
                             db: Session = Depends(get_db),
                             _ = Depends(get_api_key)):
    access = _ops_require_vm_access(project.path)
    app_path = _ops_require_app_path(access)
    command = (
        f"cd {_ops_shell_quote(app_path)} && "
        "if docker compose config --services | grep -qx postgres; then "
        "docker compose exec -T postgres pg_isready -U ${POSTGRES_USER:-app} -d ${POSTGRES_DB:-app}; "
        "else echo 'Nenhum serviço postgres encontrado no docker-compose.yml'; exit 3; fi"
    )
    result = _ops_run_ssh(access, command, timeout=60)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_DB_CHECK", details=f"Database check em {access.get('host')}:{app_path} | Exit: {result.get('exit_code')}"))
    db.commit()
    return result

@app.post("/api/projects/{project_id}/ops-infra/domain/preview", tags=["Ops Infra"])
def ops_infra_domain_preview(req: OpsInfraDomainRequest,
                             project: Project = Depends(get_project_or_404),
                             _ = Depends(get_api_key)):
    if not req.domain.strip():
        raise HTTPException(status_code=400, detail="Informe um domínio para configurar o Caddy.")
    return {"status": "success", **_ops_domain_preview(project.path, req.domain)}

@app.post("/api/projects/{project_id}/ops-infra/domain/apply", tags=["Ops Infra"])
def ops_infra_domain_apply(req: OpsInfraDomainRequest,
                           project: Project = Depends(get_project_or_404),
                           db: Session = Depends(get_db),
                           _ = Depends(get_api_key)):
    if not req.domain.strip():
        raise HTTPException(status_code=400, detail="Informe um domínio para configurar o Caddy.")
    preview = _ops_domain_preview(project.path, req.domain)
    caddy_path = os.path.join(project.path, "Caddyfile")
    if os.path.exists(caddy_path) and not req.overwrite:
        return {"status": "skipped", "message": "Caddyfile já existe.", **preview}
    with open(caddy_path, "w", encoding="utf-8") as f:
        f.write(preview["caddyfile"])
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_DOMAIN", details=f"Caddyfile configurado para {preview['domain']}"))
    db.commit()
    return {"status": "success", "written": ["Caddyfile"], **preview}

@app.get("/api/projects/{project_id}/ops-infra/env/{environment}", tags=["Ops Infra"])
def ops_infra_get_env(environment: str,
                      project: Project = Depends(get_project_or_404),
                      _ = Depends(get_api_key)):
    return {"status": "success", **_ops_read_env(project.path, environment)}

@app.post("/api/projects/{project_id}/ops-infra/env", tags=["Ops Infra"])
def ops_infra_save_env(req: OpsInfraEnvRequest,
                       project: Project = Depends(get_project_or_404),
                       db: Session = Depends(get_db),
                       _ = Depends(get_api_key)):
    result = _ops_write_env(project.path, req)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_ENV", details=f"Ambiente {req.environment} salvo. Env file: {result.get('env_file')}"))
    db.commit()
    return {"status": "success", **result}

@app.post("/api/projects/{project_id}/ops-infra/env/validate", tags=["Ops Infra"])
def ops_infra_validate_env(req: OpsInfraEnvRequest,
                           project: Project = Depends(get_project_or_404),
                           _ = Depends(get_api_key)):
    detected = _ops_detect_stack(project.path)
    keys = [re.sub(r"[^A-Z0-9_]", "_", item.key.strip().upper()) for item in req.variables if item.key.strip()]
    issues = []
    if "APP_ENV" not in keys:
        issues.append("APP_ENV ausente.")
    if "APP_PORT" not in keys:
        issues.append("APP_PORT ausente.")
    if (req.environment or "").lower() == "prod" and not any(k in keys for k in ["APP_DOMAIN", "DOMAIN"]):
        issues.append("Domínio de produção não informado em APP_DOMAIN ou DOMAIN.")
    if detected.get("runtime") == "node" and not any(k in keys for k in ["NODE_ENV", "APP_ENV"]):
        issues.append("NODE_ENV recomendado para projetos Node.")
    if detected.get("runtime") == "python" and not any(k in keys for k in ["PYTHONUNBUFFERED", "APP_ENV"]):
        issues.append("PYTHONUNBUFFERED=1 recomendado para logs Python em container.")
    return {
        "status": "success",
        "valid": not issues,
        "issues": issues,
        "suggested": [
            {"key": "APP_ENV", "value": req.environment, "secret": False},
            {"key": "APP_PORT", "value": str(detected.get("port", 8080)), "secret": False},
            {"key": "APP_DOMAIN", "value": "", "secret": False},
        ]
    }

@app.post("/api/projects/{project_id}/ops-infra/command", tags=["Ops Infra"])
def ops_infra_command(req: OpsInfraCommandRequest,
                      project: Project = Depends(get_project_or_404),
                      db: Session = Depends(get_db),
                      _ = Depends(get_api_key)):
    commands = {
        "build": "docker compose build",
        "up": "docker compose up -d",
        "down": "docker compose down",
        "restart": "docker compose restart",
        "logs": "docker compose logs --tail=120",
        "ps": "docker compose ps",
    }
    if req.action not in commands:
        raise HTTPException(status_code=400, detail="Ação inválida para Ops Infra.")
    result = subprocess.run(commands[req.action], cwd=project.path, shell=True, text=True, capture_output=True, timeout=120)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_COMMAND", details=f"{commands[req.action]}\nExit: {result.returncode}"))
    db.commit()
    return {"status": "success" if result.returncode == 0 else "error", "command": commands[req.action], "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

@app.post("/api/projects/{project_id}/ops-infra/remote-command", tags=["Ops Infra"])
def ops_infra_remote_command(req: OpsInfraCommandRequest,
                             project: Project = Depends(get_project_or_404),
                             db: Session = Depends(get_db),
                             _ = Depends(get_api_key)):
    commands = {
        "build": "docker compose build",
        "up": "docker compose up -d",
        "down": "docker compose down",
        "restart": "docker compose restart",
        "logs": "docker compose logs --tail=120",
        "ps": "docker compose ps",
    }
    if req.action not in commands:
        raise HTTPException(status_code=400, detail="Ação inválida para Ops Infra.")
    access = _ops_read_vm_access(project.path, public=False)
    if not access.get("host") or not access.get("user") or not access.get("app_path"):
        raise HTTPException(status_code=400, detail="Configure VM / Acesso antes de executar comandos remotos.")
    remote_command = f"cd {_ops_shell_quote(access['app_path'])} && {commands[req.action]}"
    result = _ops_run_ssh(access, remote_command, timeout=180 if req.action in ["build", "up"] else 90)
    db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_REMOTE_COMMAND", details=f"{commands[req.action]} em {access['host']}:{access['app_path']}\nExit: {result['exit_code']}"))
    db.commit()
    return result

# --- ENDPOINTS DO SPEC-DRIVEN DEVELOPMENT (SDD) ---

def _sdd_documents_dir(project: Project) -> str:
    docs_dir = os.path.join(project.path, ".documents")
    os.makedirs(docs_dir, exist_ok=True)
    return docs_dir

def _qa_annotations_path(project: Project) -> str:
    qa_dir = os.path.join(project.path, ".documents", "qa")
    os.makedirs(qa_dir, exist_ok=True)
    return os.path.join(qa_dir, "annotations.json")

def _qa_evidence_dir(project: Project) -> str:
    evidence_dir = os.path.join(project.path, ".documents", "qa", "evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    return evidence_dir

def _store_qa_screenshot(project: Project, annotation_id: str, data_url: Optional[str]) -> dict:
    if not data_url or not data_url.startswith("data:image/"):
        return {}
    header, _, payload = data_url.partition(",")
    if not payload:
        return {}
    mime = header.split(";", 1)[0].replace("data:", "").lower()
    extension = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(mime)
    if not extension:
        return {}
    try:
        image_bytes = base64.b64decode(payload, validate=False)
    except Exception:
        return {}
    filename = f"{re.sub(r'[^A-Za-z0-9_-]', '_', annotation_id)}.{extension}"
    path = os.path.join(_qa_evidence_dir(project), filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return {
        "screenshot": None,
        "screenshot_file": filename,
        "screenshot_mime": mime,
    }

def _externalize_qa_screenshots(project: Project, annotations: list) -> bool:
    changed = False
    for item in annotations:
        screenshot = item.get("screenshot")
        if isinstance(screenshot, str) and screenshot.startswith("data:image/"):
            annotation_id = item.get("id") or f"QA-{secrets.token_hex(4).upper()}"
            item["id"] = annotation_id
            stored = _store_qa_screenshot(project, annotation_id, screenshot)
            if stored:
                item.update(stored)
                changed = True
    return changed

def _qa_screenshot_url(project: Project, item: dict) -> str:
    filename = item.get("screenshot_file")
    if filename:
        return f"/api/projects/{project.id}/qa/evidence/{filename}"
    screenshot = item.get("screenshot")
    return screenshot if isinstance(screenshot, str) else ""

def _qa_public_annotation(project: Project, item: dict) -> dict:
    public = dict(item)
    public["screenshot"] = _qa_screenshot_url(project, item)
    return public

def _read_qa_annotations(project: Project) -> list:
    path = _qa_annotations_path(project)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            annotations = data if isinstance(data, list) else []
            if _externalize_qa_screenshots(project, annotations):
                _write_qa_annotations(project, annotations)
            return annotations
    except Exception:
        return []

def _write_qa_annotations(project: Project, annotations: list):
    path = _qa_annotations_path(project)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)

def _qa_filtered_annotations(project: Project, status_filter: Optional[str] = None) -> list:
    annotations = _read_qa_annotations(project)
    if status_filter:
        annotations = [item for item in annotations if item.get("status") == status_filter]
    annotations.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return annotations

def _run_git_metrics_command(project_path: str, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""

def _format_duration_hours(hours: Optional[float]) -> str:
    if hours is None:
        return "Sem dados"
    if hours < 1:
        return f"{max(1, round(hours * 60))} min"
    if hours < 24:
        return f"{hours:.1f} h"
    return f"{hours / 24:.1f} dias"

def _format_percent(value: Optional[float]) -> str:
    if value is None:
        return "Sem dados"
    return f"{round(value)}%"

def _parse_task_metrics(project_path: str) -> dict:
    task_path = os.path.join(project_path, ".documents", "task", "task.md")
    if not os.path.exists(task_path):
        return {"total": 0, "done": 0, "rate": None}
    try:
        with open(task_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return {"total": 0, "done": 0, "rate": None}
    tasks = re.findall(r"^\s*-\s*\[([ xX])\]\s*TASK-", content, re.MULTILINE)
    total = len(tasks)
    done = sum(1 for marker in tasks if marker.lower() == "x")
    return {"total": total, "done": done, "rate": (done / total * 100) if total else None}

def _classify_dora(deploy_frequency_weekly: float, failure_rate: Optional[float], lead_time_hours: Optional[float], mttr_hours: Optional[float]) -> str:
    score = 0
    if deploy_frequency_weekly >= 5:
        score += 2
    elif deploy_frequency_weekly >= 1:
        score += 1
    if lead_time_hours is not None:
        score += 2 if lead_time_hours <= 24 else 1 if lead_time_hours <= 168 else 0
    if failure_rate is not None:
        score += 2 if failure_rate <= 15 else 1 if failure_rate <= 30 else 0
    if mttr_hours is not None:
        score += 2 if mttr_hours <= 24 else 1 if mttr_hours <= 168 else 0
    if score >= 7:
        return "Alta performance"
    if score >= 4:
        return "Em evolução"
    return "Base inicial"

def _qa_status_label(status_value: str) -> str:
    return {
        "open": "Aberta",
        "reviewing": "Em revisão",
        "resolved": "Resolvida",
    }.get(status_value or "open", "Aberta")

def _qa_category_label(category_value: str) -> str:
    return {
        "functional": "Funcionais",
        "interface": "Interface",
        "content": "Conteúdo",
        "interaction": "Interação",
        "design": "Design",
        "structure": "Estrutura",
        "visual": "Visual",
    }.get(category_value or "functional", "Funcionais")

def _qa_export_rows(annotations: list) -> list:
    rows = []
    for item in annotations:
        metadata = item.get("metadata") or {}
        viewport = item.get("viewport") or {}
        rows.append({
            "ID": item.get("id", ""),
            "Título": item.get("title", ""),
            "Descrição": item.get("description", ""),
            "Tipo": _qa_category_label(item.get("category", "")),
            "Severidade": item.get("severity", ""),
            "Status": _qa_status_label(item.get("status", "")),
            "URL": item.get("url", ""),
            "Seletor": item.get("selector", ""),
            "Viewport": f"{viewport.get('width', '')} x {viewport.get('height', '')}",
            "Aba": metadata.get("tabTitle", ""),
            "Texto selecionado": metadata.get("selectedText", ""),
            "Criado em": item.get("created_at", ""),
            "Atualizado em": item.get("updated_at", ""),
        })
    return rows

def _xlsx_col_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name

def _xlsx_cell(value) -> str:
    value = "" if value is None else str(value)
    return f'<c t="inlineStr"><is><t>{xml_escape(value)}</t></is></c>'

def _build_qa_xlsx(annotations: list) -> bytes:
    rows = _qa_export_rows(annotations)
    headers = list(rows[0].keys()) if rows else ["ID", "Título", "Descrição", "Severidade", "Status", "URL", "Seletor", "Viewport", "Aba", "Texto selecionado", "Criado em", "Atualizado em"]
    sheet_rows = []
    sheet_rows.append("<row>" + "".join(_xlsx_cell(header) for header in headers) + "</row>")
    for row in rows:
        sheet_rows.append("<row>" + "".join(_xlsx_cell(row.get(header, "")) for header in headers) + "</row>")
    cols = "".join(f'<col min="{i}" max="{i}" width="{min(max(len(header) + 4, 14), 42)}" customWidth="1"/>' for i, header in enumerate(headers, 1))
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<cols>{cols}</cols><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="QA Annotations" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()

def _pdf_hex_text(text: str) -> str:
    return (b"\xfe\xff" + (text or "").encode("utf-16-be", errors="replace")).hex().upper()

def _pdf_escape_stream(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def _pdf_safe_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return normalized.encode("ascii", errors="ignore").decode("ascii")

def _qa_screenshot_to_pdf_image(data_url: Optional[str]) -> Optional[dict]:
    if not data_url or not data_url.startswith("data:image/"):
        return None
    header, _, payload = data_url.partition(",")
    if not payload:
        return None
    media_type = header.split(";", 1)[0].lower()
    if media_type not in {"data:image/jpeg", "data:image/jpg"}:
        return None
    try:
        image_bytes = base64.b64decode(payload, validate=False)
        width, height = _jpeg_dimensions(image_bytes)
    except Exception:
        return None
    if not width or not height:
        return None
    return {
        "bytes": image_bytes,
        "width": width,
        "height": height,
    }

def _qa_annotation_pdf_image(project: Project, item: dict) -> Optional[dict]:
    filename = item.get("screenshot_file")
    if filename:
        safe_name = os.path.basename(filename)
        path = os.path.join(_qa_evidence_dir(project), safe_name)
        if not os.path.exists(path) or not safe_name.lower().endswith((".jpg", ".jpeg")):
            return None
        try:
            with open(path, "rb") as f:
                image_bytes = f.read()
            width, height = _jpeg_dimensions(image_bytes)
        except Exception:
            return None
        if not width or not height:
            return None
        return {
            "bytes": image_bytes,
            "width": width,
            "height": height,
        }
    return _qa_screenshot_to_pdf_image(item.get("screenshot"))

def _jpeg_dimensions(image_bytes: bytes) -> tuple[int, int]:
    index = 2
    length = len(image_bytes)
    if length < 4 or image_bytes[:2] != b"\xff\xd8":
        return 0, 0
    while index < length:
        if image_bytes[index] != 0xFF:
            index += 1
            continue
        while index < length and image_bytes[index] == 0xFF:
            index += 1
        if index >= length:
            break
        marker = image_bytes[index]
        index += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > length:
            break
        segment_length = int.from_bytes(image_bytes[index:index + 2], "big")
        if segment_length < 2 or index + segment_length > length:
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if segment_length >= 7:
                height = int.from_bytes(image_bytes[index + 3:index + 5], "big")
                width = int.from_bytes(image_bytes[index + 5:index + 7], "big")
                return width, height
            break
        index += segment_length
    return 0, 0

def _pdf_stream_object(stream: str) -> bytes:
    stream_bytes = stream.encode("utf-8")
    return f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream"

def _pdf_image_object(image: dict) -> bytes:
    image_bytes = image["bytes"]
    dictionary = (
        f"<< /Type /XObject /Subtype /Image /Width {image['width']} /Height {image['height']} "
        "/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
        f"/Length {len(image_bytes)} >>\nstream\n"
    ).encode("ascii")
    return dictionary + image_bytes + b"\nendstream"

def _build_qa_pdf(annotations: list, project: Project) -> bytes:
    project_name = project.name
    rows = _qa_export_rows(annotations)
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_refs = []

    def add_page(lines: list[str], image: Optional[dict] = None):
        image_name = None
        image_obj_no = None
        stream_parts = ["BT", "/F1 10 Tf"]
        y = 800
        for line in lines:
            safe = _pdf_escape_stream(_pdf_safe_text(line[:135]))
            stream_parts.append(f"1 0 0 1 50 {y} Tm ({safe}) Tj")
            y -= 16
        stream_parts.append("ET")
        if image:
            image_name = f"Im{len(page_refs) + 1}"
            image_obj_no = len(objects) + 1
            objects.append(_pdf_image_object(image))
            max_width = 495
            max_height = 430
            scale = min(max_width / image["width"], max_height / image["height"], 1)
            display_width = image["width"] * scale
            display_height = image["height"] * scale
            image_y = max(56, y - display_height - 16)
            stream_parts.extend([
                "q",
                f"{display_width:.2f} 0 0 {display_height:.2f} 50 {image_y:.2f} cm",
                f"/{image_name} Do",
                "Q",
            ])
        content_obj_no = len(objects) + 1
        objects.append(_pdf_stream_object("\n".join(stream_parts)))
        page_obj_no = len(objects) + 1
        xobject = f" /XObject << /{image_name} {image_obj_no} 0 R >>" if image_name and image_obj_no else ""
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >>{xobject} >> "
            f"/Contents {content_obj_no} 0 R >>"
        )
        objects.append(page.encode("ascii"))
        page_refs.append(f"{page_obj_no} 0 R")

    add_page([
        f"Relatório QA - {project_name}",
        f"Gerado em {datetime.utcnow().isoformat()}Z",
        f"Total de anotações: {len(rows)}",
        "",
        "As evidencias visuais aparecem nas paginas de cada anotacao quando existe print anexado.",
    ] if rows else [
        f"Relatório QA - {project_name}",
        f"Gerado em {datetime.utcnow().isoformat()}Z",
        "Total de anotações: 0",
        "",
        "Nenhuma anotação QA encontrada.",
    ])

    for item, row in zip(annotations, rows):
        image = _qa_annotation_pdf_image(project, item)
        lines = [
            f"{row['ID']} | {row['Status']} | {row['Severidade']}",
            f"Tipo: {row['Tipo']}",
            row["Título"],
            f"URL: {row['URL']}",
            f"Seletor: {row['Seletor']}",
            f"Descrição: {row['Descrição']}",
            "",
            "Evidencia visual:" if image else "Evidencia visual: sem print anexado ou formato nao suportado no PDF.",
        ]
        add_page(lines, image)

    objects[1] = f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {len(page_refs)} >>".encode("ascii")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        if isinstance(obj, bytes):
            pdf.extend(f"{number} 0 obj\n".encode("ascii"))
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        else:
            pdf.extend(f"{number} 0 obj\n{obj}\nendobj\n".encode("utf-8"))
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    return bytes(pdf)

@app.get("/api/projects/{project_id}/qa/annotations", tags=["QA"])
def list_qa_annotations(
    status_filter: Optional[str] = Query(None, alias="status"),
    project: Project = Depends(get_project_or_404)
):
    """Lista anotações de QA capturadas pela extensão ou pela interface."""
    annotations = _read_qa_annotations(project)
    if status_filter:
        annotations = [item for item in annotations if item.get("status") == status_filter]
    annotations.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"annotations": [_qa_public_annotation(project, item) for item in annotations], "total": len(annotations)}

@app.get("/api/projects/{project_id}/qa/evidence/{filename}", tags=["QA"])
def get_qa_evidence(filename: str, project: Project = Depends(get_project_or_404)):
    """Serve a evidência visual de uma anotação QA sem manter base64 no JSON."""
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nome de evidência inválido.")
    path = os.path.join(_qa_evidence_dir(project), safe_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Evidência QA não encontrada.")
    return FileResponse(path)

@app.get("/api/projects/{project_id}/qa/export.xlsx", tags=["QA"])
def export_qa_annotations_xlsx(status_filter: Optional[str] = Query(None, alias="status"), project: Project = Depends(get_project_or_404)):
    annotations = _qa_filtered_annotations(project, status_filter)
    content = _build_qa_xlsx(annotations)
    filename = f"qa-annotations-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/projects/{project_id}/qa/export.pdf", tags=["QA"])
def export_qa_annotations_pdf(status_filter: Optional[str] = Query(None, alias="status"), project: Project = Depends(get_project_or_404)):
    annotations = _qa_filtered_annotations(project, status_filter)
    content = _build_qa_pdf(annotations, project)
    filename = f"qa-annotations-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.post("/api/projects/{project_id}/qa/text/polish", tags=["QA"])
def polish_qa_text(payload: QaTextPolishRequest, project: Project = Depends(get_project_or_404), _ = Depends(get_api_key)):
    """Reescreve título ou descrição de uma anotação QA usando a IA configurada no Act IA."""
    original = (payload.text or "").strip()
    if not original:
        raise HTTPException(status_code=400, detail="Texto obrigatório.")

    config = agent.load_agent_config()
    provider = config.get("provider")
    model = config.get("model")
    api_key = config.get("api_key")
    if not provider or not model or not api_key:
        raise HTTPException(status_code=400, detail="IA não configurada no Agente IA.")

    mode = "title" if payload.mode == "title" else "description"
    system_prompt = (
        "Voce e um revisor de texto para anotacoes de QA em portugues do Brasil.\n"
        "Corrija erros de digitacao, gramatica, acentuacao e clareza sem mudar a intencao tecnica.\n"
        "Nao invente contexto, nao adicione detalhes que nao estejam no texto e nao explique.\n"
        "NAO resuma a descricao. Preserve todos os detalhes uteis para um desenvolvedor entender e corrigir o problema.\n"
        "Responda exclusivamente em JSON valido.\n"
        "Formato obrigatorio: {\"text\":\"texto revisado\"}.\n"
        "Se o modo for title, gere um titulo curto, objetivo, com no maximo 72 caracteres.\n"
        "Se o modo for description, reescreva como uma anotacao tecnica clara para QA, mantendo problema, local, comportamento esperado, evidencia e impacto quando existirem.\n"
        "Para description, prefira 2 a 5 linhas curtas. Se o texto tiver informacoes suficientes, use este formato:\n"
        "Problema: ...\n"
        "Onde ocorre: ...\n"
        "Esperado: ...\n"
        "Evidencia: ...\n"
        "Se algum campo nao estiver no texto, nao invente; apenas omita.\n"
        "Exemplo: 'Retirar essas inforções que aparecem na lsita' vira 'Problema: Retirar as informações que aparecem na lista.'.\n"
    )
    user_prompt = (
        f"Modo: {mode}\n"
        f"Projeto: {project.name}\n"
        f"Contexto: {(payload.context or '').strip()[:500]}\n"
        f"Texto original:\n{original}"
    )

    try:
        raw_resp = agent.call_llm(provider, model, api_key, [{"role": "user", "content": user_prompt}], system_prompt)
        parsed = agent.extract_json(raw_resp)
        text = str(parsed.get("text") or "").strip()
        if not text:
            raise ValueError("Resposta sem campo text.")
        if mode == "title":
            text = text.replace("\n", " ").strip().rstrip(".")
            text = text[:72].strip()
        return {"status": "success", "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao reescrever texto com IA: {str(e)}")

@app.post("/api/projects/{project_id}/qa/annotations", tags=["QA"])
def create_qa_annotation(payload: QaAnnotationInput, project: Project = Depends(get_project_or_404)):
    """Cria uma anotação de QA para o projeto ativo."""
    now = datetime.utcnow().isoformat() + "Z"
    severity = payload.severity if payload.severity in {"low", "medium", "high", "critical"} else "medium"
    category = payload.category if payload.category in {"functional", "interface", "content", "interaction", "design", "structure", "visual"} else "functional"
    status_value = payload.status if payload.status in {"open", "reviewing", "resolved"} else "open"
    annotation_id = f"QA-{secrets.token_hex(4).upper()}"
    screenshot_data = _store_qa_screenshot(project, annotation_id, payload.screenshot)
    annotation = {
        "id": annotation_id,
        "title": payload.title.strip()[:160] or "Anotação QA",
        "description": payload.description.strip(),
        "url": payload.url.strip(),
        "category": category,
        "severity": severity,
        "status": status_value,
        "selector": payload.selector.strip(),
        "viewport": payload.viewport or {},
        "browser": payload.browser.strip(),
        "screenshot": None,
        **screenshot_data,
        "metadata": payload.metadata or {},
        "created_at": now,
        "updated_at": now,
    }
    annotations = _read_qa_annotations(project)
    annotations.append(annotation)
    _write_qa_annotations(project, annotations)
    return {"status": "success", "annotation": _qa_public_annotation(project, annotation)}

@app.patch("/api/projects/{project_id}/qa/annotations/{annotation_id}", tags=["QA"])
def update_qa_annotation_status(
    annotation_id: str,
    payload: QaAnnotationStatusUpdate,
    project: Project = Depends(get_project_or_404)
):
    """Atualiza o status de uma anotação de QA."""
    if payload.status not in {"open", "reviewing", "resolved"}:
        raise HTTPException(status_code=400, detail="Status inválido. Use open, reviewing ou resolved.")
    annotations = _read_qa_annotations(project)
    for item in annotations:
        if item.get("id") == annotation_id:
            item["status"] = payload.status
            item["updated_at"] = datetime.utcnow().isoformat() + "Z"
            _write_qa_annotations(project, annotations)
            return {"status": "success", "annotation": _qa_public_annotation(project, item)}
    raise HTTPException(status_code=404, detail="Anotação QA não encontrada.")

@app.delete("/api/projects/{project_id}/qa/annotations/{annotation_id}", tags=["QA"])
def delete_qa_annotation(annotation_id: str, project: Project = Depends(get_project_or_404)):
    """Remove uma anotação de QA."""
    annotations = _read_qa_annotations(project)
    removed = next((item for item in annotations if item.get("id") == annotation_id), None)
    next_annotations = [item for item in annotations if item.get("id") != annotation_id]
    if len(next_annotations) == len(annotations):
        raise HTTPException(status_code=404, detail="Anotação QA não encontrada.")
    if removed and removed.get("screenshot_file"):
        evidence_path = os.path.join(_qa_evidence_dir(project), os.path.basename(removed["screenshot_file"]))
        if os.path.exists(evidence_path):
            os.remove(evidence_path)
    _write_qa_annotations(project, next_annotations)
    return {"status": "success", "deleted_id": annotation_id}

@app.get("/api/projects/{project_id}/engineering-metrics/dora", tags=["Engineering Metrics"])
def get_engineering_metrics_dora(
    days: int = Query(30, ge=1, le=365),
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
):
    """Calcula uma leitura inicial de métricas DORA a partir de Git, logs, QA e tasks."""
    since = datetime.utcnow() - timedelta(days=days)
    deploy_logs = db.query(ActivityLog).filter(
        ActivityLog.project_id == project.id,
        ActivityLog.timestamp >= since,
        ActivityLog.action_type.in_(["GIT_DEPLOY", "GIT_PUSH", "OPS_INFRA_DOMAIN", "OPS_INFRA_ARTIFACTS"]),
    ).order_by(ActivityLog.timestamp.asc()).all()
    operational_logs = db.query(ActivityLog).filter(
        ActivityLog.project_id == project.id,
        ActivityLog.timestamp >= since,
    ).order_by(ActivityLog.timestamp.desc()).limit(200).all()

    git_since = since.strftime("%Y-%m-%d")
    commit_lines = _run_git_metrics_command(project.path, ["log", f"--since={git_since}", "--pretty=%ct"]).splitlines()
    commit_timestamps = []
    for line in commit_lines:
        try:
            commit_timestamps.append(datetime.utcfromtimestamp(int(line.strip())))
        except Exception:
            continue
    commit_timestamps.sort()

    lead_time_hours = None
    lead_samples = []
    if deploy_logs and commit_timestamps:
        for deploy in deploy_logs:
            previous_commits = [ts for ts in commit_timestamps if ts <= deploy.timestamp]
            if previous_commits:
                lead_samples.append((deploy.timestamp - previous_commits[-1]).total_seconds() / 3600)
        if lead_samples:
            lead_time_hours = sum(lead_samples) / len(lead_samples)

    annotations = _read_qa_annotations(project)
    period_annotations = [item for item in annotations if str(item.get("created_at", "")) >= since.isoformat()]
    critical_open = [
        item for item in period_annotations
        if item.get("status", "open") != "resolved" and item.get("severity") in {"high", "critical"}
    ]
    resolved = [item for item in period_annotations if item.get("status") == "resolved"]
    open_items = [item for item in period_annotations if item.get("status", "open") == "open"]
    reviewing_items = [item for item in period_annotations if item.get("status") == "reviewing"]

    failure_markers = ("fail", "erro", "error", "rollback", "abort", "conflito", "conflict", "hotfix", "Exit: 1")
    failure_logs = [
        log for log in operational_logs
        if any(marker.lower() in f"{log.action_type} {log.details or ''}".lower() for marker in failure_markers)
    ]
    failures = len(failure_logs) + len(critical_open)
    deploy_count = len(deploy_logs)
    failure_rate = (failures / deploy_count * 100) if deploy_count else (100 if failures else None)

    mttr_hours = None
    recovery_samples = []
    for item in resolved:
        created = str(item.get("created_at", "")).replace("Z", "")
        updated = str(item.get("updated_at", "")).replace("Z", "")
        try:
            recovery_samples.append((datetime.fromisoformat(updated) - datetime.fromisoformat(created)).total_seconds() / 3600)
        except Exception:
            continue
    if recovery_samples:
        mttr_hours = sum(recovery_samples) / len(recovery_samples)

    task_metrics = _parse_task_metrics(project.path)
    deploy_frequency_weekly = deploy_count / max(days / 7, 1 / 7)
    performance = _classify_dora(deploy_frequency_weekly, failure_rate, lead_time_hours, mttr_hours)
    risk_level = "Baixo" if not critical_open and (failure_rate is None or failure_rate <= 15) else "Médio" if len(critical_open) <= 2 else "Alto"

    return {
        "period_days": days,
        "performance_level": performance,
        "risk_level": risk_level,
        "risk_note": f"{len(critical_open)} QA crítico/alto aberto e {len(failure_logs)} log(s) com falha.",
        "metrics": {
            "deploy_frequency": {
                "value": deploy_frequency_weekly,
                "label": f"{deploy_frequency_weekly:.1f}/semana",
                "context": f"{deploy_count} deploy(s) nos últimos {days} dias",
            },
            "lead_time": {"value_hours": lead_time_hours, "label": _format_duration_hours(lead_time_hours)},
            "change_failure_rate": {"value": failure_rate, "label": _format_percent(failure_rate)},
            "mttr": {"value_hours": mttr_hours, "label": _format_duration_hours(mttr_hours)},
            "success_rate": {
                "value": task_metrics["rate"],
                "label": _format_percent(task_metrics["rate"]),
                "done": task_metrics["done"],
                "total": task_metrics["total"],
            },
        },
        "signals": {
            "commits": len(commit_timestamps),
            "deploys": deploy_count,
            "qa_open": len(open_items),
            "qa_reviewing": len(reviewing_items),
            "qa_resolved": len(resolved),
            "critical_open": len(critical_open),
            "failure_logs": len(failure_logs),
            "tasks_total": task_metrics["total"],
            "tasks_done": task_metrics["done"],
        },
        "recent_deploys": [
            {"timestamp": log.timestamp.isoformat() + "Z", "type": log.action_type, "details": log.details or ""}
            for log in deploy_logs[-8:]
        ],
    }


@app.get("/api/projects/{project_id}/engineering-metrics/reports/{report_type}", tags=["Engineering Metrics"])
def get_engineering_metrics_report(
    report_type: str,
    project: Project = Depends(get_project_or_404)
):
    """Retorna relatórios Markdown de auditoria usados pela página Engineering Metrics."""
    report_map = {
        "prod-readiness": {
            "title": "Prod-Ready Validator",
            "filepath": os.path.join(".documents", "prod-readiness", "prod-readiness-report.md"),
            "message": "Nenhum relatório Production-Ready encontrado. Execute o GPT Action Prod-Ready Validator para gerar este arquivo.",
        },
        "security": {
            "title": "Security Rules",
            "filepath": os.path.join(".documents", "security", "security-review-report.md"),
            "message": "Nenhum relatório de Security Review encontrado. Execute o GPT Action Security Rules para gerar este arquivo.",
        },
    }
    config = report_map.get(report_type)
    if not config:
        raise HTTPException(status_code=404, detail="Tipo de relatório não suportado.")

    sync_project_system_files(project.path)
    full_path = vcs.get_safe_path(project.path, config["filepath"])
    if not os.path.exists(full_path):
        return {
            "status": "empty",
            "title": config["title"],
            "filepath": config["filepath"].replace("\\", "/"),
            "content": "",
            "message": config["message"],
            "updated_at": None,
        }

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "status": "success",
        "title": config["title"],
        "filepath": config["filepath"].replace("\\", "/"),
        "content": content,
        "message": "",
        "updated_at": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
    }

def _sdd_charter_path(project: Project) -> str:
    return os.path.join(_sdd_documents_dir(project), "project-charter.md")

SDD_PROJECT_DOCUMENTS = {
    "design": {
        "dir": "design",
        "filename": "design.md",
        "title": "Design — Planejamento Técnico do Projeto",
    },
    "dri": {
        "dir": "dri",
        "filename": "dri.md",
        "title": "DRI — Documento de Requisito de Interface do Projeto",
    },
    "task": {
        "dir": "task",
        "filename": "task.md",
        "title": "Task List — Tarefas do Projeto",
    },
    "task_details": {
        "dir": "task",
        "filename": "task.details.md",
        "title": "Task Details — Plano Detalhado da Task Atual",
    },
}

def _sdd_req_pai_template(req_id: str = "REQ-01", title: str = "Título do Macro Requisito") -> str:
    return (
        f"# {req_id} — {title}\n\n"
        "## 1. Identificação\n\n"
        "| Campo | Valor |\n"
        "|---|---|\n"
        f"| ID | {req_id} |\n"
        f"| Título | {title} |\n"
        "| Projeto | A definir |\n"
        "| Tipo | Requisito Macro |\n"
        "| Prioridade | Alta |\n"
        "| Status | Levantado |\n"
        "| Fonte | .documents/project-charter.md |\n\n"
        "## 2. Objetivo\n\n"
        "Descreva o objetivo macro da funcionalidade.\n\n"
        "## 3. Escopo Macro\n\n"
        "- Escopo 1\n"
        "- Escopo 2\n\n"
        "## 4. Requisitos Funcionais Vinculados\n\n"
        "| ID | Requisito Funcional | Arquivo | Status |\n"
        "|---|---|---|---|\n"
        f"| RF-01-01 | Primeiro fluxo de {title} | .documents/functional-requirements/RF-01-01.md | Levantado |\n\n"
        "## 5. Fontes de Dados\n\n"
        "| ID | Fonte | Uso no processo |\n"
        "|---|---|---|\n"
        "| FD-01-01 | Banco de Dados / API | Descrição |\n\n"
        "## 6. Regras Gerais\n\n"
        "| ID | Regra |\n"
        "|---|---|\n"
        "| RN-01-01 | Regra macro 1 |\n\n"
        "## 7. Critérios de Aceite Macro\n\n"
        "- [ ] Critério 1.\n\n"
        "## 8. Fora do Escopo\n\n"
        "- Item fora do escopo.\n\n"
        "## 9. Rastreabilidade\n\n"
        "| Origem | Referência |\n"
        "|---|---|\n"
        "| TAP | .documents/project-charter.md |\n"
    )

def _sdd_rf_template(rf_id: str = "RF-01-01", req_id: str = "REQ-01", title: str = "Título do Requisito Funcional") -> str:
    return (
        f"# {rf_id} — {title}\n\n"
        "## 1. Identificação\n\n"
        "| Campo | Valor |\n"
        "|---|---|\n"
        f"| ID | {rf_id} |\n"
        f"| REQ Pai | {req_id} |\n"
        f"| Título | {title} |\n"
        "| Tipo | Requisito funcional |\n"
        "| Prioridade | Alta |\n"
        "| Status | Detalhado |\n\n"
        "## 2. Objetivo\n\n"
        "Objetivo específico deste fluxo.\n\n"
        "## 3. Descrição Funcional\n\n"
        "Descrição detalhada de como o fluxo funciona.\n\n"
        "## 4. História do Usuário\n\n"
        "Como [usuário], quero [ação], para que [benefício].\n\n"
        "## 5. Regras de Negócio\n\n"
        "| ID | Regra |\n"
        "|---|---|\n"
        f"| RN-{rf_id}-01 | Regra específica 1 |\n\n"
        "## 6. Dados Necessários\n\n"
        "| Campo | Tipo | Obrigatório | Descrição |\n"
        "|---|---|---|---|\n"
        "| campo_exemplo | string | Sim | Descrição do dado |\n\n"
        "## 7. Critérios de Aceite\n\n"
        "- [ ] Critério de aceite específico 1.\n\n"
        "## 8. Fora do Escopo\n\n"
        "- Item fora do escopo deste RF.\n\n"
        "## 9. Próximo Artefato\n\n"
        "| Tipo | Arquivo |\n"
        "|---|---|\n"
        f"| DRI | ../dri/DRI-{rf_id}.md |\n"
        f"| Task List | ../task-lists/TASKLIST-{rf_id}.md |\n"
    )

def _dri_template() -> str:
    return (
        "## RI-XX - Nome da Interface\n\n"
        "### 1. Identificação da Interface\n\n"
        "| Campo | Valor |\n"
        "| --- | --- |\n"
        "| Código | RI-XX |\n"
        "| Nome da interface | [Ex.: Página Meu Perfil] |\n"
        "| Módulo | [Ex.: Profissionais / Conta] |\n"
        "| RF relacionado | [Ex.: REQ-0000] |\n"
        "| SubRFs relacionados | [Ex.: SubRF-01.01] |\n"
        "| Tipo de interface | Página / Modal / Drawer / Formulário / Grid / Dashboard / Detalhe |\n"
        "| Perfil de usuário | [Perfil principal de usuário] |\n"
        "| Dispositivo prioritário | Desktop / Mobile / Responsivo |\n"
        "| Objetivo da tela | [Resultado operacional esperado] |\n\n"
        "### 2. Objetivo da Interface\n\n"
        "[Descreva o propósito da tela, quais dados ou decisões ela sustenta e como se conecta ao REQ relacionado.]\n\n"
        "### 3. Contexto de Uso\n\n"
        "| Item | Descrição |\n"
        "| --- | --- |\n"
        "| Quem usa | [Perfil principal de usuário] |\n"
        "| Quando usa | [Momento do fluxo ou rotina operacional] |\n"
        "| Por que usa | [Motivação e necessidade do usuário] |\n"
        "| Gatilho de acesso | [Menu, onboarding, notificação, link, workflow, ação anterior] |\n"
        "| Resultado esperado | [Estado desejado após uso da interface] |\n\n"
        "### 4. Arquitetura da Informação\n\n"
        "| Ordem | Seção | Objetivo | Tipo de componente |\n"
        "| --- | --- | --- | --- |\n"
        "| 1 | [Nome da seção] | [Objetivo funcional da seção] | [Header, formulário, lista, tabela, card, painel] |\n\n"
        "### 5. Mapa de Componentes\n\n"
        "| Componente | Tipo | Obrigatório | Editável | Comportamento esperado |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| [Nome do campo/ação] | [Input, select, badge, button] | Sim/Não | Sim/Não | [Validação, máscara, permissão, estado ou regra de interação] |\n\n"
        "### 6. Regras de Exibição\n\n"
        "| Código | Regra | Comportamento |\n"
        "| --- | --- | --- |\n"
        "| RI-RG-01 | [Nome da regra visual ou condicional] | [Comportamento esperado na interface] |\n\n"
        "### 7. Estados da Interface\n\n"
        "| Estado | Descrição | Comportamento visual |\n"
        "| --- | --- | --- |\n"
        "| Loading | Dados sendo carregados. | Skeleton, spinner ou placeholder consistente. |\n"
        "| Empty | Não há dados ou configuração iniciada. | Mensagem orientativa e CTA pertinente. |\n"
        "| View | Dados exibidos para leitura. | Campos organizados e ações secundárias discretas. |\n"
        "| Edit | Usuário editando informações. | Campos habilitados e botões de ação visíveis. |\n"
        "| Saving | Salvamento em andamento. | Ação principal desabilitada com feedback. |\n"
        "| Success | Operação concluída. | Toast ou mensagem de confirmação. |\n"
        "| Error | Falha ao carregar, validar ou salvar. | Mensagem clara e ação de nova tentativa. |\n"
        "| Read-only | Usuário sem permissão de edição. | Campos bloqueados e aviso de restrição. |\n\n"
        "### 8. Fluxo de Interação\n\n"
        "| Ação do usuário | Resposta da interface | Resultado esperado |\n"
        "| --- | --- | --- |\n"
        "| [Acessar interface] | [Sistema carrega dados e estados] | [Tela exibe informações atuais] |\n\n"
        "### 9. Mapeamento de Dados\n\n"
        "| Campo na tela | Nome técnico | Origem | Editável | Obrigatório |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| [Campo] | [snake_case] | [Collection, API, sistema, usuário] | Sim/Não | Sim/Não |\n\n"
        "### 10. Hierarquia Visual\n\n"
        "**Prioridade Alta:** [Informações críticas, status, ação principal, alertas e pendências.]\n\n"
        "**Prioridade Média:** [Dados de apoio, seções recorrentes, filtros, grupos secundários.]\n\n"
        "**Prioridade Baixa:** [Informações auxiliares, histórico, textos explicativos e suporte.]\n\n"
        "### 11. Microcopy da Interface\n\n"
        "| Elemento | Texto sugerido | Observação |\n"
        "| --- | --- | --- |\n"
        "| Título da tela | [Texto objetivo e operacional] | [Evitar promessa genérica] |\n"
        "| Descrição curta | [Explicar a finalidade da tela] | [Uma ou duas frases no máximo] |\n"
        "| CTA principal | [Salvar alterações / Enviar para análise] | [Verbo de ação claro] |\n"
        "| Erro de validação | [Informe o ajuste necessário] | [Mensagem contextual] |\n"
        "| Toast de sucesso | [Alterações salvas com sucesso] | [Confirmação curta] |\n\n"
        "### 12. Responsividade\n\n"
        "| Contexto | Requisito |\n"
        "| --- | --- |\n"
        "| Desktop | [Layout, colunas, largura, painéis laterais, tabela ou formulário completo] |\n"
        "| Tablet | [Reorganização de colunas, navegação e ações] |\n"
        "| Mobile | [Ordem das seções, ações fixas, campos em uma coluna, estados críticos] |\n\n"
        "### 13. Acessibilidade\n\n"
        "| Aspecto | Requisito |\n"
        "| --- | --- |\n"
        "| Labels | [Todos os campos possuem label persistente e claro] |\n"
        "| Contraste | [Cores atendem leitura confortável e função semântica] |\n"
        "| Navegação por teclado | [Foco visível e ordem lógica] |\n"
        "| Mensagens de erro | [Erro próximo ao campo e linguagem acionável] |\n"
        "| Leitores de tela | [Nomes acessíveis, estados e regiões relevantes] |\n\n"
        "### 14. Critérios de Aceite da Interface\n\n"
        "| Código | Critério |\n"
        "| --- | --- |\n"
        "| CA-RI-01 | A interface deve exibir os dados necessários ao usuário autenticado conforme permissão. |\n"
        "| CA-RI-02 | A interface deve permitir edição apenas dos campos autorizados. |\n"
        "| CA-RI-03 | Campos obrigatórios devem exibir validação quando não preenchidos. |\n"
        "| CA-RI-04 | A ação principal deve responder aos estados de alteração, validação e salvamento. |\n"
        "| CA-RI-05 | Após sucesso, a interface deve confirmar a operação ao usuário. |\n"
        "| CA-RI-06 | Em caso de erro, a interface deve informar a falha e permitir nova tentativa. |\n"
        "| CA-RI-07 | A interface deve exibir status, pendências ou bloqueios relevantes. |\n"
        "| CA-RI-08 | A interface deve ser responsiva para desktop, tablet e mobile quando aplicável. |\n\n"
        "### 15. Lacunas e Premissas\n\n"
        "| Item | Tipo | Descrição |\n"
        "| --- | --- | --- |\n"
        "| 1 | Lacuna | [Informação ausente que impede decisão completa] |\n"
        "| 2 | Premissa | [Suposição usada para avançar o RI] |\n"
        "| 3 | Risco | [Risco de regra, dado, permissão ou experiência] |\n\n"
        "### 16. Fora do Escopo\n\n"
        "- [Item, comportamento, regra ou integração que não faz parte deste RI.]\n\n"
        "### 17. Possíveis Evoluções Futuras\n\n"
        "- [Melhoria futura, automação, componente avançado ou integração adicional.]\n"
    )

def _sdd_spec_dir(project: Project, create: bool = False) -> str:
    spec_dir = os.path.join(_sdd_documents_dir(project), "requirements")
    if create:
        os.makedirs(spec_dir, exist_ok=True)
    return spec_dir

def _sdd_strip_forbidden_req_sections(markdown: str) -> str:
    """Mantem o arquivo do REQ restrito ao Specify."""
    lines = (markdown or "").splitlines()
    kept = []
    skip = False
    forbidden = ("design", "planejamento", "dri", "documento de requisito de interface", "task list", "tasks", "tarefas", "execute", "implementação", "implementacao")

    for line in lines:
        heading = re.match(r"^(#{2,6})\s*(?:\d+\.?\s*)?(.+)$", line.strip())
        if heading:
            level = len(heading.group(1))
            normalized = heading.group(2).strip().lower()
            if level <= 2 and any(term in normalized for term in forbidden):
                skip = True
                continue
            if skip and level <= 2:
                skip = False
        if not skip:
            kept.append(line)

    cleaned = "\n".join(kept).strip()
    return cleaned + "\n" if cleaned else ""

def _sdd_project_document_path(project: Project, kind: str, create_dir: bool = False) -> str:
    config = SDD_PROJECT_DOCUMENTS.get(kind)
    if not config:
        raise HTTPException(status_code=400, detail="Documento Harness inválido.")
    doc_dir = os.path.join(_sdd_documents_dir(project), config["dir"])
    if create_dir:
        os.makedirs(doc_dir, exist_ok=True)
    return os.path.join(doc_dir, config["filename"])

SDD_TASK_CODE_FRAGMENT = r"TASK-(?:REQ-\d{2,6}|RF-\d{2,6}-\d{1,4}|QA-[A-Z0-9-]+)-\d{3}"
SDD_TASK_CODE_PATTERN = re.compile(rf"\b{SDD_TASK_CODE_FRAGMENT}\b", flags=re.IGNORECASE)
SDD_TASK_LINE_PATTERN = re.compile(
    rf"^({SDD_TASK_CODE_FRAGMENT})\s*:\s*-?\s*(.+)$",
    flags=re.IGNORECASE,
)


def _parse_sdd_task_line(line: str, line_index: int) -> Optional[dict]:
    checkbox_match = re.match(r"^\-\s*\[([ xX])\]\s*(.*)", (line or "").strip())
    if not checkbox_match:
        return None
    task_match = SDD_TASK_LINE_PATTERN.match(checkbox_match.group(2).strip())
    if not task_match:
        return None
    task_code = task_match.group(1).upper()
    task_title = task_match.group(2).strip()
    return {
        "id": line_index,
        "line_no": line_index + 1,
        "code": task_code,
        "title": task_title,
        "text": f"{task_code}: - {task_title}",
        "checked": checkbox_match.group(1).lower() == "x",
    }


def _remove_sdd_task_detail_section(details_path: str, task_code: str) -> bool:
    if not os.path.exists(details_path):
        return False

    with open(details_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    heading_pattern = re.compile(
        rf"^(#{{1,6}})\s+.*\b{re.escape(task_code)}\b.*$",
        flags=re.IGNORECASE,
    )
    start_index = -1
    heading_level = 0
    for index, line in enumerate(lines):
        match = heading_pattern.match(line.strip())
        if match:
            start_index = index
            heading_level = len(match.group(1))
            break

    if start_index < 0:
        return False

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        heading = re.match(r"^(#{1,6})\s+", lines[index].strip())
        if heading and len(heading.group(1)) <= heading_level:
            end_index = index
            break

    while start_index > 0 and not lines[start_index - 1].strip():
        start_index -= 1

    updated_lines = lines[:start_index] + lines[end_index:]
    with open(details_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
    return True

def _default_sdd_project_document(project: Project, kind: str) -> str:
    config = SDD_PROJECT_DOCUMENTS.get(kind)
    if not config:
        raise HTTPException(status_code=400, detail="Documento Harness inválido.")
    project_name = project.name or "Projeto"
    if kind == "design":
        return (
            f"# {config['title']}\n\n"
            f"## Projeto\n\n{project_name}\n\n"
            "## 1. Arquitetura Proposta\n\n"
            "Descreva as decisões técnicas, componentes impactados, dados, integrações, permissões, riscos e restrições do projeto.\n\n"
            "## 2. Fluxos Técnicos\n\n"
            "- \n\n"
            "## 3. APIs, Eventos e Contratos\n\n"
            "| Item | Contrato | Observação |\n"
            "| --- | --- | --- |\n"
            "| [Endpoint/evento] | [Entrada/saída] | [Risco ou dependência] |\n\n"
            "## 4. Dados e Persistência\n\n"
            "| Entidade | Origem | Persistência | Observação |\n"
            "| --- | --- | --- | --- |\n"
            "| [Entidade] | [UI/API/serviço] | [Banco/arquivo/cache] | [Regra] |\n\n"
            "## 5. Segurança e Permissões\n\n"
            "- \n\n"
            "## 6. Estratégia de Validação\n\n"
            "- \n"
        )
    if kind == "dri":
        return (
            f"# {config['title']}\n\n"
            f"## Projeto\n\n{project_name}\n\n"
            f"{_dri_template()}\n"
        )
    if kind == "task":
        return (
            f"# {config['title']}\n\n"
            f"## Projeto\n\n{project_name}\n\n"
            "## Task List - Tarefas\n\n"
            "> Use itens rastreáveis no formato `- [ ] TASK-RF-0001-01-001: - Título curto da tarefa.`\n"
            "> Não coloque plano detalhado aqui. Use `.documents/task/task.details.md` para o plano da task atual.\n\n"
            "- [ ] TASK-RF-0001-01-001: - Detalhar primeira tarefa do projeto.\n"
        )
    return (
        f"# {config['title']}\n\n"
        f"## Projeto\n\n{project_name}\n\n"
        "> Arquivo acumulativo. Não sobrescreva detalhes de tasks anteriores.\n"
        "> Para uma nova task, anexe uma nova seção `# TASK-RF-0001-01-000` ao final.\n"
        "> Para revisar uma task existente, atualize somente a seção daquela task.\n\n"
        "# TASK-RF-0001-01-001\n\n"
        "### Título\n\n"
        "Título curto da task.\n\n"
        "### Objetivo\n\n"
        "Descreva o objetivo da task atual.\n\n"
        "### História do usuário\n\n"
        "Descreva a história do usuário associada.\n\n"
        "### Escopo\n\n"
        "Detalhes do escopo desta task.\n\n"
        "### Regras de negócio\n\n"
        "Regras de negócio que se aplicam a esta task.\n\n"
        "### Critérios de aceite\n\n"
        "- [ ] Critério 1.\n\n"
        "### Dependências\n\n"
        "Dependências técnicas ou de negócio.\n\n"
        "### Definition of Done\n\n"
        "- [ ] Critérios de aceite atendidos.\n\n"
        "Para autorizar a execução de todas as tasks planejadas, responda: **\"Aprovado executar o pacote Harness\"**.\n"
    )

def _sdd_project_structure_status(project: Project) -> dict:
    spec_dir = _sdd_spec_dir(project)
    project_documents = {}
    for kind in SDD_PROJECT_DOCUMENTS:
        path = _sdd_project_document_path(project, kind)
        exists = os.path.exists(path)
        stat = os.stat(path) if exists else None
        project_documents[kind] = {
            "path": os.path.relpath(path, project.path).replace("\\", "/"),
            "exists": exists,
            "size_bytes": stat.st_size if stat else 0,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else None,
        }
    return {
        "documents_dir": ".documents",
        "spec_dir": ".documents/spec",
        "spec_dir_exists": os.path.exists(spec_dir),
        "project_documents": project_documents,
    }

def _sdd_ensure_project_structure(project: Project) -> dict:
    created = []
    _sdd_spec_dir(project, create=True)
    for kind, config in SDD_PROJECT_DOCUMENTS.items():
        path = _sdd_project_document_path(project, kind, create_dir=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write(_default_sdd_project_document(project, kind))
            created.append(os.path.relpath(path, project.path).replace("\\", "/"))
    return {"created": created, **_sdd_project_structure_status(project)}

def _default_sdd_charter(project: Project) -> str:
    project_name = project.name or "Projeto"
    return (
        f"# Termo de Abertura do Projeto - {project_name}\n\n"
        "## 1. Contexto\n\n"
        "Descreva o problema, oportunidade ou necessidade que justifica este projeto.\n\n"
        "## 2. Objetivo do Projeto\n\n"
        "Defina o resultado esperado em linguagem de negócio.\n\n"
        "## 3. Escopo Inicial\n\n"
        "### Dentro do escopo\n\n"
        "- \n\n"
        "### Fora do escopo\n\n"
        "- \n\n"
        "## 4. Stakeholders\n\n"
        "- Solicitante:\n"
        "- Usuários impactados:\n"
        "- Responsável técnico:\n\n"
        "## 5. Premissas e Restrições\n\n"
        "- \n\n"
        "## 6. Riscos Iniciais\n\n"
        "- \n\n"
        "## 7. Critérios de Sucesso\n\n"
        "- [ ] \n\n"
        "## 8. Próximo Passo\n\n"
        "A partir deste TAP, crie as especificações funcionais em Specify, Design, DRI, Task List e Execute.\n"
    )

@app.get("/api/projects/{project_id}/sdd/structure", tags=["Spec-Driven Development"])
def get_sdd_structure(project: Project = Depends(get_project_or_404)):
    """Reconhece a estrutura documental viva do Harness Engineering sem criar arquivos."""
    return {"status": "success", **_sdd_project_structure_status(project)}

@app.post("/api/projects/{project_id}/sdd/structure", tags=["Spec-Driven Development"])
def ensure_sdd_structure(
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Cria a estrutura documental viva do Harness Engineering quando ainda não existir."""
    try:
        result = _sdd_ensure_project_structure(project)
        db.add(ActivityLog(
            project_id=project.id,
            action_type="SDD_STRUCTURE_ENSURED",
            details=f"Estrutura Harness verificada/criada. Arquivos criados: {', '.join(result.get('created', [])) or 'nenhum'}"
        ))
        db.commit()
        return {"status": "success", **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao preparar estrutura Harness: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/project-documents/{kind}", tags=["Spec-Driven Development"])
def get_sdd_project_document(kind: str, project: Project = Depends(get_project_or_404)):
    """Retorna um documento vivo do Harness Engineering: design, dri, task ou task_details."""
    path = _sdd_project_document_path(project, kind)
    if not os.path.exists(path):
        return {
            "status": "empty",
            "kind": kind,
            "filepath": os.path.relpath(path, project.path).replace("\\", "/"),
            "content": _default_sdd_project_document(project, kind)
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "status": "success",
            "kind": kind,
            "filepath": os.path.relpath(path, project.path).replace("\\", "/"),
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler documento Harness: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/project-documents/{kind}", tags=["Spec-Driven Development"])
def save_sdd_project_document(
    kind: str,
    req: SddCharterSaveRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Salva um documento vivo do Harness Engineering: design, dri ou task."""
    path = _sdd_project_document_path(project, kind, create_dir=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(req.content)
        rel_path = os.path.relpath(path, project.path).replace("\\", "/")
        db.add(ActivityLog(
            project_id=project.id,
            action_type="SDD_PROJECT_DOCUMENT_SAVED",
            details=f"Documento Harness salvo: {rel_path}"
        ))
        db.commit()
        return {
            "status": "success",
            "kind": kind,
            "filepath": rel_path,
            "message": "Documento Harness salvo com sucesso."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar documento Harness: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/charter", tags=["Spec-Driven Development"])
def get_sdd_charter(project: Project = Depends(get_project_or_404)):
    """Retorna o Project Charter/TAP do projeto."""
    charter_path = _sdd_charter_path(project)
    if not os.path.exists(charter_path):
        return {
            "status": "empty",
            "filename": "project-charter.md",
            "content": _default_sdd_charter(project)
        }

    try:
        with open(charter_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "status": "success",
            "filename": "project-charter.md",
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler TAP do projeto: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/charter", tags=["Spec-Driven Development"])
def save_sdd_charter(
    req: SddCharterSaveRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Cria ou atualiza o Project Charter/TAP do projeto."""
    charter_path = _sdd_charter_path(project)
    try:
        with open(charter_path, "w", encoding="utf-8") as f:
            f.write(req.content)

        log = ActivityLog(
            project_id=project.id,
            action_type="SDD_CHARTER_SAVED",
            details="Project Charter/TAP salvo: project-charter.md"
        )
        db.add(log)
        db.commit()

        return {"status": "success", "filename": "project-charter.md", "message": "TAP salvo com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar TAP do projeto: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/generate-charter", tags=["Spec-Driven Development"])
def generate_sdd_charter(
    req: SddCharterGenerateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Gera o Project Charter/TAP do projeto usando IA."""
    config = agent.load_agent_config()
    provider = config.get("provider")
    model = config.get("model")
    api_key = config.get("api_key")

    if not api_key:
        raise HTTPException(status_code=400, detail="Chave de API da LLM não configurada no Agente IA.")

    title = req.title or project.name or "Projeto"
    system_prompt = (
        "Você é um Product Manager e Arquiteto de Software especialista em Project Charter/TAP.\n"
        "Gere um Termo de Abertura do Projeto em Markdown para orientar especificações funcionais futuras.\n"
        "O documento deve ser executivo, claro para pessoas leigas e útil para engenharia.\n\n"
        "Use obrigatoriamente esta estrutura de títulos Markdown:\n"
        f"# Termo de Abertura do Projeto - {title}\n"
        "## 1. Contexto\n"
        "## 2. Objetivo do Projeto\n"
        "## 3. Escopo Inicial\n"
        "  Inclua 'Dentro do escopo' e 'Fora do escopo'.\n"
        "## 4. Stakeholders\n"
        "## 5. Premissas e Restrições\n"
        "## 6. Riscos Iniciais\n"
        "## 7. Critérios de Sucesso\n"
        "  Critérios devem usar checklist Markdown '- [ ]'.\n"
        "## 8. Próximo Passo\n"
        "  Explique quais specs funcionais devem nascer a partir deste TAP.\n\n"
        "Retorne somente Markdown, sem bloco de código e sem JSON."
    )

    messages = [
        {"role": "user", "content": f"Projeto: {title}\n\nContexto informado:\n{req.prompt}"}
    ]

    try:
        markdown_content = agent.call_llm(provider, model, api_key, messages, system_prompt).strip()
        markdown_content = re.sub(r"^```(?:markdown|md)?\s*", "", markdown_content, flags=re.IGNORECASE).strip()
        markdown_content = re.sub(r"\s*```$", "", markdown_content).strip() + "\n"

        charter_path = _sdd_charter_path(project)
        with open(charter_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        log = ActivityLog(
            project_id=project.id,
            action_type="SDD_CHARTER_GENERATED",
            details="Project Charter/TAP gerado por IA: project-charter.md"
        )
        db.add(log)
        db.commit()

        return {
            "status": "success",
            "filename": "project-charter.md",
            "content": markdown_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar TAP por IA: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/specs", tags=["Spec-Driven Development"])
def list_sdd_specs(project: Project = Depends(get_project_or_404)):
    """Lista REQs de .documents/requirements, antigas de .documents/spec e specs legadas de .documents/specs."""
    documents_dir = os.path.join(project.path, ".documents")
    requirements_dir = os.path.join(documents_dir, "requirements")
    functional_dir = os.path.join(documents_dir, "functional-requirements")
    spec_dir = os.path.join(documents_dir, "spec")
    legacy_specs_dir = os.path.join(documents_dir, "specs")

    def extract_markdown_title(filepath: str, fallback: str) -> str:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line_stripped = line.strip()
                    if line_stripped.startswith("# "):
                        return line_stripped.lstrip("# ").strip()
        except Exception:
            pass
        return fallback

    def classify_spec(rel_path: str, title: str, filename: str) -> str:
        identity = f"{rel_path} {title} {filename}".replace("\\", "/")
        basename = os.path.splitext(os.path.basename(filename))[0]
        if (
            "functional-requirements" in identity.lower()
            or re.search(r"\bRF-\d{2,6}(?:-\d{1,4})?\b", identity, flags=re.IGNORECASE)
            or re.match(r"^\s*RF[-_\[]", basename, flags=re.IGNORECASE)
        ):
            return "rf"
        if re.search(r"\bREQ-\d{2,6}\b", identity, flags=re.IGNORECASE):
            return "req"
        return "other"

    def append_markdown_specs(directory: str, storage_type: str, filepath_prefix: str):
        if not os.path.exists(directory):
            return
        for root, _, files in os.walk(directory):
            for filename in files:
                if not filename.endswith(".md"):
                    continue
                filepath = os.path.join(root, filename)
                rel_dir = os.path.relpath(root, directory)
                if rel_dir == ".":
                    rel_path = filename
                else:
                    rel_path = f"{rel_dir}/{filename}".replace("\\", "/")
                
                stat = os.stat(filepath)
                title = extract_markdown_title(filepath, filename)
                kind = classify_spec(rel_path, title, filename)
                specs.append({
                    "id": os.path.splitext(filename)[0],
                    "filename": rel_path,
                    "title": title,
                    "kind": kind,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "storage_type": storage_type,
                    "filepath": f"{filepath_prefix}/{rel_path}".replace("\\", "/")
                })

    specs = []
    try:
        append_markdown_specs(requirements_dir, "project_spec_file", ".documents/requirements")
        append_markdown_specs(functional_dir, "project_spec_file", ".documents/functional-requirements")
        append_markdown_specs(spec_dir, "project_spec_file", ".documents/spec")
        append_markdown_specs(legacy_specs_dir, "legacy_markdown", ".documents/specs")
        specs.sort(key=lambda x: x["modified_at"], reverse=True)
        return specs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar especificações: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/specs/{filename:path}/criteria", tags=["Spec-Driven Development"])
def get_sdd_spec_criteria(filename: str, project: Project = Depends(get_project_or_404)):
    """Extrai tarefas exclusivamente do task.md vivo do projeto."""
    filename = filename.strip()
    if not filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    task_path = _sdd_project_document_path(project, "task")
    source_type = "project_task_document"

    if not os.path.exists(task_path):
        return {
            "filename": filename,
            "source_type": "project_task_document",
            "filepath": os.path.relpath(task_path, project.path).replace("\\", "/"),
            "criteria": []
        }

    criteria = []
    try:
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            criterion = _parse_sdd_task_line(line, i)
            if criterion:
                criteria.append(criterion)
        return {
            "filename": filename,
            "source_type": source_type,
            "filepath": os.path.relpath(task_path, project.path).replace("\\", "/"),
            "criteria": criteria
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair tarefas: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/specs/{filename:path}", tags=["Spec-Driven Development"])
def get_sdd_spec(filename: str, project: Project = Depends(get_project_or_404)):
    """Retorna o conteúdo de um REQ em .documents/spec ou de uma spec legada."""
    filename = filename.strip()
    if not filename or ".." in filename or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    spec_path_requirements = os.path.join(project.path, ".documents", "requirements", filename)
    spec_path_functional = os.path.join(project.path, ".documents", "functional-requirements", filename)
    spec_path = os.path.join(_sdd_spec_dir(project), filename)
    legacy_spec_path = os.path.join(project.path, ".documents", "specs", filename)
    storage_type = "project_spec_file"
    
    target_path = None
    for p in [spec_path_requirements, spec_path_functional, spec_path, legacy_spec_path]:
        if os.path.exists(p):
            target_path = p
            if p == legacy_spec_path:
                storage_type = "legacy_markdown"
            break

    if not target_path:
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "filename": filename,
            "content": content,
            "storage_type": storage_type,
            "filepath": os.path.relpath(target_path, project.path).replace("\\", "/")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler especificação: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/specs", tags=["Spec-Driven Development"])
def save_sdd_spec(
    req: SddSpecSaveRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Cria ou atualiza um REQ em .documents/spec, preservando edição legada quando aplicável."""
    filename = req.filename.strip().replace("\\", "/")
    if not filename or ".." in filename or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido. Deve terminar com .md")

    legacy_specs_dir = os.path.join(_sdd_documents_dir(project), "specs")
    
    basename = filename.split("/")[-1]

    # Se for um RF, salva em functional-requirements, senão em requirements
    if (
        "functional-requirements" in filename
        or re.search(r"\bRF-\d{2,6}(?:-\d{1,4})?\b", filename, flags=re.IGNORECASE)
        or re.match(r"^\s*RF[-_\[]", os.path.splitext(basename)[0], flags=re.IGNORECASE)
    ):
        spec_dir = os.path.join(_sdd_documents_dir(project), "functional-requirements")
        # Remove a pasta do nome do arquivo se o frontend enviar para não aninhar
        if "/" in filename:
            filename = basename
    else:
        spec_dir = os.path.join(_sdd_documents_dir(project), "requirements")
        if "/" in filename:
            filename = basename
            
    os.makedirs(spec_dir, exist_ok=True)
    spec_path = os.path.join(spec_dir, filename)
    legacy_spec_path = os.path.join(legacy_specs_dir, filename)

    should_update_legacy = os.path.exists(legacy_spec_path) and not os.path.exists(spec_path) and req.overwrite
    target_path = legacy_spec_path if should_update_legacy else spec_path
    storage_type = "legacy_markdown" if should_update_legacy else "project_spec_file"

    if os.path.exists(target_path) and not req.overwrite:
        raise HTTPException(status_code=409, detail="Já existe uma especificação com este arquivo.")

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(req.content)

        rel_path = os.path.relpath(target_path, project.path).replace("\\", "/")
        log = ActivityLog(
            project_id=project.id,
            action_type="SPEC_SAVED",
            details=f"REQ salvo: {rel_path}"
        )
        db.add(log)
        db.commit()

        return {
            "status": "success",
            "message": "REQ salvo com sucesso.",
            "filename": filename,
            "filepath": rel_path,
            "storage_type": storage_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar REQ: {str(e)}")

@app.delete("/api/projects/{project_id}/sdd/specs/{filename:path}", tags=["Spec-Driven Development"])
def delete_sdd_spec(
    filename: str,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Deleta uma especificação específica."""
    if ".." in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    filename = filename.strip()
    
    docs_dir = os.path.join(project.path, ".documents")
    spec_path = os.path.join(docs_dir, "requirements", filename)
    func_spec_path = os.path.join(docs_dir, "functional-requirements", filename)
    legacy_spec_path = os.path.join(docs_dir, "specs", filename)
    legacy_spec2_path = os.path.join(docs_dir, "spec", filename)
    
    target_path = None
    for p in [spec_path, func_spec_path, legacy_spec_path, legacy_spec2_path]:
        if os.path.exists(p):
            target_path = p
            break
            
    if not target_path:
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")
        
    try:
        os.remove(target_path)
        
        # Check if this is the main REQ file inside a REQ folder
        parent_dir = os.path.dirname(target_path)
        basename_no_ext = os.path.splitext(os.path.basename(target_path))[0]
        parent_dir_name = os.path.basename(parent_dir)
        
        if parent_dir_name and basename_no_ext.lower() == parent_dir_name.lower():
            import shutil
            try:
                shutil.rmtree(parent_dir)
            except Exception:
                pass
        else:
            # Cleanup parent directory if it is now empty (e.g. RF folder)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except Exception:
                    pass
                
        rel_path = os.path.relpath(target_path, project.path).replace("\\", "/")
        log = ActivityLog(
            project_id=project.id,
            action_type="SPEC_DELETED",
            details=f"REQ deletado: {rel_path}"
        )
        db.add(log)
        db.commit()
        
        return {"status": "success", "message": "Especificação excluída com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar especificação: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/generate-spec", tags=["Spec-Driven Development"])
def generate_sdd_spec(
    req: SddSpecGenerateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Gera uma especificação técnica em Markdown usando IA com base no prompt."""
    config = agent.load_agent_config()
    provider = config.get("provider")
    model = config.get("model")
    api_key = config.get("api_key")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Chave de API da LLM não configurada no Agente IA.")
        
    is_rf = req.kind == "rf"
    doc_type = "Requisito Funcional (RF)" if is_rf else "Macro Requisito (REQ Pai)"
    req_id = req.parent_id if is_rf and req.parent_id else "REQ-01"
    template_to_use = _sdd_rf_template("RF-01-01", req_id, "[Título]") if is_rf else _sdd_req_pai_template("REQ-01", "[Título]")
    folder_context = f"RF-01-01-nome.md (em .documents/functional-requirements)" if is_rf else f"REQ-01-nome.md (em .documents/requirements)"
    
    system_prompt = (
        f"Você é um Product Engineer especialista em Harness Engineering.\n"
        f"Sua tarefa é gerar SOMENTE o documento {doc_type}.\n"
        "Você DEVE retornar a resposta formatada estritamente como um objeto JSON estruturado contendo:\n"
        "1. \"title\": O título.\n"
        f"2. \"filename\": nome seguro com caminho relativo: ex: {folder_context}\n"
        f"3. \"markdown\": o arquivo Markdown gerado.\n\n"
        "Use obrigatoriamente o template abaixo:\n\n"
        f"{template_to_use}\n\n"
        "Em Critérios de Aceite, use checklist Markdown '- [ ]'.\n"
        "Retorne estritamente um JSON."
    )
    
    messages = [
        {"role": "user", "content": f"Por favor, gere uma especificação completa para a seguinte ideia de funcionalidade:\n\n{req.prompt}"}
    ]
    
    try:
        raw_resp = agent.call_llm(provider, model, api_key, messages, system_prompt)
        parsed = agent.extract_json(raw_resp)
        
        title = parsed.get("title", req.title or "Especificação Gerada")
        filename = parsed.get("filename", "spec.md").replace("\\", "/")
        if not filename.endswith(".md"):
            filename += ".md"
            
        markdown_content = parsed.get("markdown", "")
        if not markdown_content:
            raise HTTPException(status_code=500, detail="A IA não retornou um documento válido.")
        required_sections = [
            "## 1. Identificação",
        ]
        missing_sections = [section for section in required_sections if section not in markdown_content]
        if missing_sections:
            raise HTTPException(status_code=500, detail=f"A IA retornou um REQ fora do template oficial. Seções ausentes: {', '.join(missing_sections)}")
        
        specs_dir = _sdd_spec_dir(project, create=True)
        spec_path = os.path.join(specs_dir, filename)
        os.makedirs(os.path.dirname(spec_path), exist_ok=True)
        
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        rel_path = os.path.relpath(spec_path, project.path).replace("\\", "/")
        log = ActivityLog(
            project_id=project.id,
            action_type="SPEC_GENERATED",
            details=f"REQ gerado por IA: {rel_path}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "title": title,
            "filename": filename,
            "filepath": rel_path,
            "storage_type": "project_spec_file",
            "markdown": markdown_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar especificação por IA: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/tasks", tags=["Spec-Driven Development"])
def get_sdd_project_tasks(project: Project = Depends(get_project_or_404)):
    """Extrai todas as tarefas do task.md vivo do projeto."""
    task_path = _sdd_project_document_path(project, "task")
    source_type = "project_task_document"

    if not os.path.exists(task_path):
        return {
            "source_type": source_type,
            "filepath": os.path.relpath(task_path, project.path).replace("\\", "/"),
            "criteria": []
        }

    criteria = []
    try:
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            criterion = _parse_sdd_task_line(line, i)
            if criterion:
                criteria.append(criterion)
        return {
            "source_type": source_type,
            "filepath": os.path.relpath(task_path, project.path).replace("\\", "/"),
            "criteria": criteria
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair tarefas: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/specs/{filename}/criteria", tags=["Spec-Driven Development"])
def update_sdd_spec_criteria(
    filename: str,
    req: SddCriteriaUpdateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Atualiza checkboxes exclusivamente no task.md vivo do projeto."""
    filename = os.path.basename(filename.strip())
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    task_path = _sdd_project_document_path(project, "task")
    source_type = "project_task_document"

    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail="Documento de tarefas não encontrado.")

    try:
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updates = {item.line_no: item.checked for item in req.criteria}
        for line_no, checked in updates.items():
            idx = line_no - 1
            if 0 <= idx < len(lines):
                indent_match = re.match(r"^(\s*)\-\s*\[[ xX]\](.*)", lines[idx])
                if indent_match:
                    indent = indent_match.group(1)
                    rest = indent_match.group(2)
                    box = "[x]" if checked else "[ ]"
                    lines[idx] = f"{indent}- {box}{rest}\n"

        with open(task_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        rel_path = os.path.relpath(task_path, project.path).replace("\\", "/")
        db.add(ActivityLog(
            project_id=project.id,
            action_type="SDD_TASK_CRITERIA_UPDATED",
            details=f"Checkboxes atualizados em {rel_path}"
        ))
        db.commit()

        return {
            "status": "success",
            "message": "Tarefas atualizadas com sucesso.",
            "source_type": source_type,
            "filepath": rel_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar tarefas: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/tasks/criteria", tags=["Spec-Driven Development"])
def update_sdd_project_tasks(
    req: SddCriteriaUpdateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Atualiza checkboxes diretamente no task.md vivo do projeto."""
    task_path = _sdd_project_document_path(project, "task")
    source_type = "project_task_document"

    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail="Documento de tarefas não encontrado.")

    try:
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        updates = {item.line_no: item.checked for item in req.criteria}
        for line_no, checked in updates.items():
            idx = line_no - 1
            if 0 <= idx < len(lines):
                indent_match = re.match(r"^(\s*)\-\s*\[[ xX]\](.*)", lines[idx])
                if indent_match:
                    indent = indent_match.group(1)
                    rest = indent_match.group(2)
                    box = "[x]" if checked else "[ ]"
                    lines[idx] = f"{indent}- {box}{rest}\n"

        with open(task_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        rel_path = os.path.relpath(task_path, project.path).replace("\\", "/")
        db.add(ActivityLog(
            project_id=project.id,
            action_type="SDD_PROJECT_TASKS_UPDATED",
            details=f"Checkboxes atualizados em {rel_path}"
        ))
        db.commit()

        return {
            "status": "success",
            "message": "Tarefas atualizadas com sucesso.",
            "source_type": source_type,
            "filepath": rel_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar tarefas: {str(e)}")


@app.delete("/api/projects/{project_id}/sdd/tasks/bulk", tags=["Spec-Driven Development"])
def delete_sdd_project_tasks_bulk(
    req: SddTaskBulkDeleteRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key),
):
    """Remove múltiplas tarefas do task.md e suas seções correspondentes do task.details.md."""
    line_nos = sorted({line_no for line_no in req.line_nos if line_no >= 1}, reverse=True)
    if not line_nos:
        raise HTTPException(status_code=400, detail="Nenhuma linha de tarefa válida foi informada.")

    task_path = _sdd_project_document_path(project, "task")
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail="Documento de tarefas não encontrado.")

    try:
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        removed_tasks = []
        invalid_lines = []
        for line_no in line_nos:
            line_index = line_no - 1
            if line_index >= len(lines):
                invalid_lines.append(line_no)
                continue
            criterion = _parse_sdd_task_line(lines[line_index], line_index)
            if not criterion:
                invalid_lines.append(line_no)
                continue
            removed_tasks.append(criterion)
            del lines[line_index]

        if invalid_lines:
            raise HTTPException(
                status_code=400,
                detail=f"Linhas inválidas ou sem task: {', '.join(map(str, sorted(invalid_lines)))}",
            )
        if not removed_tasks:
            raise HTTPException(status_code=400, detail="Nenhuma tarefa válida foi encontrada para exclusão.")

        with open(task_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        details_path = _sdd_project_document_path(project, "task_details")
        removed_details = []
        for task in removed_tasks:
            if _remove_sdd_task_detail_section(details_path, task["code"]):
                removed_details.append(task["code"])

        rel_path = os.path.relpath(task_path, project.path).replace("\\", "/")
        removed_codes = [task["code"] for task in sorted(removed_tasks, key=lambda item: item["line_no"])]
        db.add(ActivityLog(
            project_id=project.id,
            action_type="SDD_TASKS_BULK_DELETED",
            details=f"{len(removed_codes)} tasks removidas de {rel_path}: {', '.join(removed_codes)}",
        ))
        db.commit()
        return {
            "status": "success",
            "message": "Tarefas excluídas com sucesso.",
            "tasks": removed_codes,
            "details_removed": removed_details,
            "filepath": rel_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir tarefas: {str(e)}")


@app.delete("/api/projects/{project_id}/sdd/tasks/{line_no}", tags=["Spec-Driven Development"])
def delete_sdd_project_task(
    line_no: int,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key),
):
    """Remove uma tarefa do task.md e sua seção correspondente do task.details.md."""
    if line_no < 1:
        raise HTTPException(status_code=400, detail="Número de linha inválido.")

    task_path = _sdd_project_document_path(project, "task")
    if not os.path.exists(task_path):
        raise HTTPException(status_code=404, detail="Documento de tarefas não encontrado.")

    try:
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line_index = line_no - 1
        if line_index >= len(lines):
            raise HTTPException(status_code=404, detail="Tarefa não encontrada na linha informada.")

        criterion = _parse_sdd_task_line(lines[line_index], line_index)
        if not criterion:
            raise HTTPException(status_code=400, detail="A linha informada não contém uma tarefa válida.")

        task_code = criterion["code"]
        del lines[line_index]
        with open(task_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        details_path = _sdd_project_document_path(project, "task_details")
        detail_removed = _remove_sdd_task_detail_section(details_path, task_code)
        rel_path = os.path.relpath(task_path, project.path).replace("\\", "/")
        db.add(ActivityLog(
            project_id=project.id,
            action_type="SDD_TASK_DELETED",
            details=f"{task_code} removida de {rel_path}; detalhe removido: {detail_removed}",
        ))
        db.commit()
        return {
            "status": "success",
            "message": "Tarefa excluída com sucesso.",
            "task_code": task_code,
            "detail_removed": detail_removed,
            "filepath": rel_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir tarefa: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/generate-tests", tags=["Spec-Driven Development"])
def generate_sdd_tests(
    req: SddTestGenerateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Gera arquivos de testes unitários ou de integração com IA baseado na especificação."""
    if ".." in req.filename or "/" in req.filename or "\\" in req.filename:
        raise HTTPException(status_code=400, detail="Nome de especificação inválido.")
        
    filename = os.path.basename(req.filename.strip())
    spec_path = os.path.join(_sdd_spec_dir(project), filename)
    legacy_spec_path = os.path.join(project.path, ".documents", "specs", filename)
    if not os.path.exists(spec_path):
        spec_path = legacy_spec_path
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")
        
    config = agent.load_agent_config()
    provider = config.get("provider")
    model = config.get("model")
    api_key = config.get("api_key")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Chave de API da LLM não configurada no Agente IA.")
        
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_content = f.read()
            
        system_prompt = (
            "Você é um Engenheiro de Software focado em Qualidade de Software (QA) e Testes Automatizados.\n"
            "Sua tarefa é ler uma especificação técnica e gerar um código de teste completo e limpo para ela.\n"
            f"O framework de teste a ser utilizado é: {req.framework}.\n"
            "Você deve mapear Specify, Design, DRI quando existir, e cada item marcado como tarefa da seção Task List para um ou mais casos de teste no código.\n\n"
            "Você DEVE retornar a resposta formatada estritamente como um objeto JSON estruturado contendo:\n"
            "1. \"filepath\": O caminho onde o arquivo de teste deve ser gravado (ex: tests/test_auth.py, __tests__/auth.test.js).\n"
            "2. \"code\": O código de teste completo, pronto para execução.\n\n"
            "Retorne estritamente o objeto JSON. Não adicione tags de bloco ```json ou qualquer texto explicativo."
        )
        
        messages = [
            {"role": "user", "content": f"Aqui está a especificação técnica em Markdown:\n\n{spec_content}"}
        ]
        
        raw_resp = agent.call_llm(provider, model, api_key, messages, system_prompt)
        parsed = agent.extract_json(raw_resp)
        
        filepath = parsed.get("filepath", "tests/test_spec.py")
        code = parsed.get("code", "")
        
        # Limpa o filepath contra caminhos maliciosos
        if ".." in filepath:
            filepath = os.path.basename(filepath)
            
        full_filepath = os.path.join(project.path, filepath)
        # Garante que as pastas pai existem
        os.makedirs(os.path.dirname(full_filepath), exist_ok=True)
        
        with open(full_filepath, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Log da ação
        log = ActivityLog(
            project_id=project.id,
            action_type="TEST_GENERATED",
            details=f"Testes gerados via IA ({req.framework}): {filepath} baseado em {req.filename}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "filepath": filepath,
            "code": code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar testes via IA: {str(e)}")

# --- ENDPOINTS DO AGENTE IA NATIVO ---

def _native_agent_ops_context(project: Project) -> str:
    access = _ops_read_vm_access(project.path, public=True)
    detected = _ops_detect_stack(project.path)
    access_summary = "não configurado"
    if access.get("host") and access.get("user"):
        auth = access.get("auth_method", "key")
        app_path = access.get("app_path") or "não informado"
        access_summary = f"{access.get('user')}@{access.get('host')}:{access.get('port', 22)} via {auth}; app_path={app_path}"
    return (
        f"Project ID: {project.id}\n"
        f"Projeto: {project.name}\n"
        f"Workspace: {project.path}\n"
        f"Git remote: {project.git_remote or 'não configurado'}\n"
        f"Stack detectada: runtime={detected.get('runtime')}, package={detected.get('package_manager')}, port={detected.get('port')}\n"
        f"Ops Infra VM: {access_summary}\n"
        "A IA nativa tem acesso operacional ao Ops Infra por ferramentas internas ops_infra_*.\n"
        "Sempre use essas ferramentas para VM/deploy/domínio/banco/Docker/Caddy/health check.\n"
        "IDs no formato QA-XXXXXXXX pertencem à Central QA. Sempre use qa_get_annotation antes de inferir comando, teste ou arquivo.\n"
        "Operações destrutivas como down devem ser explicitamente confirmadas pelo usuário no pedido atual.\n"
    )

def _read_project_text(project: Project, rel_path: str, max_chars: int = 6000) -> str:
    safe_rel = rel_path.replace("\\", "/").lstrip("/")
    target = os.path.abspath(os.path.join(project.path, safe_rel))
    root = os.path.abspath(project.path)
    if not target.startswith(root) or not os.path.exists(target) or not os.path.isfile(target):
        return ""
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception:
        return ""

def _find_req_document(project: Project, req_id: str) -> dict:
    req_id = req_id.upper()
    spec_dir = _sdd_spec_dir(project, create=False)
    if not os.path.isdir(spec_dir):
        return {}
    for filename in sorted(os.listdir(spec_dir)):
        if not filename.lower().endswith(".md"):
            continue
        path = os.path.join(spec_dir, filename)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(12000)
            if req_id in content.upper() or req_id.lower() in filename.lower():
                return {
                    "id": req_id,
                    "filepath": os.path.relpath(path, project.path).replace("\\", "/"),
                    "content": content,
                }
        except Exception:
            continue
    return {}

def _find_task_context(project: Project, task_id: str) -> dict:
    task_id = task_id.upper()
    task_path = _sdd_project_document_path(project, "task")
    details_path = _sdd_project_document_path(project, "task_details")
    task_content = _read_project_text(project, os.path.relpath(task_path, project.path), 16000)
    details_content = _read_project_text(project, os.path.relpath(details_path, project.path), 20000)
    task_line = ""
    for line in task_content.splitlines():
        if task_id in line.upper():
            task_line = line.strip()
            break
    details_section = ""
    if details_content:
        escaped = re.escape(task_id)
        match = re.search(rf"(^##\s+Plano\s+[—-]\s+{escaped}[\s\S]*?)(?=^##\s+Plano\s+[—-]\s+TASK-|\Z)", details_content, re.IGNORECASE | re.MULTILINE)
        if match:
            details_section = match.group(1).strip()
    return {
        "id": task_id,
        "task_file": ".documents/task/task.md",
        "task_line": task_line,
        "details_file": ".documents/task/task.details.md",
        "details": details_section,
    }

def _native_agent_intent_context(project: Project, prompt: str) -> str:
    """Cria contexto determinístico para IDs do Act IA antes da LLM decidir ferramentas."""
    prompt_text = prompt or ""
    parts = []
    template_rules = (
        "TEMPLATES OFICIAIS OBRIGATÓRIOS DO HARNESS:\n"
        "- Esta regra vale para todos os documentos gerados ou revisados pelo agente, sem exceção.\n"
        "- É proibido criar documento resumido, simplificado ou fora do template oficial.\n"
        "- Um REQ com apenas Título, Descrição, Detalhes Técnicos e Prioridade/Severidade é inválido e deve ser refeito.\n"
        "- REQ individual deve ficar em `.documents/spec/*.md` e conter obrigatoriamente: `## 1. Specify - Especificação Funcional`, `### 1.1 Identificação e Metadados Básicos`, `### 1.2 Contexto`, `### 1.3 Objetivo Funcional`, `### 1.4 Descrição do Requisito`, `### 1.5 História de Usuário`, `### 1.6 Regras de Negócio`, `### 1.7 Restrições e Premissas`, `### 1.8 Fora do Escopo`, `### 1.9 Critérios de Aceite` e `### 1.10 Rastreabilidade Funcional`.\n"
        "- Design deve ficar em `.documents/design/design.md` e conter arquitetura proposta, fluxos técnicos, APIs/eventos/contratos, dados/persistência, segurança/permissões e estratégia de validação.\n"
        "- DRI deve ficar em `.documents/dri/dri.md` e seguir o RI oficial completo com as seções 1 a 17, incluindo critérios de aceite da interface, lacunas/premissas, fora do escopo e evoluções futuras.\n"
        "- Task List deve ficar em `.documents/task/task.md` e conter somente itens no formato `- [ ] TASK-RF-0001-01-001: - Título curto` ou `- [ ] TASK-QA-XXXXXXXX-001: - Título curto`.\n"
        "- Task Details deve ficar em `.documents/task/task.details.md`, ser acumulativo, nunca apagar seções anteriores e usar seções `# TASK-...` contendo as subseções: Título, Objetivo, História do usuário, Escopo, Regras de negócio, Critérios de aceite, Dependências e Definition of Done, além de pedir a autorização única do pacote Harness.\n"
        "- O agente deve criar/revisar REQ, Design, DRI quando aplicável, Task List e Task Details em sequência, sem pedir aprovação por documento.\n"
        "- Depois de montar todos os documentos, solicite uma única aprovação do pacote completo. Se aprovado, execute todas as tasks em ordem, sem aprovação intermediária por task. Solicite validação final somente após executar e verificar todas as tasks.\n"
        "- Para QA visual/layout enquadrado na exceção controlada, não crie REQ resumido: crie somente TASK-QA no task.md e detalhe completo no task.details.md, peça uma única aprovação do pacote QA e depois execute todas as tasks QA em sequência.\n"
        "- Se um documento existente estiver fora do formato oficial, primeiro corrija o documento para o template completo antes de avançar no fluxo.\n"
    )

    qa_ids = sorted(set(re.findall(r"\bQA-[A-Z0-9]{6,12}\b", prompt_text, flags=re.IGNORECASE)))
    if qa_ids:
        annotations = _read_qa_annotations(project)
        for qa_id in qa_ids[:3]:
            qa_upper = qa_id.upper()
            item = next((entry for entry in annotations if str(entry.get("id", "")).upper() == qa_upper), None)
            if item:
                public = _qa_public_annotation(project, item)
                public.pop("screenshot_data", None)
                if isinstance(public.get("screenshot"), str) and public["screenshot"].startswith("data:"):
                    public["screenshot"] = "[evidencia base64 omitida]"
                parts.append(
                    "INTENÇÃO DETECTADA: QA\n"
                    f"QA ID: {qa_upper}\n"
                    "Regra: este ID é uma anotação da Central QA, não um comando de terminal.\n"
                    "Primeira ação obrigatória: use qa_get_annotation se precisar confirmar dados; não use git_status ou package.json como primeira ação.\n"
                    "Fluxo esperado: entender a anotação, classificar se é ajuste visual/layout ou mudança funcional, criar/atualizar os documentos Harness no template oficial completo, solicitar uma única aprovação do pacote, executar todas as tasks aprovadas em sequência e atualizar status QA quando concluído.\n"
                    "Se for ajuste fino visual/layout sem impacto funcional/arquitetural, use a exceção controlada: crie TASK-QA em `.documents/task/task.md` e detalhe completo em `.documents/task/task.details.md`; não crie REQ resumido; peça uma única aprovação do pacote QA e execute todas as tasks QA após aprovação.\n"
                    "Se for mudança funcional, crie/atualize REQ completo com seções 1.1 a 1.10, revise Design, revise DRI quando houver interface, crie Task List e Task Details; depois peça uma única aprovação do pacote completo antes de executar.\n"
                    f"Anotação carregada: {json.dumps(public, ensure_ascii=False)[:5000]}"
                )
            else:
                parts.append(
                    "INTENÇÃO DETECTADA: QA\n"
                    f"QA ID: {qa_upper}\n"
                    "Regra: buscar com qa_get_annotation antes de qualquer outra ação. Se não encontrar, responda solicitando confirmar o ID. Nunca crie documento resumido para este QA."
                )

    task_ids = sorted({match.group(0).upper() for match in SDD_TASK_CODE_PATTERN.finditer(prompt_text)})
    for task_id in task_ids[:3]:
        context = _find_task_context(project, task_id)
        parts.append(
            "INTENÇÃO DETECTADA: TASK\n"
            f"Task ID: {context['id']}\n"
            "Regra: este ID é uma tarefa Harness. Antes de executar, leia task.md e task.details.md; se detalhes estiverem ausentes ou resumidos, crie/atualize o plano detalhado no template oficial. A execução deve respeitar a aprovação única do pacote Harness, sem aprovações intermediárias task a task.\n"
            f"Linha em task.md: {context.get('task_line') or '[não encontrada]'}\n"
            f"Detalhes em task.details.md: {(context.get('details') or '[não encontrado]')[:5000]}"
        )

    req_ids = sorted(set(re.findall(r"\bREQ-\d{2,6}\b", prompt_text, flags=re.IGNORECASE)))
    for req_id in req_ids[:3]:
        context = _find_req_document(project, req_id)
        if context:
            parts.append(
                "INTENÇÃO DETECTADA: REQ\n"
                f"REQ ID: {context['id']}\n"
                "Regra: este ID é um requisito funcional. Leia/revise o REQ antes de Design/DRI/Task/Execute. Se o conteúdo estiver resumido ou sem as seções 1.1 a 1.10, corrija o REQ para o template oficial completo antes de avançar.\n"
                f"Arquivo: {context['filepath']}\n"
                f"Conteúdo: {context['content'][:5000]}"
            )
        else:
            parts.append(
                "INTENÇÃO DETECTADA: REQ\n"
                f"REQ ID: {req_id.upper()}\n"
                "Regra: Localize os requisitos em .documents/requirements e .documents/functional-requirements."
            )

    if not parts:
        return template_rules
    return template_rules + "\n\n---\n\n" + "\n\n---\n\n".join(parts)

def _native_agent_ops_tool_descriptions() -> list:
    return [
        "- `qa_get_annotation(annotation_id: str)`: Busca uma anotação QA por ID (ex: QA-D3F8D1C8) em .documents/qa/annotations.json antes de qualquer tentativa de executar comando.",
        "- `qa_list_annotations(status: Optional[str])`: Lista anotações QA resumidas, opcionalmente filtradas por status.",
        "- `qa_update_annotation_status(annotation_id: str, status: str)`: Atualiza status de uma anotação QA para aberta, em_revisao ou resolvida.",
        "- `ops_infra_status()`: Mostra stack detectada, VM cadastrada e capacidades de Ops Infra disponíveis.",
        "- `ops_infra_generate_public_key()`: Gera par de chaves SSH do Act IA e retorna somente a chave pública para instalar na VM.",
        "- `ops_infra_test_ssh()`: Testa conexão SSH cadastrada e valida Docker/Compose quando possível.",
        "- `ops_infra_list_directories(path: str)`: Lista diretórios da VM via SSH para o usuário escolher o caminho do app.",
        "- `ops_infra_create_directory(path: str)`: Cria/valida um diretório absoluto na VM.",
        "- `ops_infra_bootstrap_vm()`: Instala/valida Docker, Docker Compose, Git e firewall básico na VM.",
        "- `ops_infra_sync_project()`: Clona ou atualiza o repositório Git do projeto no diretório salvo da VM.",
        "- `ops_infra_generate_artifacts(environment: str, domain: str, database: str, overwrite: bool)`: Gera Dockerfile, compose, env example e Caddyfile conforme stack detectada.",
        "- `ops_infra_domain_preview(domain: str)`: Prepara prévia de Caddyfile e checklist DNS para o domínio.",
        "- `ops_infra_domain_apply(domain: str, overwrite: bool)`: Escreve Caddyfile no projeto para o domínio informado.",
        "- `ops_infra_env_validate(environment: str, variables: List[dict])`: Valida variáveis de ambiente e secrets planejados.",
        "- `ops_infra_env_save(environment: str, variables: List[dict], write_env_file: bool)`: Salva variáveis por ambiente, criptografando secrets.",
        "- `ops_infra_remote_command(action: str)`: Executa ação Docker Compose remota: build, up, down, restart, logs ou ps.",
        "- `ops_infra_dns_check(domain: str)`: Valida se o domínio aponta para o IP/host da VM cadastrada.",
        "- `ops_infra_health_check(url: str, domain: str)`: Testa HTTP/HTTPS da aplicação implantada.",
        "- `ops_infra_database_check()`: Valida o serviço de banco definido no docker-compose remoto.",
    ]

def _native_agent_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)

def _native_agent_ops_tool(tool_name: str):
    def _handler(db: Session, project: Project, args: dict) -> str:
        try:
            if tool_name == "qa_get_annotation":
                annotation_id = (args.get("annotation_id") or args.get("id") or "").strip().upper()
                if not annotation_id:
                    raise HTTPException(status_code=400, detail="Informe annotation_id.")
                annotations = _read_qa_annotations(project)
                item = next((entry for entry in annotations if str(entry.get("id", "")).upper() == annotation_id), None)
                if not item:
                    return _native_agent_json({
                        "status": "not_found",
                        "annotation_id": annotation_id,
                        "message": f"Anotação QA não encontrada: {annotation_id}",
                        "available_ids": [entry.get("id") for entry in annotations[:20]],
                    })
                public = _qa_public_annotation(project, item)
                public.pop("screenshot_data", None)
                if isinstance(public.get("screenshot"), str) and public["screenshot"].startswith("data:"):
                    public["screenshot"] = "[evidencia base64 omitida; use a tela QA para visualizar]"
                return _native_agent_json({"status": "success", "annotation": public})

            if tool_name == "qa_list_annotations":
                status_filter = (args.get("status") or "").strip() or None
                annotations = _qa_filtered_annotations(project, status_filter)
                rows = []
                for item in annotations[:50]:
                    rows.append({
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "status": item.get("status"),
                        "severity": item.get("severity"),
                        "category": item.get("category"),
                        "url": item.get("url"),
                        "created_at": item.get("created_at"),
                        "description": str(item.get("description") or "")[:240],
                    })
                return _native_agent_json({"status": "success", "total": len(annotations), "annotations": rows})

            if tool_name == "qa_update_annotation_status":
                annotation_id = (args.get("annotation_id") or args.get("id") or "").strip().upper()
                new_status = (args.get("status") or "").strip().lower()
                aliases = {
                    "aberta": "aberta",
                    "open": "aberta",
                    "em revisão": "em_revisao",
                    "em_revisao": "em_revisao",
                    "review": "em_revisao",
                    "resolvida": "resolvida",
                    "resolvido": "resolvida",
                    "resolved": "resolvida",
                }
                normalized_status = aliases.get(new_status)
                if not annotation_id or not normalized_status:
                    raise HTTPException(status_code=400, detail="Informe annotation_id e status válido: aberta, em_revisao ou resolvida.")
                annotations = _read_qa_annotations(project)
                changed = False
                for item in annotations:
                    if str(item.get("id", "")).upper() == annotation_id:
                        item["status"] = normalized_status
                        item["updated_at"] = datetime.utcnow().isoformat() + "Z"
                        changed = True
                        break
                if not changed:
                    return _native_agent_json({"status": "not_found", "annotation_id": annotation_id})
                _write_qa_annotations(project, annotations)
                db.add(ActivityLog(project_id=project.id, action_type="QA_STATUS_UPDATED", details=f"[Agente] {annotation_id} -> {normalized_status}"))
                db.commit()
                return _native_agent_json({"status": "success", "annotation_id": annotation_id, "new_status": normalized_status})

            if tool_name == "ops_infra_status":
                return _native_agent_json({
                    "status": "success",
                    "detected": _ops_detect_stack(project.path),
                    "vm_access": _ops_read_vm_access(project.path, public=True),
                    "capabilities": [
                        "SSH", "VM directory browser", "bootstrap Docker/Git", "sync Git repo",
                        "Docker Compose remote commands", "Caddy/domain", "env/secrets", "database check", "health check"
                    ],
                })

            if tool_name == "ops_infra_generate_public_key":
                result = _ops_generate_keypair(project.path, f"act-ia-{project.name or project.id}")
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_SSH_KEY", details="[Agente] Par de chaves SSH gerado para Ops Infra."))
                db.commit()
                return _native_agent_json({"status": "success", "public_key": result.get("public_key"), "vm_access": _ops_read_vm_access(project.path, public=True)})

            if tool_name == "ops_infra_test_ssh":
                access = _ops_require_vm_access(project.path)
                parts = ["printf ACTIA_SSH_OK", "pwd", "command -v docker || true", "docker compose version || docker-compose version || true"]
                if access.get("app_path"):
                    parts.insert(1, f"test -d {_ops_shell_quote(access['app_path'])} && printf '\\nAPP_PATH_OK\\n' || printf '\\nAPP_PATH_NOT_FOUND\\n'")
                result = _ops_run_ssh(access, " && ".join(parts), timeout=30)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_SSH_TEST", details=f"[Agente] SSH testado em {access['user']}@{access['host']}:{access['port']} | Exit: {result['exit_code']}"))
                db.commit()
                return _native_agent_json(result)

            if tool_name == "ops_infra_list_directories":
                access = _ops_require_vm_access(project.path)
                return _native_agent_json(_ops_list_remote_directories(access, args.get("path") or "/"))

            if tool_name == "ops_infra_create_directory":
                access = _ops_require_vm_access(project.path)
                target = _ops_normalize_remote_path(args.get("path") or "")
                result = _ops_run_ssh(access, f"mkdir -p {_ops_shell_quote(target)} && test -d {_ops_shell_quote(target)} && printf ACTIA_DIR_CREATED", timeout=45)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_VM_DIR", details=f"[Agente] Diretório VM criado/validado: {target} | Exit: {result.get('exit_code')}"))
                db.commit()
                return _native_agent_json(result)

            if tool_name == "ops_infra_bootstrap_vm":
                access = _ops_require_vm_access(project.path)
                result = _ops_run_ssh(access, _ops_bootstrap_script(), timeout=600)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_BOOTSTRAP", details=f"[Agente] Bootstrap VM {access.get('host')} | Exit: {result.get('exit_code')}"))
                db.commit()
                return _native_agent_json(result)

            if tool_name == "ops_infra_sync_project":
                access = _ops_require_vm_access(project.path)
                app_path = _ops_require_app_path(access)
                result = _ops_run_ssh(access, _ops_sync_script(app_path, project.git_remote), timeout=240)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_SYNC", details=f"[Agente] Sync {project.git_remote or '-'} -> {access.get('host')}:{app_path} | Exit: {result.get('exit_code')}"))
                db.commit()
                return _native_agent_json(result)

            if tool_name == "ops_infra_generate_artifacts":
                artifacts = _ops_artifacts(project.path, args.get("environment") or "prod", args.get("domain") or "", args.get("database") or "none")
                overwrite = bool(args.get("overwrite", False))
                written, skipped = [], []
                for rel_path, content in artifacts["files"].items():
                    full_path = os.path.join(project.path, rel_path)
                    if os.path.exists(full_path) and not overwrite:
                        skipped.append(rel_path)
                        continue
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    written.append(rel_path)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_ARTIFACTS", details=f"[Agente] Arquivos gerados: {', '.join(written)}"))
                db.commit()
                return _native_agent_json({"status": "success", "written": written, "skipped": skipped, "detected": artifacts.get("detected")})

            if tool_name == "ops_infra_domain_preview":
                domain = (args.get("domain") or "").strip()
                if not domain:
                    raise HTTPException(status_code=400, detail="Informe o domínio.")
                return _native_agent_json({"status": "success", **_ops_domain_preview(project.path, domain)})

            if tool_name == "ops_infra_domain_apply":
                domain = (args.get("domain") or "").strip()
                if not domain:
                    raise HTTPException(status_code=400, detail="Informe o domínio.")
                preview = _ops_domain_preview(project.path, domain)
                caddy_path = os.path.join(project.path, "Caddyfile")
                if os.path.exists(caddy_path) and not bool(args.get("overwrite", False)):
                    return _native_agent_json({"status": "skipped", "message": "Caddyfile já existe.", **preview})
                with open(caddy_path, "w", encoding="utf-8") as f:
                    f.write(preview["caddyfile"])
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_DOMAIN", details=f"[Agente] Caddyfile configurado para {preview['domain']}"))
                db.commit()
                return _native_agent_json({"status": "success", "written": ["Caddyfile"], **preview})

            if tool_name in {"ops_infra_env_validate", "ops_infra_env_save"}:
                variables = [OpsInfraEnvItem(**item) for item in args.get("variables", []) if isinstance(item, dict)]
                req = OpsInfraEnvRequest(
                    environment=args.get("environment") or "prod",
                    variables=variables,
                    write_env_file=bool(args.get("write_env_file", False)),
                )
                if tool_name == "ops_infra_env_validate":
                    keys = [re.sub(r"[^A-Z0-9_]", "_", item.key.strip().upper()) for item in req.variables if item.key.strip()]
                    detected = _ops_detect_stack(project.path)
                    issues = []
                    if "APP_ENV" not in keys:
                        issues.append("APP_ENV ausente.")
                    if "APP_PORT" not in keys:
                        issues.append("APP_PORT ausente.")
                    if req.environment.lower() == "prod" and not any(k in keys for k in ["APP_DOMAIN", "DOMAIN"]):
                        issues.append("Domínio de produção não informado em APP_DOMAIN ou DOMAIN.")
                    return _native_agent_json({"status": "success", "valid": not issues, "issues": issues, "detected": detected})
                result = _ops_write_env(project.path, req)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_ENV", details=f"[Agente] Ambiente {req.environment} salvo. Env file: {result.get('env_file')}"))
                db.commit()
                return _native_agent_json({"status": "success", **result})

            if tool_name == "ops_infra_remote_command":
                action = (args.get("action") or "").strip().lower()
                commands = {
                    "build": "docker compose build",
                    "up": "docker compose up -d",
                    "down": "docker compose down",
                    "restart": "docker compose restart",
                    "logs": "docker compose logs --tail=120",
                    "ps": "docker compose ps",
                    "status": "docker compose ps",
                }
                if action == "status":
                    action = "ps"
                if action not in commands:
                    raise HTTPException(status_code=400, detail="Ação inválida para Ops Infra.")
                access = _ops_require_vm_access(project.path)
                app_path = _ops_require_app_path(access)
                remote_command = f"cd {_ops_shell_quote(app_path)} && {commands[action]}"
                result = _ops_run_ssh(access, remote_command, timeout=180 if action in ["build", "up"] else 90)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_REMOTE_COMMAND", details=f"[Agente] {commands[action]} em {access['host']}:{app_path}\nExit: {result['exit_code']}"))
                db.commit()
                return _native_agent_json(result)

            if tool_name == "ops_infra_dns_check":
                access = _ops_require_vm_access(project.path)
                domain = (args.get("domain") or "").strip().lower()
                if not domain:
                    raise HTTPException(status_code=400, detail="Informe o domínio.")
                try:
                    records = sorted({item[4][0] for item in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
                except Exception as e:
                    return _native_agent_json({"status": "error", "domain": domain, "expected": access.get("host"), "records": [], "matches": False, "detail": str(e)})
                return _native_agent_json({"status": "success", "domain": domain, "expected": access.get("host"), "records": records, "matches": access.get("host") in records})

            if tool_name == "ops_infra_health_check":
                access = _ops_require_vm_access(project.path)
                req = OpsInfraHealthRequest(url=args.get("url") or "", domain=args.get("domain") or "")
                url = _ops_health_url(project.path, access, req)
                response = requests.get(url, timeout=15, allow_redirects=True)
                return _native_agent_json({
                    "status": "success" if response.status_code < 500 else "error",
                    "url": url,
                    "status_code": response.status_code,
                    "final_url": response.url,
                    "ok": response.ok,
                    "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
                    "content_type": response.headers.get("content-type", ""),
                    "body_preview": response.text[:500],
                })

            if tool_name == "ops_infra_database_check":
                access = _ops_require_vm_access(project.path)
                app_path = _ops_require_app_path(access)
                command = (
                    f"cd {_ops_shell_quote(app_path)} && "
                    "if docker compose config --services | grep -qx postgres; then "
                    "docker compose exec -T postgres pg_isready -U ${POSTGRES_USER:-app} -d ${POSTGRES_DB:-app}; "
                    "else echo 'Nenhum serviço postgres encontrado no docker-compose.yml'; exit 3; fi"
                )
                result = _ops_run_ssh(access, command, timeout=60)
                db.add(ActivityLog(project_id=project.id, action_type="OPS_INFRA_DB_CHECK", details=f"[Agente] Database check em {access.get('host')}:{app_path} | Exit: {result.get('exit_code')}"))
                db.commit()
                return _native_agent_json(result)

            return _native_agent_json({"status": "error", "message": f"Ferramenta Ops desconhecida: {tool_name}"})
        except HTTPException as e:
            return _native_agent_json({"status": "error", "message": e.detail})
        except Exception as e:
            return _native_agent_json({"status": "error", "message": str(e)})
    return _handler

def _native_agent_ops_tools() -> dict:
    names = [
        "qa_get_annotation",
        "qa_list_annotations",
        "qa_update_annotation_status",
        "ops_infra_status",
        "ops_infra_generate_public_key",
        "ops_infra_test_ssh",
        "ops_infra_list_directories",
        "ops_infra_create_directory",
        "ops_infra_bootstrap_vm",
        "ops_infra_sync_project",
        "ops_infra_generate_artifacts",
        "ops_infra_domain_preview",
        "ops_infra_domain_apply",
        "ops_infra_env_validate",
        "ops_infra_env_save",
        "ops_infra_remote_command",
        "ops_infra_dns_check",
        "ops_infra_health_check",
        "ops_infra_database_check",
    ]
    return {name: _native_agent_ops_tool(name) for name in names}

@app.get("/api/agent/config", tags=["Agente IA"])
def get_agent_config():
    """Retorna as configurações atuais do agente IA."""
    return agent.load_agent_config()

@app.post("/api/agent/config", tags=["Agente IA"])
def save_agent_config(config_in: AgentConfigInput):
    """Salva as configurações do agente IA."""
    agent.save_agent_config(config_in.model_dump())
    return {"status": "success", "message": "Configurações do agente salvas."}

@app.get("/api/agent/ollama/models", tags=["Agente IA"])
def list_ollama_models(
    base_url: str = Query("http://127.0.0.1:11434", description="Endpoint local do Ollama"),
    api_key: str = Query(None, description="API Key para Ollama Cloud")
):
    """Lista modelos instalados no Ollama local ou Cloud."""
    clean_url = (base_url or "http://127.0.0.1:11434").strip().rstrip("/")
    if not (clean_url.startswith(("http://127.0.0.1", "http://localhost", "http://0.0.0.0")) or clean_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Por segurança, informe um endpoint local ou uma URL https:// para Cloud.")
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        response = requests.get(f"{clean_url}/api/tags", headers=headers, timeout=8)
        response.raise_for_status()
        data = response.json()
        models = []
        for item in data.get("models", []):
            name = item.get("name")
            if not name:
                continue
            models.append({
                "name": name,
                "size": item.get("size"),
                "modified_at": item.get("modified_at"),
                "details": item.get("details") or {},
            })
        return {"status": "success", "base_url": clean_url, "models": models}
    except Exception as e:
        return {"status": "error", "base_url": clean_url, "models": [], "message": str(e)}

def _agent_history_path(project: Project) -> str:
    agent_dir = os.path.join(project.path, ".documents", "agent")
    os.makedirs(agent_dir, exist_ok=True)
    return os.path.join(agent_dir, "history.json")

def _sanitize_agent_history_payload(payload: dict) -> dict:
    messages = payload.get("messages") if isinstance(payload, dict) else []
    workflow = payload.get("workflow") if isinstance(payload, dict) else []
    clean_messages = []
    clean_workflow = []
    for item in messages[-80:] if isinstance(messages, list) else []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "")[:12000]
        if role in {"user", "assistant"} and content:
            clean_messages.append({
                "role": role,
                "content": content,
                "created_at": item.get("created_at") or datetime.utcnow().isoformat() + "Z",
            })
    for item in workflow[-120:] if isinstance(workflow, list) else []:
        if not isinstance(item, dict):
            continue
        event_type = str(item.get("type") or "status")[:40]
        title = str(item.get("title") or "")[:160]
        body = str(item.get("body") or "")[:2000]
        if body or title:
            clean_workflow.append({
                "type": event_type,
                "title": title,
                "body": body,
                "created_at": item.get("created_at") or datetime.utcnow().isoformat() + "Z",
            })
    return {
        "version": 1,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "messages": clean_messages,
        "workflow": clean_workflow,
    }

@app.get("/api/projects/{project_id}/agent/history", tags=["Agente IA"])
def get_agent_history(project: Project = Depends(get_project_or_404)):
    """Carrega o histórico persistido do Agente IA no projeto ativo."""
    filepath = _agent_history_path(project)
    if not os.path.exists(filepath):
        return {"status": "success", "messages": [], "workflow": [], "updated_at": None}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        clean = _sanitize_agent_history_payload(data)
        return {"status": "success", **clean}
    except Exception as e:
        return {"status": "error", "messages": [], "workflow": [], "message": str(e)}

@app.put("/api/projects/{project_id}/agent/history", tags=["Agente IA"])
def save_agent_history(req: AgentHistorySaveRequest, project: Project = Depends(get_project_or_404)):
    """Persiste o histórico visual e operacional do Agente IA no projeto ativo."""
    filepath = _agent_history_path(project)
    payload = _sanitize_agent_history_payload(req.model_dump())
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"status": "success", "filepath": ".documents/agent/history.json", "updated_at": payload["updated_at"]}

@app.delete("/api/projects/{project_id}/agent/history", tags=["Agente IA"])
def clear_agent_history(project: Project = Depends(get_project_or_404)):
    """Limpa o histórico persistido do Agente IA no projeto ativo."""
    filepath = _agent_history_path(project)
    if os.path.exists(filepath):
        os.remove(filepath)
    return {"status": "success", "message": "Histórico do agente limpo."}

@app.post("/api/projects/{project_id}/agent/run", tags=["Agente IA"])
def run_agent(project_id: int, 
              req: AgentChatRequest, 
              project: Project = Depends(get_project_or_404),
              db: Session = Depends(get_db)):
    """
    Roda a execução do agente em tempo real por streaming.
    Retorna Server-Sent Events (SSE).
    """
    config = agent.load_agent_config()
    runtime_context = _native_agent_ops_context(project)
    intent_context = _native_agent_intent_context(project, req.prompt)
    if intent_context:
        runtime_context += "\n\nROTEAMENTO DETERMINÍSTICO DO PEDIDO:\n" + intent_context
    return StreamingResponse(
        agent.run_agent_loop(
            db,
            project,
            config,
            req.prompt,
            conversation_history=req.history or [],
            extra_tools=_native_agent_ops_tools(),
            extra_tool_descriptions=_native_agent_ops_tool_descriptions(),
            system_context=runtime_context,
        ),
        media_type="text/event-stream"
    )

def list_drives():
    drives = []
    if os.name == 'nt':
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    return drives

@app.get("/api/system/dirs", tags=["Sistema"])
def browse_directories(path: Optional[str] = None):
    """Retorna a lista de subdiretórios de um caminho físico no computador (para seleção de pastas)."""
    if not path:
        path = os.path.expanduser("~")
        
    path = os.path.abspath(path)
    if not os.path.exists(path):
        path = os.path.expanduser("~")
        
    try:
        entries = os.scandir(path)
        dirs = []
        for entry in entries:
            try:
                if entry.is_dir() and not entry.name.startswith('.'):
                    dirs.append(entry.name)
            except OSError:
                continue
        dirs.sort(key=str.lower)
        
        parent = os.path.dirname(path)
        if parent == path:
            parent = None
            
        return {
            "status": "success",
            "current_path": path,
            "parent_path": parent,
            "directories": dirs,
            "drives": list_drives()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Não foi possível ler o diretório: {str(e)}")

@app.post("/api/system/dirs", tags=["Sistema"])
def create_directory(req: CreateDirectoryRequest):
    """Cria uma nova pasta no caminho especificado."""
    # Sanitize/normalize parent_path
    parent = os.path.abspath(req.parent_path)
    if not os.path.exists(parent):
        raise HTTPException(status_code=400, detail="Diretório pai não existe.")
    
    # Sanitize folder name
    # Previne path traversal
    folder_name = os.path.basename(req.name).strip()
    if not folder_name or folder_name in (".", "..") or "/" in req.name or "\\" in req.name:
        raise HTTPException(status_code=400, detail="Nome de pasta inválido.")
        
    new_dir_path = os.path.join(parent, folder_name)
    if os.path.exists(new_dir_path):
        raise HTTPException(status_code=400, detail=f"Já existe uma pasta ou arquivo com o nome '{folder_name}' neste caminho.")
        
    try:
        os.makedirs(new_dir_path, exist_ok=True)
        return {
            "status": "success", 
            "message": f"Pasta '{folder_name}' criada com sucesso.",
            "path": new_dir_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar pasta: {str(e)}")

# Servir Frontend do Dashboard
# Serviremos o index.html na raiz e montaremos os estáticos
# Vamos criar o diretório static em seguida
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- MARKITDOWN DISCOVERY ---

class DiscoveryUrlInput(BaseModel):
    url: str

def _ensure_discovery_dirs(project: Project):
    base = os.path.join(project.path, ".discovery")
    entrega = os.path.join(base, "entrega")
    saida = os.path.join(base, "saida")
    os.makedirs(entrega, exist_ok=True)
    os.makedirs(saida, exist_ok=True)
    return entrega, saida

@app.post("/api/projects/{project_id}/discovery/upload", tags=["Discovery"])
async def discovery_upload(
    project_id: int, 
    file: UploadFile = File(...), 
    project: Project = Depends(get_project_or_404)
):
    try:
        from markitdown import MarkItDown
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca markitdown não instalada.")
        
    entrega_dir, saida_dir = _ensure_discovery_dirs(project)
    
    # Save original
    original_path = os.path.join(entrega_dir, file.filename)
    with open(original_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Convert sem LLM para evitar travamentos e crashes com Ollama local
    md = MarkItDown()
    client = None
    model = None
    try:
        # Pede para não truncar as imagens para podermos enviá-las ao LLM
        result = md.convert(original_path, keep_data_uris=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")
        
    import re
    if 'client' in locals() and client:
        def replace_with_llm(match):
            data_uri = match.group(0)
            uri_match = re.search(r'data:image\/[^;]+;base64,[a-zA-Z0-9+/=]+', data_uri)
            if not uri_match:
                return "<imagem-truncada-removida>"
            uri_full = uri_match.group(0)
            try:
                resp = client.chat.completions.create(
                    model=model if provider == "ollama" else "gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Descreva o conteúdo desta imagem ou extraia o texto presente nela em Markdown. Se for um fluxograma, descreva o fluxo."},
                                {"type": "image_url", "image_url": {"url": uri_full}}
                            ]
                        }
                    ]
                )
                return resp.choices[0].message.content
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Erro LLM: {e}")
                return f"<erro-ao-extrair-imagem: {str(e)}>"
        
        text_content = re.sub(r'!\[([^\]]*)\]\(data:image\/[^;]+;base64,[^\)]+\)', replace_with_llm, result.text_content)
        text_content = re.sub(r'!\[([^\]]*)\]\(data:image\/[^;]+;base64[^\)]+\)', r'![\1](<imagem-truncada-removida>)', text_content)
    else:
        text_content = re.sub(r'!\[([^\]]*)\]\(data:image\/[^;]+;base64[^\)]+\)', r'![\1](<imagem-base64-removida>)', result.text_content)
    
    
    # Save output
    basename = os.path.splitext(file.filename)[0]
    out_filename = f"{basename}.md"
    out_path = os.path.join(saida_dir, out_filename)
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(text_content)
        
    return {"message": "Convertido com sucesso", "original": file.filename, "markdown": out_filename}

@app.post("/api/projects/{project_id}/discovery/url", tags=["Discovery"])
def discovery_url(
    project_id: int,
    payload: DiscoveryUrlInput,
    project: Project = Depends(get_project_or_404)
):
    try:
        from markitdown import MarkItDown
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca markitdown não instalada.")
        
    entrega_dir, saida_dir = _ensure_discovery_dirs(project)
    
    config = agent.load_agent_config()
    provider = config.get("provider", "openai")
    
    try:
        from openai import OpenAI
        if provider == "ollama":
            base_url = config.get("ollama_base_url", "http://127.0.0.1:11434")
            model = config.get("model", "llava")
            ollama_api_key = config.get("api_key") or "ollama"
            client = OpenAI(base_url=f"{base_url}/v1", api_key=ollama_api_key)
            md = MarkItDown(llm_client=client, llm_model=model)
        else:
            api_key = config.get("api_key")
            if api_key:
                client = OpenAI(api_key=api_key)
                md = MarkItDown(llm_client=client, llm_model="gpt-4o")
            else:
                md = MarkItDown()
    except Exception:
        md = MarkItDown()
        client = None
        model = None
    try:
        result = md.convert(payload.url, keep_data_uris=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na extração da URL: {str(e)}")
        
    # Create a filename based on URL hash
    url_hash = hashlib.md5(payload.url.encode()).hexdigest()[:8]
    
    import re
    if 'client' in locals() and client:
        def replace_with_llm(match):
            data_uri = match.group(0)
            uri_match = re.search(r'data:image\/[^;]+;base64,[a-zA-Z0-9+/=]+', data_uri)
            if not uri_match:
                return "<imagem-truncada-removida>"
            uri_full = uri_match.group(0)
            try:
                resp = client.chat.completions.create(
                    model=model if provider == "ollama" else "gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Descreva o conteúdo desta imagem ou extraia o texto presente nela em Markdown. Se for um fluxograma, descreva o fluxo."},
                                {"type": "image_url", "image_url": {"url": uri_full}}
                            ]
                        }
                    ]
                )
                return resp.choices[0].message.content
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Erro LLM: {e}")
                return f"<erro-ao-extrair-imagem: {str(e)}>"
        
        text_content = re.sub(r'!\[([^\]]*)\]\(data:image\/[^;]+;base64,[^\)]+\)', replace_with_llm, result.text_content)
        text_content = re.sub(r'!\[([^\]]*)\]\(data:image\/[^;]+;base64[^\)]+\)', r'![\1](<imagem-truncada-removida>)', text_content)
    else:
        text_content = re.sub(r'!\[([^\]]*)\]\(data:image\/[^;]+;base64[^\)]+\)', r'![\1](<imagem-base64-removida>)', result.text_content)
        
    content = f"# Fonte: {payload.url}\n\n{text_content}"
    out_filename = f"url_{url_hash}.md"
    out_path = os.path.join(saida_dir, out_filename)
    
    # Prepend the URL as title
    content = f"# Fonte: {payload.url}\n\n{result.text_content}"
    
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(content)
        
    return {"message": "URL processada com sucesso", "markdown": out_filename}

@app.get("/api/projects/{project_id}/discovery/files", tags=["Discovery"])
def list_discovery_files(project_id: int, project: Project = Depends(get_project_or_404)):
    saida_dir = os.path.join(project.path, ".discovery", "saida")
    if not os.path.exists(saida_dir):
        return []
    
    files = []
    for f in os.listdir(saida_dir):
        if f.endswith(".md"):
            fp = os.path.join(saida_dir, f)
            files.append({
                "filename": f,
                "size": os.path.getsize(fp),
                "mtime": os.path.getmtime(fp),
                "filepath": f".discovery/saida/{f}"
            })
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files

class PricingConfigIn(BaseModel):
    hourly_rate: float
    daily_hours: int


PRICING_DEFAULT_CONFIG = {"hourly_rate": 150.0, "daily_hours": 8}
PRICING_TASK_PATTERN = re.compile(
    r"^\s*-\s*\[([ xX])\]\s*(TASK-[A-Z0-9-]+)\s*:\s*-?\s*(.+?)\s*$",
    re.MULTILINE,
)


def _pricing_config_path(project: Project) -> str:
    return os.path.join(project.path, ".documents", "pricing_config.json")


def _pricing_report_paths(project: Project) -> tuple:
    documents_dir = os.path.join(project.path, ".documents")
    return (
        os.path.join(documents_dir, "estimativa.json"),
        os.path.join(documents_dir, "estimativa.md"),
    )


def _load_pricing_config(project: Project) -> dict:
    config = dict(PRICING_DEFAULT_CONFIG)
    path = _pricing_config_path(project)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config["hourly_rate"] = max(0.01, float(saved.get("hourly_rate", config["hourly_rate"])))
            config["daily_hours"] = max(1, min(24, int(saved.get("daily_hours", config["daily_hours"]))))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    return config


def _read_project_markdown(path: str, limit: int = 120000) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(limit)


def _pricing_task_details(details_content: str) -> dict:
    headings = list(re.finditer(
        r"^##\s+(?:Plano\s*[—-]\s*)?(TASK-[A-Z0-9-]+).*?$",
        details_content or "",
        flags=re.MULTILINE | re.IGNORECASE,
    ))
    details = {}
    for index, match in enumerate(headings):
        start = match.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(details_content)
        details[match.group(1).upper()] = details_content[start:end].strip()[:5000]
    return details


def _collect_pricing_context(project: Project) -> tuple:
    task_path = os.path.join(project.path, ".documents", "task", "task.md")
    details_path = os.path.join(project.path, ".documents", "task", "task.details.md")
    task_content = _read_project_markdown(task_path)
    details_content = _read_project_markdown(details_path)
    details_by_task = _pricing_task_details(details_content)

    tasks = []
    for match in PRICING_TASK_PATTERN.finditer(task_content):
        if match.group(1).lower() == "x":
            continue
        task_id = match.group(2).upper()
        tasks.append({
            "id": task_id,
            "title": match.group(3).strip().rstrip("."),
            "completed": False,
            "details": details_by_task.get(task_id, ""),
        })

    reference_parts = []
    reference_dirs = [
        ("REQ", os.path.join(project.path, ".documents", "spec")),
        ("RF", os.path.join(project.path, ".documents", "functional-requirements")),
    ]
    for label, directory in reference_dirs:
        if not os.path.isdir(directory):
            continue
        for filename in sorted(os.listdir(directory)):
            if not filename.lower().endswith(".md"):
                continue
            content = _read_project_markdown(os.path.join(directory, filename), limit=3500)
            reference_parts.append(f"=== {label}: {filename} ===\n{content}")

    reference_context = "\n\n".join(reference_parts)
    return tasks, reference_context[:30000]


def _infer_pricing_task_type(task: dict) -> str:
    searchable = f"{task.get('id', '')}\n{task.get('title', '')}\n{task.get('details', '')}\n{task.get('rationale', '')}".lower()
    if any(token in searchable for token in ["corrigir", "correção", "correcao", "bug", "erro", "falha", "quebrou", "fix"]):
        return "correction"
    if any(token in searchable for token in ["ajustar", "ajuste", "melhorar", "refinar", "visual", "layout", "spacing", "gap", "copy", "texto", "alinh"]):
        return "adjustment"
    return "implementation"


def _infer_pricing_task_area(task: dict) -> str:
    searchable = f"{task.get('id', '')}\n{task.get('title', '')}\n{task.get('details', '')}\n{task.get('rationale', '')}".lower()
    frontend_tokens = [
        "front", "frontend", "front-end", "ui", "ux", "layout", "visual", "css", "html", "tela",
        "componente", "modal", "drawer", "botão", "botao", "select", "preview", "canvas", "react",
    ]
    backend_tokens = [
        "back", "backend", "back-end", "api", "endpoint", "rota", "server", "servidor", "banco",
        "database", "sql", "schema", "migration", "auth", "token", "arquivo", "persist", "json",
    ]
    infra_tokens = ["docker", "deploy", "caddy", "ssh", "vm", "infra", "domínio", "dominio", "pipeline", "git"]
    qa_tokens = ["teste", "test", "qa", "validação", "validacao", "evidência", "evidencia"]
    has_front = any(token in searchable for token in frontend_tokens)
    has_back = any(token in searchable for token in backend_tokens)
    if any(token in searchable for token in infra_tokens):
        return "infra"
    if has_front and has_back:
        return "fullstack"
    if has_front:
        return "frontend"
    if has_back:
        return "backend"
    if any(token in searchable for token in qa_tokens):
        return "qa"
    return "general"


def _normalize_pricing_task_type(value: Optional[str], task: dict) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "implementacao": "implementation",
        "implementação": "implementation",
        "implementation": "implementation",
        "feature": "implementation",
        "correcao": "correction",
        "correção": "correction",
        "correction": "correction",
        "fix": "correction",
        "bugfix": "correction",
        "ajuste": "adjustment",
        "ajustes": "adjustment",
        "adjustment": "adjustment",
        "improvement": "adjustment",
        "melhoria": "adjustment",
    }
    return aliases.get(normalized) or _infer_pricing_task_type(task)


def _normalize_pricing_task_area(value: Optional[str], task: dict) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "front": "frontend",
        "frontend": "frontend",
        "front_end": "frontend",
        "back": "backend",
        "backend": "backend",
        "back_end": "backend",
        "full": "fullstack",
        "fullstack": "fullstack",
        "full_stack": "fullstack",
        "infra": "infra",
        "devops": "infra",
        "ops": "infra",
        "qa": "qa",
        "test": "qa",
        "teste": "qa",
        "docs": "docs",
        "documentacao": "docs",
        "documentação": "docs",
    }
    return aliases.get(normalized) or _infer_pricing_task_area(task)


def _enrich_pricing_task_classification(task: dict) -> dict:
    enriched = dict(task)
    enriched["task_type"] = _normalize_pricing_task_type(enriched.get("task_type"), enriched)
    enriched["technical_area"] = _normalize_pricing_task_area(enriched.get("technical_area"), enriched)
    return enriched


def _pricing_float_from_aliases(data: dict, aliases: list, default: Optional[float] = None) -> Optional[float]:
    for alias in aliases:
        value = data.get(alias)
        if value is None:
            continue
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            continue
    return default


def _normalize_pricing_complexity(value: Optional[str]) -> str:
    normalized = str(value or "").strip().lower()
    aliases = {
        "baixa": "low",
        "baixo": "low",
        "low": "low",
        "media": "medium",
        "média": "medium",
        "medio": "medium",
        "médio": "medium",
        "medium": "medium",
        "alta": "high",
        "alto": "high",
        "high": "high",
    }
    return aliases.get(normalized, "medium")


def _normalize_saved_pricing_task(saved_task: dict, source_task: dict) -> Optional[dict]:
    if not isinstance(saved_task, dict) or not isinstance(source_task, dict):
        return None
    manual_hours = _pricing_float_from_aliases(
        saved_task,
        ["manual_hours", "sem_ia_horas", "sem_ia_hours", "manual", "without_ai_hours"],
    )
    ai_hours = _pricing_float_from_aliases(
        saved_task,
        ["ai_hours", "com_ia_horas", "com_ia_horas_humanas", "with_ai_hours", "human_ai_hours"],
    )
    if manual_hours is None or ai_hours is None or manual_hours <= 0 or ai_hours <= 0:
        return None
    saved_hours = round(manual_hours - ai_hours, 1)
    rationale = str(
        saved_task.get("rationale")
        or saved_task.get("justificativa")
        or saved_task.get("justificativa_tecnica")
        or saved_task.get("justificativa_técnica")
        or "Estimativa importada do arquivo .documents/estimativa.json."
    ).strip()
    normalized = {
        "id": source_task["id"],
        "title": str(saved_task.get("title") or saved_task.get("titulo") or source_task.get("title") or "").strip(),
        "complexity": _normalize_pricing_complexity(saved_task.get("complexity") or saved_task.get("complexidade")),
        "manual_hours": round(manual_hours, 1),
        "ai_hours": round(ai_hours, 1),
        "task_type": saved_task.get("task_type") or saved_task.get("tipo") or saved_task.get("tipo_task"),
        "technical_area": saved_task.get("technical_area") or saved_task.get("area") or saved_task.get("área"),
        "rationale": rationale[:700],
        "source": saved_task.get("source") or "ai",
        "completed": False,
        "saved_hours": saved_hours,
        "saving_percent": round((saved_hours / manual_hours * 100) if manual_hours else 0, 1),
    }
    return _enrich_pricing_task_classification(normalized)


def _normalize_pricing_estimate(task: dict, candidate: Optional[dict]) -> dict:
    if not isinstance(candidate, dict):
        raise ValueError(f"A IA não retornou estimativa para {task['id']}.")
    try:
        manual_hours = float(candidate.get("manual_hours"))
        ai_hours = float(candidate.get("ai_hours"))
    except (TypeError, ValueError):
        raise ValueError(f"A IA retornou horas inválidas para {task['id']}.")
    if manual_hours <= 0 or ai_hours <= 0:
        raise ValueError(f"A IA retornou horas zeradas ou negativas para {task['id']}.")
    complexity = str(candidate.get("complexity") or "medium").lower()
    if complexity not in {"low", "medium", "high"}:
        raise ValueError(f"A IA retornou complexidade inválida para {task['id']}.")
    rationale = str(candidate.get("rationale") or "").strip()
    if len(rationale) < 20:
        raise ValueError(f"A IA retornou justificativa insuficiente para {task['id']}.")
    return _enrich_pricing_task_classification({
        "id": task["id"],
        "title": task["title"],
        "complexity": complexity,
        "manual_hours": round(manual_hours, 1),
        "ai_hours": round(ai_hours, 1),
        "task_type": candidate.get("task_type"),
        "technical_area": candidate.get("technical_area"),
        "rationale": rationale[:700],
        "source": "ai",
    })


def _pricing_totals(tasks: list, config: dict) -> dict:
    manual_hours = round(sum(float(task["manual_hours"]) for task in tasks), 1)
    ai_hours = round(sum(float(task["ai_hours"]) for task in tasks), 1)
    daily_hours = max(1, int(config["daily_hours"]))
    hourly_rate = float(config["hourly_rate"])
    saved_hours = round(manual_hours - ai_hours, 1)
    return {
        "task_count": len(tasks),
        "manual_hours": manual_hours,
        "ai_hours": ai_hours,
        "manual_days": round(manual_hours / daily_hours, 1),
        "ai_days": round(ai_hours / daily_hours, 1),
        "manual_cost": round(manual_hours * hourly_rate, 2),
        "ai_cost": round(ai_hours * hourly_rate, 2),
        "saved_hours": saved_hours,
        "saved_cost": round(saved_hours * hourly_rate, 2),
        "saving_percent": round((saved_hours / manual_hours * 100) if manual_hours else 0, 1),
    }


def _pricing_markdown(report: dict) -> str:
    totals = report["totals"]
    config = report["config"]
    lines = [
        "# Estimativa Global do Projeto",
        "",
        f"> Gerada em {report['generated_at']} com {totals['task_count']} tarefa(s), valor-hora de R$ {config['hourly_rate']:.2f} e {config['daily_hours']} hora(s) por dia.",
        "",
        "## Resumo Executivo",
        "",
        "| Cenário | Horas | Dias | Custo |",
        "| --- | ---: | ---: | ---: |",
        f"| Sem IA | {totals['manual_hours']:.1f}h | {totals['manual_days']:.1f} | R$ {totals['manual_cost']:.2f} |",
        f"| Com IA | {totals['ai_hours']:.1f}h | {totals['ai_days']:.1f} | R$ {totals['ai_cost']:.2f} |",
        f"| Economia estimada | {totals['saved_hours']:.1f}h | - | R$ {totals['saved_cost']:.2f} ({totals['saving_percent']:.1f}%) |",
        "",
        "## Estimativa por Tarefa",
        "",
        "| Tarefa | Título | Tipo | Área | Complexidade | Sem IA | Com IA | Economia |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for task in report["tasks"]:
        saving = max(0, float(task["manual_hours"]) - float(task["ai_hours"]))
        title = str(task["title"]).replace("|", "\\|")
        lines.append(
            f"| {task['id']} | {title} | {task.get('task_type', 'implementation')} | {task.get('technical_area', 'general')} | {task['complexity']} | {task['manual_hours']:.1f}h | {task['ai_hours']:.1f}h | {saving:.1f}h |"
        )
    lines.extend([
        "",
        "## Premissas",
        "",
        "- A estimativa considera somente as tarefas em aberto de REQs, RFs, Task List e Task Details.",
        "- Tarefas concluídas (`[x]`) não entram no esforço, prazo ou custo projetado.",
        "- Cada task é estimada individualmente a partir do título, Task Details e documentos vinculados.",
        "- A estimativa não usa valores fixos por task e não preenche artificialmente a capacidade diária disponível.",
        "- O cenário Sem IA representa execução manual por profissional técnico.",
        "- O cenário Com IA representa o esforço humano real para orientar, revisar, validar, corrigir e aprovar a execução com apoio do Act IA.",
        "- O ganho com IA é estimado individualmente por task, sem aplicar percentual fixo de redução.",
        "- Horas, custos, capacidade diária e sequência devem ser revisados quando o escopo documental mudar.",
    ])
    if report.get("warning"):
        lines.extend(["", f"> Atenção: {report['warning']}"])
    return "\n".join(lines) + "\n"

@app.get("/api/projects/{project_id}/pricing/config", tags=["Pricing"])
def get_pricing_config(project: Project = Depends(get_project_or_404)):
    return _load_pricing_config(project)

@app.post("/api/projects/{project_id}/pricing/config", tags=["Pricing"])
def save_pricing_config(config: PricingConfigIn, project: Project = Depends(get_project_or_404)):
    if config.hourly_rate <= 0 or config.daily_hours < 1 or config.daily_hours > 24:
        raise HTTPException(status_code=400, detail="Informe valor-hora positivo e jornada entre 1 e 24 horas.")
    config_path = _pricing_config_path(project)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, ensure_ascii=False, indent=2)
    return {"status": "success"}

@app.get("/api/projects/{project_id}/pricing/report", tags=["Pricing"])
def get_pricing_report(project: Project = Depends(get_project_or_404)):
    report_json_path, report_md_path = _pricing_report_paths(project)
    report = None
    markdown = ""
    if os.path.exists(report_json_path):
        try:
            with open(report_json_path, "r", encoding="utf-8") as f:
                report = json.load(f)
        except (OSError, json.JSONDecodeError):
            report = None
    if isinstance(report, dict):
        open_tasks, _ = _collect_pricing_context(project)
        open_tasks_by_id = {task["id"]: task for task in open_tasks}
        open_task_ids = set(open_tasks_by_id)
        report = dict(report)
        normalized_tasks = []
        for task in report.get("tasks", []):
            if not isinstance(task, dict):
                continue
            task_id = str(task.get("id") or "").upper()
            if task_id not in open_task_ids:
                continue
            normalized_task = _normalize_saved_pricing_task(task, open_tasks_by_id[task_id])
            if normalized_task:
                normalized_tasks.append(normalized_task)
        report["tasks"] = normalized_tasks
        report["totals"] = _pricing_totals(
            report["tasks"],
            report.get("config") or _load_pricing_config(project),
        )
        markdown = _pricing_markdown(report)
    else:
        markdown = _read_project_markdown(report_md_path)
    return {"status": "success", "report": report, "markdown": markdown}

@app.post("/api/projects/{project_id}/pricing/generate", tags=["Pricing"])
def generate_pricing_report(project: Project = Depends(get_project_or_404)):
    config = _load_pricing_config(project)
    tasks, reference_context = _collect_pricing_context(project)
    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma tarefa em aberto foi encontrada em .documents/task/task.md. Use o formato - [ ] TASK-REQ-NNNN-001: Título.",
        )

    llm_config = agent.load_agent_config()
    provider = llm_config.get("provider")
    model = llm_config.get("model")
    api_key = llm_config.get("api_key") or ""
    can_use_ai = bool(provider and model and (provider == "ollama" or api_key))
    if not can_use_ai:
        raise HTTPException(
            status_code=400,
            detail="Configure uma IA antes de gerar estimativas. A estimativa não usa contingência automática nem valores fixos por task.",
        )
    estimates_by_id = {}
    estimation_errors = []
    response_schema = {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "complexity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "task_type": {"type": "string", "enum": ["implementation", "correction", "adjustment"]},
                        "technical_area": {"type": "string", "enum": ["frontend", "backend", "fullstack", "infra", "qa", "docs", "general"]},
                        "manual_hours": {"type": "number"},
                        "ai_hours": {"type": "number"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["id", "complexity", "task_type", "technical_area", "manual_hours", "ai_hours", "rationale"],
                },
            }
        },
        "required": ["tasks"],
    }
    system_prompt = (
        "Você é um Engenheiro de Software Sênior especialista em estimativas de projetos. "
        "Estime cada tarefa individualmente a partir do título, Task Details, REQs e RFs. "
        "É proibido usar valores fixos, arbitrários ou padrões como 4h, 8h ou 1 dia por tarefa sem justificativa técnica específica. "
        "A estimativa deve refletir o esforço provável e proporcional à complexidade real da tarefa, sem inflar ou comprimir para preencher a capacidade diária. "
        "Classifique task_type como implementation, correction ou adjustment. "
        "Classifique technical_area como frontend, backend, fullstack, infra, qa, docs ou general. "
        "manual_hours representa execução manual por um profissional, considerando análise, implementação, testes, validação e operação necessária. "
        "ai_hours representa o esforço humano real para orientar, revisar, validar, corrigir e aprovar a execução realizada com apoio do Act IA. "
        "Não calcule ai_hours aplicando percentual fixo sobre manual_hours; estime o ganho individualmente por tarefa. "
        "Considere escopo real, complexidade técnica, arquivos/camadas impactadas, dependências, integrações, riscos, incertezas, validação e esforço operacional do usuário. "
        "Considere também a capacidade diária informada, dependências, sequência e possibilidade de paralelismo, mas nunca ajuste horas para preencher artificialmente a jornada. "
        "Não omita tarefas e não altere IDs. "
        "Responda exclusivamente com JSON compatível com o schema fornecido."
    )
    for task in tasks:
        task_payload = {
            "id": task["id"],
            "title": task["title"],
            "details": task["details"][:7000],
            "completed": bool(task.get("completed")),
        }
        user_prompt = (
            f"Capacidade diária informada pelo usuário: {config['daily_hours']} hora(s)/dia.\n"
            f"Valor-hora informado: R$ {float(config['hourly_rate']):.2f}.\n\n"
            f"Contexto resumido de REQs e RFs:\n{reference_context[:12000]}\n\n"
            "Estime exclusivamente a task abaixo. Analise título e Task Details antes de estimar.\n"
            f"{json.dumps(task_payload, ensure_ascii=False)}"
        )
        try:
            raw = agent.call_llm(
                provider,
                model,
                api_key,
                [{"role": "user", "content": user_prompt}],
                system_prompt,
                ollama_base_url=llm_config.get("ollama_base_url", "http://127.0.0.1:11434"),
                ollama_options={
                    "num_ctx": max(4096, int(llm_config.get("ollama_num_ctx") or 4096)),
                    "num_predict": max(900, int(llm_config.get("ollama_num_predict") or 900)),
                },
                response_schema=response_schema,
            )
            parsed = agent.extract_json(raw)
            candidates = parsed.get("tasks") or []
            candidate = next(
                (item for item in candidates if str(item.get("id") or "").upper() == task["id"]),
                candidates[0] if len(candidates) == 1 else None,
            )
            estimate = _normalize_pricing_estimate(task, candidate)
            estimates_by_id[task["id"]] = estimate
        except Exception as exc:
            estimation_errors.append(f"{task['id']}: {str(exc)[:220]}")

    if estimation_errors:
        raise HTTPException(
            status_code=502,
            detail="A IA não conseguiu gerar estimativas válidas para todas as tasks sem contingência automática. "
            + " | ".join(estimation_errors[:8]),
        )

    normalized_tasks = []
    for task in tasks:
        estimate = _normalize_pricing_estimate(task, estimates_by_id.get(task["id"]))
        estimate["completed"] = bool(task.get("completed"))
        estimate["saved_hours"] = round(estimate["manual_hours"] - estimate["ai_hours"], 1)
        estimate["saving_percent"] = round(
            (estimate["saved_hours"] / estimate["manual_hours"] * 100) if estimate["manual_hours"] else 0,
            1,
        )
        normalized_tasks.append(estimate)

    report = {
        "version": 1,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "project_id": project.id,
        "project_name": project.name,
        "config": config,
        "totals": _pricing_totals(normalized_tasks, config),
        "tasks": normalized_tasks,
        "warning": "",
    }
    markdown = _pricing_markdown(report)
    report_json_path, report_md_path = _pricing_report_paths(project)
    os.makedirs(os.path.dirname(report_json_path), exist_ok=True)
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return {"status": "success", "report": report, "markdown": markdown}

@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
def get_dashboard():
    """Servidor HTML principal do Dashboard do Act IA."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return HTMLResponse(content="<h1>Act IA está rodando!</h1><p>Dashboard HTML não encontrado na pasta <code>static/</code>.</p>", status_code=200)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.ico")) if os.path.exists(os.path.join(STATIC_DIR, "favicon.ico")) else Response(status_code=404)

# Customização do OpenAPI para injetar headers de bypass do Pinggy e Ngrok
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    # Allowlist explícita: expõe exatamente as operações abaixo para o GPT Action.
    # Limite do ChatGPT: 30 operações. Adicionar rotas aqui é uma decisão consciente.
    ALLOWED_OPERATIONS = {
        # Projects
        ("GET",    "/api/projects"),
        ("POST",   "/api/projects"),
        ("DELETE", "/api/projects/{project_id}"),
        # Files
        ("GET",    "/api/projects/{project_id}/files"),
        ("GET",    "/api/projects/{project_id}/files/read"),
        ("POST",   "/api/projects/{project_id}/files/write"),
        ("PATCH",  "/api/projects/{project_id}/files/patch"),
        ("DELETE", "/api/projects/{project_id}/files/delete"),
        # Execute
        ("POST",   "/api/projects/{project_id}/execute"),
        ("GET",    "/api/projects/{project_id}/execute/pending"),
        ("POST",   "/api/projects/{project_id}/execute/pending/{command_id}/approve"),
        ("POST",   "/api/projects/{project_id}/execute/pending/{command_id}/reject"),
        # Database
        ("POST",   "/api/projects/{project_id}/db/query"),
        # Git
        ("GET",    "/api/projects/{project_id}/git/status"),
        ("POST",   "/api/projects/{project_id}/git/init"),
        ("POST",   "/api/projects/{project_id}/git/pull"),
        ("POST",   "/api/projects/{project_id}/git/push"),
        ("POST",   "/api/projects/{project_id}/git/deploy"),
        ("GET",    "/api/projects/{project_id}/git/branches"),
        ("POST",   "/api/projects/{project_id}/git/merge"),
        ("POST",   "/api/projects/{project_id}/git/pullrequest"),
        ("POST",   "/api/projects/{project_id}/git/commit-message/suggest"),
        # SDD
        ("GET",    "/api/projects/{project_id}/sdd/specs"),
        ("GET",    "/api/projects/{project_id}/sdd/specs/{filename}"),
        ("POST",   "/api/projects/{project_id}/sdd/specs"),
        ("DELETE", "/api/projects/{project_id}/sdd/specs/{filename}"),
        ("POST",   "/api/projects/{project_id}/sdd/generate-spec"),
        ("GET",    "/api/projects/{project_id}/sdd/tasks"),
    }

    filtered_routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        for method in methods:
            if (method.upper(), path) in ALLOWED_OPERATIONS:
                filtered_routes.append(route)
                break
            
    openapi_schema = get_openapi(
        title="Act IA software engineer API",
        version="1.0.0",
        description="Interface para GPT Actions interagirem livremente com código, comandos e bancos de dados locais.",
        routes=filtered_routes,
    )
    
    # Configura o servidor padrão (URL padrão)
    openapi_schema["servers"] = [
        {
            "url": "https://ide.builtt.com.br",
            "description": "Servidor local Act IA"
        }
    ]
    
    # Clean up anyOf/null in parameters to prevent ClientResponseError in Custom GPT Actions
    # Inject x-openai-isConsequential: false in all operations to suppress Confirm/Deny buttons
    # (security is enforced at the application layer)
    for path, path_data in openapi_schema.get("paths", {}).items():
        for method, method_data in path_data.items():
            if isinstance(method_data, dict):
                # Suprime os botões Confirm/Deny do GPT Action em todas as operações
                method_data["x-openai-isConsequential"] = False

                if "parameters" in method_data:
                    for param in method_data["parameters"]:
                        schema = param.get("schema", {})
                        if "anyOf" in schema:
                            types = [t for t in schema["anyOf"] if t.get("type") != "null"]
                            if types:
                                param["schema"] = types[0]
                                if "title" in schema:
                                    param["schema"]["title"] = schema["title"]
                                if "description" in schema:
                                    param["schema"]["description"] = schema["description"]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


@app.get("/api/ops-infra-openapi.json", include_in_schema=False)
def ops_infra_openapi():
    """OpenAPI enxuto para GPT Action focado em gestao e operacao de VM/App."""
    allowed_operations = {
        ("GET", "/api/info"),
        ("GET", "/api/projects"),
        ("GET", "/api/projects/{project_id}/ops-infra/detect"),
        ("GET", "/api/projects/{project_id}/ops-infra/vm-access"),
        ("POST", "/api/projects/{project_id}/ops-infra/vm-access"),
        ("POST", "/api/projects/{project_id}/ops-infra/vm-access/test"),
        ("POST", "/api/projects/{project_id}/ops-infra/vm-access/generate-key"),
        ("POST", "/api/projects/{project_id}/ops-infra/vm/directories"),
        ("POST", "/api/projects/{project_id}/ops-infra/vm/directories/create"),
        ("POST", "/api/projects/{project_id}/ops-infra/plan"),
        ("POST", "/api/projects/{project_id}/ops-infra/artifacts"),
        ("POST", "/api/projects/{project_id}/ops-infra/bootstrap"),
        ("POST", "/api/projects/{project_id}/ops-infra/sync"),
        ("POST", "/api/projects/{project_id}/ops-infra/dns/check"),
        ("POST", "/api/projects/{project_id}/ops-infra/health"),
        ("POST", "/api/projects/{project_id}/ops-infra/database/check"),
        ("GET", "/api/projects/{project_id}/ops-infra/env/{environment}"),
        ("POST", "/api/projects/{project_id}/ops-infra/env"),
        ("POST", "/api/projects/{project_id}/ops-infra/env/validate"),
        ("POST", "/api/projects/{project_id}/ops-infra/domain/preview"),
        ("POST", "/api/projects/{project_id}/ops-infra/domain/apply"),
        ("POST", "/api/projects/{project_id}/ops-infra/remote-command"),
    }
    filtered_routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        for method in methods:
            if (method.upper(), path) in allowed_operations:
                filtered_routes.append(route)
                break
    schema = get_openapi(
        title="Act IA Ops Infra API",
        version="1.0.0",
        description="API dedicada para GPT Action operar VM, ambiente, dominio, banco e deploy via Ops Infra.",
        routes=filtered_routes,
    )
    schema["servers"] = [{"url": "https://ide.builtt.com.br", "description": "Servidor Act IA"}]
    for path_data in schema.get("paths", {}).values():
        for method_data in path_data.values():
            if isinstance(method_data, dict):
                method_data["x-openai-isConsequential"] = False
    return schema

from pydantic import BaseModel
class ParameterContentUpdate(BaseModel):
    content: str

@app.get("/api/system/parameters", tags=["System Parameters"])
def get_system_parameters():
    server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(server_root, "gitide_server", "templates")
    
    templates = []
    if os.path.exists(templates_dir):
        templates = [f for f in os.listdir(templates_dir) if f.endswith(".md")]
        
    contracts = [
        "GPT_INSTRUCTIONS.md",
        "OPS_INFRA_OPERATOR.md",
        "PROD_READINESS_VALIDATOR.md",
        "SECURITY_RULES.md"
    ]
    
    return {"status": "success", "templates": templates, "contracts": contracts}

@app.get("/api/system/parameters/content", tags=["System Parameters"])
def get_system_parameter_content(type: str = Query(...), filename: str = Query(...)):
    server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if type == "template":
        filepath = os.path.join(server_root, "gitide_server", "templates", filename)
    else:
        filepath = os.path.join(server_root, filename)
        
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    return {"status": "success", "content": content}

@app.post("/api/system/parameters/content", tags=["System Parameters"])
def update_system_parameter_content(type: str = Query(...), filename: str = Query(...), payload: ParameterContentUpdate = None):
    server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if type == "template":
        filepath = os.path.join(server_root, "gitide_server", "templates", filename)
    else:
        filepath = os.path.join(server_root, filename)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(payload.content)
        
    return {"status": "success"}

