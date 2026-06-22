import os
import json
import re
import subprocess
import requests
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text as sql_text

import gitide_server.vcs as vcs
import gitide_server.git_bridge as git_bridge
from gitide_server.database import Project, ActivityLog, FileSnapshot

CONFIG_DIR = os.path.expanduser("~/.gitide")
AGENT_CONFIG_PATH = os.path.join(CONFIG_DIR, "agent_config.json")

DEFAULT_SYSTEM_PROMPT = """Você é o Agente de IA nativo do GitIDE, integrado localmente ao ambiente de desenvolvimento do usuário.
Seu objetivo é resolver a solicitação do usuário passo a passo usando as ferramentas locais disponíveis.

Para cada turno, você DEVE responder EXCLUSIVAMENTE com um único objeto JSON no formato abaixo.
Qualquer texto explicativo fora do JSON fará a chamada quebrar.

Se você precisa executar uma ação/ferramenta:
{
  "thought": "Seu raciocínio explicando o que vai fazer e por quê",
  "tool": "nome_da_ferramenta",
  "args": {
    "nome_do_parametro": "valor"
  }
}

Se você concluiu a tarefa e tem a resposta final para o usuário:
{
  "thought": "Reflexão final sobre a tarefa executada",
  "final_answer": "Sua resposta final amigável e detalhada em markdown"
}

REGRAS CRÍTICAS:
1. Siga exatamente a assinatura e tipos das ferramentas.
2. Se um arquivo for muito grande, leia-o por fatias de linhas usando start_line e end_line.
3. Se um comando falhar, analise o erro (stderr) e tente corrigi-lo.
4. Seja conciso e cirúrgico em suas alterações.
"""

