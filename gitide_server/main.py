import os
import re
import shutil
import json
import secrets
import subprocess
import sqlite3
import string
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, Depends, HTTPException, Security, status, Query, Response, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from gitide_server.database import init_db, get_db, Project, ActivityLog, FileSnapshot, PendingCommand
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

app = FastAPI(
    title="GitIDE API",
    description="Interface para GPT Actions interagirem livremente com código, comandos e bancos de dados locais.",
    version="1.0.0"
)

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Habilita compressao Gzip
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

security = HTTPBearer()

def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Valida o token enviado pela GPT Action."""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de API GitIDE inválido ou não fornecido."
        )
    return credentials.credentials

# Pydantic Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., description="Nome descritivo do projeto")
    path: str = Field(..., description="Caminho absoluto da pasta do projeto no computador")
    git_remote: Optional[str] = Field(None, description="URL do repositório Git remoto (GitHub/GitLab)")

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

class GitPullRequestCreate(BaseModel):
    title: str = Field(..., description="Título do Pull Request")
    base: str = Field(..., description="Branch de destino (ex: main, master)")
    body: Optional[str] = Field(None, description="Descrição do Pull Request")

class AgentConfigInput(BaseModel):
    provider: str
    model: str
    api_key: str
    enabled_tools: List[str]

class AgentChatRequest(BaseModel):
    prompt: str

class DocumentSection(BaseModel):
    heading: Optional[str] = Field("", description="Título da seção")
    text: str = Field(..., description="Conteúdo de texto da seção")
    type: str = Field("paragraph", description="Tipo de formatação (paragraph, bullet, highlight, code, table)")

class DocumentCreateRequest(BaseModel):
    title: str = Field(..., description="Título principal do documento")
    sections: List[DocumentSection] = Field(..., description="Lista de seções ordenadas do documento")

class CreateDirectoryRequest(BaseModel):
    parent_path: str = Field(..., description="Caminho do diretório pai")
    name: str = Field(..., description="Nome da nova pasta a ser criada")

# SDD Models
class SddSpecSaveRequest(BaseModel):
    filename: str = Field(..., description="Nome do arquivo da especificação (ex: auth.md)")
    content: str = Field(..., description="Conteúdo em Markdown da especificação")

class SddSpecGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt descrevendo a feature a ser especificada")
    title: Optional[str] = Field(None, description="Título opcional para a especificação")

class SddCriteriaItem(BaseModel):
    line_no: int = Field(..., description="Número da linha (1-indexed) do critério no Markdown")
    checked: bool = Field(..., description="Estado de verificação do critério")

class SddCriteriaUpdateRequest(BaseModel):
    criteria: List[SddCriteriaItem] = Field(..., description="Lista de critérios a serem atualizados")

class SddTestGenerateRequest(BaseModel):
    filename: str = Field(..., description="Nome do arquivo de especificação (.md)")
    framework: str = Field(..., description="Framework de teste (ex: pytest, jest, phpunit, mocha)")

# Dependência para buscar projeto do DB
def get_project_or_404(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Projeto com ID {project_id} não encontrado.")
    return project

# --- ENDPOINTS DA API PARA O GPT / DASHBOARD ---

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


# Projetos
@app.get("/api/projects", tags=["Projetos"])
def list_projects(db: Session = Depends(get_db)):
    """Lista todos os projetos cadastrados."""
    return db.query(Project).all()

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
                
    # Garante que o arquivo GPT_INSTRUCTIONS.md existe na raiz do projeto
    gpt_instructions_dest = os.path.join(project_in.path, "GPT_INSTRUCTIONS.md")
    if not os.path.exists(gpt_instructions_dest):
        server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gpt_instructions_src = os.path.join(server_root, "GPT_INSTRUCTIONS.md")
        if os.path.exists(gpt_instructions_src):
            try:
                shutil.copy2(gpt_instructions_src, gpt_instructions_dest)
            except Exception as e:
                print(f"Erro ao copiar GPT_INSTRUCTIONS.md para o workspace: {str(e)}")

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
    """Remove o cadastro do projeto do GitIDE (não apaga os arquivos do computador)."""
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
        files = vcs.list_project_files(project.path)
        return {"status": "success", "files": files}
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
        content = vcs.read_project_file(project.path, filepath)
        lines = content.split('\n')
        total_lines = len(lines)
        
        # Limite máximo de linhas por leitura para evitar estourar o limite de resposta do ChatGPT (100KB)
        MAX_READ_LINES = 250
        
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
    Exclui um arquivo do computador e cria um snapshot de backup.
    Requer autenticação Bearer Token para chamadas externas.
    """
    try:
        log = ActivityLog(
            project_id=project.id,
            action_type="FILE_DELETE",
            details=f"Exclusão do arquivo: {filepath}"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        result = vcs.delete_project_file(db, project, filepath, activity_log_id=log.id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
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
    is_dashboard = request.headers.get("x-gitide-source") == "dashboard" or request.headers.get("X-GitIDE-Source") == "dashboard"
    
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
                    "Por favor, peça ao usuário para aprovar a execução deste comando no painel Web do GitIDE. "
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

        # Registra no log do GitIDE
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

@app.post("/api/projects/{project_id}/git/init", tags=["Git Bridge"])
def git_init(project: Project = Depends(get_project_or_404), db: Session = Depends(get_db), _ = Depends(get_api_key)):
    """Inicializa um repositório Git ou vincula a URL remota configurada."""
    try:
        result = git_bridge.init_git(project.path, project.git_remote)
        
        log = ActivityLog(
            project_id=project.id,
            action_type="GIT_INIT",
            details=f"Git inicializado com remoto: {project.git_remote}"
        )
        db.add(log)
        db.commit()
        
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
        "User-Agent": "GitIDE"
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
                "User-Agent": "GitIDE"
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
                "User-Agent": "GitIDE"
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

# --- ENDPOINTS DO SPEC-DRIVEN DEVELOPMENT (SDD) ---

@app.get("/api/projects/{project_id}/sdd/specs", tags=["Spec-Driven Development"])
def list_sdd_specs(project: Project = Depends(get_project_or_404)):
    """Lista todas as especificações (.md) no diretório .documents/specs do projeto."""
    specs_dir = os.path.join(project.path, ".documents", "specs")
    if not os.path.exists(specs_dir):
        return []
    
    specs = []
    try:
        for entry in os.scandir(specs_dir):
            if entry.is_file() and entry.name.endswith(".md"):
                stat = entry.stat()
                title = entry.name
                
                # Tenta extrair o primeiro header # do arquivo
                try:
                    with open(entry.path, "r", encoding="utf-8") as f:
                        for line in f:
                            line_stripped = line.strip()
                            if line_stripped.startswith("# "):
                                title = line_stripped.lstrip("# ").strip()
                                break
                except Exception:
                    pass
                
                specs.append({
                    "filename": entry.name,
                    "title": title,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Ordena pelos mais recentes
        specs.sort(key=lambda x: x["modified_at"], reverse=True)
        return specs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar especificações: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/specs/{filename}", tags=["Spec-Driven Development"])
def get_sdd_spec(filename: str, project: Project = Depends(get_project_or_404)):
    """Retorna o conteúdo de uma especificação específica."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    spec_path = os.path.join(project.path, ".documents", "specs", filename)
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")
        
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler especificação: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/specs", tags=["Spec-Driven Development"])
def save_sdd_spec(
    req: SddSpecSaveRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Cria ou atualiza uma especificação manualmente."""
    filename = req.filename
    if ".." in filename or "/" in filename or "\\" in filename or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido. Deve terminar com .md")
        
    specs_dir = os.path.join(project.path, ".documents", "specs")
    os.makedirs(specs_dir, exist_ok=True)
    spec_path = os.path.join(specs_dir, filename)
    
    try:
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(req.content)
            
        # Log da ação no banco de dados
        log = ActivityLog(
            project_id=project.id,
            action_type="SPEC_SAVED",
            details=f"Especificação salva: {filename}"
        )
        db.add(log)
        db.commit()
        
        return {"status": "success", "message": "Especificação salva com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar especificação: {str(e)}")

@app.delete("/api/projects/{project_id}/sdd/specs/{filename}", tags=["Spec-Driven Development"])
def delete_sdd_spec(
    filename: str,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Deleta uma especificação específica."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    spec_path = os.path.join(project.path, ".documents", "specs", filename)
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")
        
    try:
        os.remove(spec_path)
        
        # Log da ação no banco de dados
        log = ActivityLog(
            project_id=project.id,
            action_type="SPEC_DELETED",
            details=f"Especificação deletada: {filename}"
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
        
    system_prompt = (
        "Você é um Engenheiro de Software Sênior especialista em Spec-Driven Development (SDD).\n"
        "Sua tarefa é gerar uma especificação técnica detalhada em formato Markdown com base no prompt do usuário.\n"
        "Você DEVE retornar a resposta formatada estritamente como um objeto JSON estruturado contendo:\n"
        "1. \"title\": O título da funcionalidade.\n"
        "2. \"filename\": Sugestão de nome de arquivo amigável terminando em .md (ex: user_auth.md, shopping_cart.md).\n"
        "3. \"markdown\": A especificação técnica completa em Markdown.\n\n"
        "A especificação técnica em Markdown DEVE conter as seguintes seções estruturadas:\n"
        "- # [Título da Funcionalidade]\n"
        "- ## 1. Escopo & Objetivos\n"
        "- ## 2. Requisitos Funcionais & Não-Funcionais\n"
        "- ## 3. Arquitetura de Dados / Modelo Proposto (ex: tabelas, campos, tipos)\n"
        "- ## 4. Fluxo de Execução & APIs / Endpoints\n"
        "- ## 5. Critérios de Aceitação (Utilize obrigatoriamente caixas de seleção Markdown '- [ ]' para cada critério)\n\n"
        "Retorne estritamente um objeto JSON. Não adicione tags de bloco ```json ou outro texto fora do JSON."
    )
    
    messages = [
        {"role": "user", "content": f"Por favor, gere uma especificação completa para a seguinte ideia de funcionalidade:\n\n{req.prompt}"}
    ]
    
    try:
        raw_resp = agent.call_llm(provider, model, api_key, messages, system_prompt)
        parsed = agent.extract_json(raw_resp)
        
        title = parsed.get("title", req.title or "Especificação Gerada")
        filename = parsed.get("filename", "spec.md")
        if not filename.endswith(".md"):
            filename += ".md"
            
        # Limpa o filename contra caminhos maliciosos
        filename = os.path.basename(filename)
        
        markdown_content = parsed.get("markdown", "")
        
        specs_dir = os.path.join(project.path, ".documents", "specs")
        os.makedirs(specs_dir, exist_ok=True)
        spec_path = os.path.join(specs_dir, filename)
        
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        # Log da ação
        log = ActivityLog(
            project_id=project.id,
            action_type="SPEC_GENERATED",
            details=f"Especificação gerada por IA: {filename}"
        )
        db.add(log)
        db.commit()
        
        return {
            "status": "success",
            "title": title,
            "filename": filename,
            "markdown": markdown_content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar especificação por IA: {str(e)}")

@app.get("/api/projects/{project_id}/sdd/specs/{filename}/criteria", tags=["Spec-Driven Development"])
def get_sdd_spec_criteria(filename: str, project: Project = Depends(get_project_or_404)):
    """Extrai todos os critérios de aceitação de uma especificação Markdown."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    spec_path = os.path.join(project.path, ".documents", "specs", filename)
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")
        
    criteria = []
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Procura por "- [ ]" ou "- [x]" ou "- [X]"
            match = re.match(r"^\-\s*\[([ xX])\]\s*(.*)", line_stripped)
            if match:
                checked = match.group(1).lower() == "x"
                text = match.group(2).strip()
                criteria.append({
                    "id": i,
                    "line_no": i + 1,  # 1-indexed para facilitar leitura
                    "text": text,
                    "checked": checked
                })
        return {"filename": filename, "criteria": criteria}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair critérios de aceitação: {str(e)}")

@app.post("/api/projects/{project_id}/sdd/specs/{filename}/criteria", tags=["Spec-Driven Development"])
def update_sdd_spec_criteria(
    filename: str,
    req: SddCriteriaUpdateRequest,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
    _ = Depends(get_api_key)
):
    """Atualiza o estado (checked/unchecked) de critérios de aceitação específicos no arquivo Markdown."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
        
    spec_path = os.path.join(project.path, ".documents", "specs", filename)
    if not os.path.exists(spec_path):
        raise HTTPException(status_code=404, detail="Especificação não encontrada.")
        
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Cria um mapeamento de line_no -> checked
        updates = {item.line_no: item.checked for item in req.criteria}
        
        for line_no, checked in updates.items():
            idx = line_no - 1  # 0-indexed para a lista de linhas
            if 0 <= idx < len(lines):
                line = lines[idx]
                # Preserva a indentação e substitui o checkbox
                indent_match = re.match(r"^(\s*)\-\s*\[[ xX]\](.*)", line)
                if indent_match:
                    indent = indent_match.group(1)
                    rest = indent_match.group(2)
                    box = "[x]" if checked else "[ ]"
                    lines[idx] = f"{indent}- {box}{rest}\n"
                    
        with open(spec_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
            
        return {"status": "success", "message": "Critérios de aceitação atualizados no disco com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar critérios de aceitação: {str(e)}")

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
        
    spec_path = os.path.join(project.path, ".documents", "specs", req.filename)
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
            "Você deve mapear cada Critério de Aceitação da especificação para um ou mais casos de teste no código.\n\n"
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

@app.get("/api/agent/config", tags=["Agente IA"])
def get_agent_config():
    """Retorna as configurações atuais do agente IA."""
    return agent.load_agent_config()

@app.post("/api/agent/config", tags=["Agente IA"])
def save_agent_config(config_in: AgentConfigInput):
    """Salva as configurações do agente IA."""
    agent.save_agent_config(config_in.model_dump())
    return {"status": "success", "message": "Configurações do agente salvas."}

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
    return StreamingResponse(
        agent.run_agent_loop(db, project, config, req.prompt),
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

@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
def get_dashboard():
    """Servidor HTML principal do Dashboard do GitIDE."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return HTMLResponse(content="<h1>GitIDE está rodando!</h1><p>Dashboard HTML não encontrado na pasta <code>static/</code>.</p>", status_code=200)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.ico")) if os.path.exists(os.path.join(STATIC_DIR, "favicon.ico")) else Response(status_code=404)

# Customização do OpenAPI para injetar headers de bypass do Pinggy e Ngrok
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    # Filtra as rotas para expor menos de 30 operações para o GPT Action (evita erro de limite do ChatGPT)
    exclude_prefixes = [
        "/api/github/auth",
        "/api/github/repos",
        "/api/agent/config",
        "/api/system/dirs",
    ]
    exclude_suffixes = [
        "/rollback",
        "/diff",
        "/logs",
        "/snapshots",
        "/git/token",
        "/git/merge/abort",
        "/documents/{filename}/preview",
        "/documents/upload",
        "/agent/run",
    ]
    
    filtered_routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        should_exclude = False
        
        # Filtra por prefixo
        for prefix in exclude_prefixes:
            if path.startswith(prefix):
                should_exclude = True
                break
                
        if not should_exclude:
            # Filtra por sufixo
            for suffix in exclude_suffixes:
                if path.endswith(suffix):
                    should_exclude = True
                    break
                    
        # Filtra a rota raiz do Dashboard
        if path == "/":
            should_exclude = True
            
        if not should_exclude:
            filtered_routes.append(route)
            
    openapi_schema = get_openapi(
        title="GitIDE API",
        version="1.0.0",
        description="Interface para GPT Actions interagirem livremente com código, comandos e bancos de dados locais.",
        routes=filtered_routes,
    )
    
    # Configura o servidor padrão (URL padrão)
    openapi_schema["servers"] = [
        {
            "url": "https://ide.builtt.com.br",
            "description": "Servidor local GitIDE"
        }
    ]
    
    # Clean up anyOf/null in parameters to prevent ClientResponseError in Custom GPT Actions
    for path, path_data in openapi_schema.get("paths", {}).items():
        for method, method_data in path_data.items():
            if isinstance(method_data, dict) and "parameters" in method_data:
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