def load_agent_config():
    if os.path.exists(AGENT_CONFIG_PATH):
        try:
            with open(AGENT_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    # Padrão
    return {
        "provider": "gemini",
        "model": "gemini-1.5-pro",
        "api_key": "",
        "enabled_tools": ["read_file", "write_file", "patch_file", "execute_command", "execute_db_query", "git_status", "git_branches", "git_deploy", "generate_word_document"]
    }

def save_agent_config(config_data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(AGENT_CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=4)

def extract_json(response_text: str) -> dict:
    # Remove marcações de bloco de código markdown
    clean_text = response_text.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    match = re.search(r'(\{.*?\})', clean_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    return json.loads(clean_text)

def call_llm(provider: str, model: str, api_key: str, messages: list, system_prompt: str) -> str:
    """Faz a chamada à API correspondente (Gemini ou OpenAI)."""
    if provider == "gemini":
        # Ajusta histórico de mensagens para o formato do Gemini
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": gemini_contents,
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        res = requests.post(url, json=payload, timeout=40)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
        
    elif provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        openai_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg["role"] == "assistant" else "user"
            openai_messages.append({"role": role, "content": msg["content"]})
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": openai_messages,
            "response_format": {"type": "json_object"}
        }
        res = requests.post(url, json=payload, headers=headers, timeout=40)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
        
    else:
        raise ValueError(f"Provedor de LLM inválido: {provider}")

def execute_agent_tool(db: Session, project: Project, tool_name: str, args: dict) -> str:
    """Executa a ferramenta local correspondente e retorna uma string com o resultado."""
    try:
        if tool_name == "read_file":
            filepath = args.get("filepath")
            start = args.get("start_line")
            end = args.get("end_line")
            
            content = vcs.read_project_file(project.path, filepath)
            lines = content.split('\n')
            total = len(lines)
            
            s_line = start or 1
            e_line = end or total
            
            s_line = max(1, min(s_line, total))
            e_line = max(s_line, min(e_line, total))
            
            sliced = lines[s_line-1:e_line]
            return json.dumps({
                "status": "success",
                "filepath": filepath,
                "total_lines": total,
                "start_line": s_line,
                "end_line": e_line,
                "content": '\n'.join(sliced)
            })
            
        elif tool_name == "write_file":
            filepath = args.get("filepath")
            content = args.get("content")
            
            # Snapshot log
            log = ActivityLog(project_id=project.id, action_type="FILE_WRITE", details=f"[Agente] Escrita no arquivo: {filepath}")
            db.add(log)
            db.commit()
            db.refresh(log)
            
            result = vcs.write_project_file(db, project, filepath, content, activity_log_id=log.id)
            return json.dumps(result)
            
        elif tool_name == "patch_file":
            filepath = args.get("filepath")
            target = args.get("target_content")
            replacement = args.get("replacement_content")
            allow_multiple = args.get("allow_multiple", False)
            
            log = ActivityLog(project_id=project.id, action_type="FILE_PATCH", details=f"[Agente] Patch no arquivo: {filepath}")
            db.add(log)
            db.commit()
            db.refresh(log)
            
            result = vcs.patch_project_file(db, project, filepath, target, replacement, allow_multiple, activity_log_id=log.id)
            return json.dumps(result)
            
        elif tool_name == "execute_command":
            cmd = args.get("command")
            log = ActivityLog(project_id=project.id, action_type="SHELL_EXEC", details=f"[Agente] Comando: {cmd}")
            db.add(log)
            db.commit()
            
            result = subprocess.run(cmd, cwd=project.path, shell=True, text=True, capture_output=True, timeout=30)
            
            log.details += f"\n[Exit: {result.returncode}]\nStdout: {result.stdout[:200]}...\nStderr: {result.stderr[:200]}..."
            db.commit()
            
            # Detecta snapshots de modificações
            vcs.detect_and_snapshot_workspace_changes(db, project, activity_log_id=log.id)
            
            return json.dumps({
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            })
            
        elif tool_name == "execute_db_query":
            db_type = args.get("db_type", "sqlite")
            conn_str = args.get("connection_string")
            query = args.get("query")
            
            # Conexão
            db_url = conn_str
            if db_type == "sqlite":
                if not db_url.startswith("sqlite:///"):
                    db_path = vcs.get_safe_path(project.path, db_url)
                    db_url = f"sqlite:///{db_path}"
            elif db_type == "mysql":
                if db_url.startswith("mysql://"):
                    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
                elif db_url.startswith("mariadb://"):
                    db_url = db_url.replace("mariadb://", "mysql+pymysql://", 1)
            elif db_type == "postgresql":
                if db_url.startswith("postgres://"):
                    db_url = db_url.replace("postgres://", "postgresql://", 1)
                    
            log = ActivityLog(project_id=project.id, action_type="DB_QUERY", details=f"[Agente] Query SQL no banco {db_type}")
            db.add(log)
            db.commit()
            
            engine = create_engine(db_url, echo=False)
            rows = []
            affected = 0
            with engine.connect() as conn:
                res = conn.execute(sql_text(query))
                if res.returns_rows:
                    rows = [dict(row._mapping) for row in res.all()]
                affected = res.rowcount
                conn.commit()
            engine.dispose()
            
            return json.dumps({
                "status": "success",
                "rows_count": len(rows),
                "rows": rows[:50],  # limita para a LLM não estourar contexto
                "rows_affected": affected
            })
            
        elif tool_name == "git_status":
            status = git_bridge.get_git_status(project.path)
            return json.dumps(status)
            
        elif tool_name == "git_branches":
            branches = git_bridge.list_branches(project.path)
            return json.dumps(branches)
            
        elif tool_name == "git_deploy":
            commit_msg = args.get("commit_message")
            branch = args.get("branch")
            
            log = ActivityLog(project_id=project.id, action_type="GIT_DEPLOY", details=f"[Agente] Git Deploy: {commit_msg}")
            db.add(log)
            db.commit()
            
            res = git_bridge.deploy_git(project.path, commit_msg, branch)
            return json.dumps(res)
            
        elif tool_name == "generate_word_document":
            title = args.get("title")
            sections = args.get("sections", [])
            
            from gitide_server.documents import generate_docx
            res = generate_docx(project.path, title, sections)
            
            log = ActivityLog(
                project_id=project.id,
                action_type="DOCUMENT_GENERATED",
                details=f"[Agente] Documento Word gerado: {res.get('filename')}"
            )
            db.add(log)
            db.commit()
            
            return json.dumps(res)
            
        else:
            return json.dumps({"status": "error", "message": f"Ferramenta desconhecida: {tool_name}"})
            
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def run_agent_loop(db: Session, project: Project, config: dict, user_prompt: str):
    """
    Roda a thread do agente em loop.
    Yields chunks de JSON contendo progresso, pensamentos e ações.
    """
    provider = config.get("provider")
    model = config.get("model")
    api_key = config.get("api_key")
    enabled_tools = config.get("enabled_tools", [])
    
    if not api_key:
        yield f"data: {json.dumps({'type': 'error', 'content': 'Chave API não configurada no Agente IA.'})}\n\n"
        return
        
    # Constrói ferramentas ativas e suas assinaturas
    tool_desc = []
    if "read_file" in enabled_tools:
        tool_desc.append("- `read_file(filepath: str, start_line: Optional[int], end_line: Optional[int])`: Lê linhas de um arquivo.")
    if "write_file" in enabled_tools:
        tool_desc.append("- `write_file(filepath: str, content: str)`: Escreve ou sobrescreve o conteúdo total de um arquivo.")
    if "patch_file" in enabled_tools:
        tool_desc.append("- `patch_file(filepath: str, target_content: str, replacement_content: str, allow_multiple: bool)`: Substitui um trecho exato no arquivo.")
    if "execute_command" in enabled_tools:
        tool_desc.append("- `execute_command(command: str)`: Executa comando bash/cmd no terminal da pasta do projeto.")
    if "execute_db_query" in enabled_tools:
        tool_desc.append("- `execute_db_query(db_type: str, connection_string: str, query: str)`: Roda query SQL (sqlite, mysql, postgresql).")
    if "git_status" in enabled_tools:
        tool_desc.append("- `git_status()`: Retorna o status atual dos arquivos no Git.")
    if "git_branches" in enabled_tools:
        tool_desc.append("- `git_branches()`: Lista as branches do repositório.")
    if "git_deploy" in enabled_tools:
        tool_desc.append("- `git_deploy(commit_message: str, branch: Optional[str])`: Adiciona, comita e envia arquivos para o GitHub.")
    if "generate_word_document" in enabled_tools:
        tool_desc.append("- `generate_word_document(title: str, sections: List[dict])`: Gera um documento Word (.docx) estruturado sob .documents. Cada seção tem: 'heading' (opcional), 'text' (obrigatório) e 'type' ('paragraph', 'bullet', 'highlight', 'code' ou 'table').")

    system_prompt = DEFAULT_SYSTEM_PROMPT + "\n\nFERRAMENTAS DISPONÍVEIS:\n" + "\n".join(tool_desc)
    
    messages = [
        {"role": "user", "content": user_prompt}
    ]
    
    max_steps = 10
    step = 0
    
    yield f"data: {json.dumps({'type': 'start', 'prompt': user_prompt})}\n\n"
    
    while step < max_steps:
        step += 1
        yield f"data: {json.dumps({'type': 'status', 'content': f'Raciocinando (Passo {step})...'})}\n\n"
        
        try:
            raw_response = call_llm(provider, model, api_key, messages, system_prompt)
            parsed = extract_json(raw_response)
        except Exception as le:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Erro na chamada do cérebro (LLM): {str(le)}'})}\n\n"
            return
            
        thought = parsed.get("thought", "Analisando...")
        tool = parsed.get("tool")
        args = parsed.get("args", {})
        final_answer = parsed.get("final_answer")
        
        # Envia pensamento
        yield f"data: {json.dumps({'type': 'thought', 'content': thought})}\n\n"
        
        # Caso resposta final
        if final_answer:
            yield f"data: {json.dumps({'type': 'final', 'content': final_answer})}\n\n"
            return
            
        # Caso chamada de ferramenta
        if tool:
            if tool not in enabled_tools:
                tool_result = json.dumps({"status": "error", "message": f"A ferramenta '{tool}' está desabilitada nas configurações do agente."})
            else:
                yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool, 'args': args})}\n\n"
                tool_result = execute_agent_tool(db, project, tool, args)
                
            # Log de tool result
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool, 'result': tool_result})}\n\n"
            
            # Adiciona ao histórico do chat
            messages.append({"role": "assistant", "content": json.dumps(parsed)})
            messages.append({"role": "user", "content": f"Resultado da ferramenta '{tool}': {tool_result}"})
        else:
            # Caso não tenha nem resposta final e nem ferramenta (erro de formatação da LLM)
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": "Erro: Você deve escolher uma ferramenta ou fornecer uma final_answer."})
            
    yield f"data: {json.dumps({'type': 'error', 'content': 'Limite máximo de 10 passos do agente atingido.'})}\n\n"
