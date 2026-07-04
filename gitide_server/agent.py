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

DEFAULT_SYSTEM_PROMPT = """Você é o Agente de IA nativo do Act IA software engineer, integrado localmente ao ambiente de desenvolvimento do usuário.
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
5. Antes de qualquer execução técnica de código, respeite o fluxo Harness documentado em GPT_INSTRUCTIONS.md.
6. Para operações de VM, deploy, domínio, banco, Docker, Caddy, health check ou comandos remotos, use exclusivamente as ferramentas ops_infra_* disponíveis. Nunca responda que não tem acesso ao Ops Infra se essas ferramentas estiverem listadas.
7. Não pule etapas: analise, gere/atualize documentação quando aplicável, aguarde validação quando o fluxo exigir, execute uma tarefa por vez e verifique o resultado.
8. Não exponha secrets, senhas, chaves privadas ou tokens em respostas finais, pensamentos ou argumentos.
9. `final_answer` NÃO é ferramenta. Nunca use `"tool": "final_answer"`. Para concluir, use somente o campo `"final_answer"`.
10. Nunca chame ferramenta sem preencher todos os argumentos obrigatórios.
11. IDs no formato `QA-XXXXXXXX` são anotações da Central QA. Para qualquer pedido envolvendo um QA ID, use primeiro `qa_get_annotation(annotation_id)`.
12. Se o contrato operacional já trouxe conteúdo de REQ, QA ou TASK, use esse conteúdo como fonte inicial. Não tente reler arquivos aleatórios antes de aplicar o roteamento informado.
13. Ao criar ou revisar documentos Harness, use sempre os templates oficiais completos. É proibido gerar REQ, Design, DRI, Task List ou Task Details em formato resumido.
14. Um REQ com apenas Título, Descrição, Detalhes Técnicos e Prioridade/Severidade é inválido. Todo REQ deve conter as seções 1.1 a 1.10 do template oficial.
15. Para QA visual/layout enquadrado na exceção controlada, não crie REQ resumido. Crie somente TASK-QA em `.documents/task/task.md` e plano completo em `.documents/task/task.details.md`.
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
        "ollama_base_url": "http://127.0.0.1:11434",
        "ollama_performance_mode": "balanced",
        "ollama_num_ctx": 4096,
        "ollama_num_predict": 768,
        "enabled_tools": ["read_file", "write_file", "patch_file", "execute_command", "execute_db_query", "git_status", "git_branches", "git_deploy", "generate_word_document"]
    }

def _safe_read_instruction(project_path: str, filename: str, max_chars: int = 12000) -> str:
    if not re.match(r"^[A-Z0-9_./-]+\.md$", filename, re.IGNORECASE):
        return ""
    path = os.path.abspath(os.path.join(project_path, filename))
    root = os.path.abspath(project_path)
    if not path.startswith(root):
        return ""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        return content
    except Exception:
        return ""


def _safe_read_instruction(project_path: str, filename: str, max_chars: int = 12000) -> str:
    if not re.match(r"^[A-Z0-9_./-]+\.md$", filename, re.IGNORECASE):
        return ""
    path = os.path.abspath(os.path.join(project_path, filename))
    root = os.path.abspath(project_path)
    if not path.startswith(root):
        return ""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        return content
    except Exception:
        return ""

def save_agent_config(config_data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(AGENT_CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=4)

def extract_json(response_text: str) -> dict:
    # Remove marcações de bloco de código markdown
    clean_text = (response_text or "").strip()
    if not clean_text:
        raise ValueError("O modelo não retornou nenhuma resposta (string vazia). Verifique a conexão com a API ou se o provedor está sobrecarregado.")
        
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
            
    try:
        return json.loads(clean_text)
    except Exception as e:
        # Pega as primeiras 100 caracteres para depuração
        snippet = clean_text[:100].replace('\n', ' ')
        raise ValueError(f"O modelo retornou texto que não é um JSON válido: '{snippet}...'. Detalhes: {e}")

def _compact_tool_result_for_local_model(tool_result: str, max_chars: int = 2200) -> str:
    try:
        data = json.loads(tool_result)
        for key in ["private_key", "password", "token", "api_key"]:
            if key in data:
                data[key] = ""
        if isinstance(data.get("vm_access"), dict):
            data["vm_access"].pop("private_key", None)
            data["vm_access"].pop("password", None)
        for key in ["stdout", "stderr", "body_preview"]:
            if isinstance(data.get(key), str) and len(data[key]) > 700:
                data[key] = data[key][:700] + "... [truncado]"
        compact = json.dumps(data, ensure_ascii=False)
        return compact[:max_chars] + ("... [truncado]" if len(compact) > max_chars else "")
    except Exception:
        return tool_result[:max_chars] + ("... [truncado]" if len(tool_result) > max_chars else "")

def call_llm(provider: str, model: str, api_key: str, messages: list, system_prompt: str, ollama_base_url: str = "http://127.0.0.1:11434", ollama_options: dict = None) -> str:
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

    elif provider == "ollama":
        base_url = (ollama_base_url or "http://127.0.0.1:11434").rstrip("/")
        if not model:
            raise ValueError("Modelo Ollama não configurado.")
        ollama_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = "assistant" if msg["role"] == "assistant" else "user"
            ollama_messages.append({"role": role, "content": msg["content"]})

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                **(ollama_options or {})
            },
            "keep_alive": "10m"
        }
        res = requests.post(f"{base_url}/api/chat", json=payload, timeout=120)
        res.raise_for_status()
        data = res.json()
        return data.get("message", {}).get("content", "")
        
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

def run_agent_loop(db: Session, project: Project, config: dict, user_prompt: str, conversation_history: list = None, extra_tools: dict = None, extra_tool_descriptions: list = None, system_context: str = ""):
    """
    Roda a thread do agente em loop.
    Yields chunks de JSON contendo progresso, pensamentos e ações.
    """
    provider = config.get("provider")
    model = config.get("model")
    api_key = config.get("api_key")
    ollama_base_url = config.get("ollama_base_url") or "http://127.0.0.1:11434"
    ollama_performance_mode = config.get("ollama_performance_mode") or "balanced"
    ollama_num_ctx = int(config.get("ollama_num_ctx") or 4096)
    ollama_num_predict = int(config.get("ollama_num_predict") or 768)
    if ollama_performance_mode == "fast":
        ollama_num_ctx = min(ollama_num_ctx, 2048)
        ollama_num_predict = min(ollama_num_predict, 384)
    elif ollama_performance_mode == "deep":
        ollama_num_ctx = max(ollama_num_ctx, 8192)
        ollama_num_predict = max(ollama_num_predict, 1200)
    enabled_tools = config.get("enabled_tools", [])
    extra_tools = extra_tools or {}
    extra_tool_descriptions = extra_tool_descriptions or []
    
    if provider != "ollama" and not api_key:
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
    tool_desc.extend(extra_tool_descriptions)

    is_ollama = provider == "ollama"
    instruction_chars = 2500 if is_ollama else 12000
    audit_chars = 1200 if is_ollama else 8000
    harness_rules = _safe_read_instruction(project.path, "GPT_INSTRUCTIONS.md", max_chars=instruction_chars)
    ops_rules = _safe_read_instruction(project.path, "OPS_INFRA_OPERATOR.md", max_chars=instruction_chars)
    prod_rules = _safe_read_instruction(project.path, "PROD_READINESS_VALIDATOR.md", max_chars=audit_chars)
    security_rules = _safe_read_instruction(project.path, "SECURITY_RULES.md", max_chars=audit_chars)
    if is_ollama:
        tool_desc = tool_desc[:18]

    system_prompt = (
        DEFAULT_SYSTEM_PROMPT
        + "\n\nFERRAMENTAS DISPONÍVEIS:\n"
        + "\n".join(tool_desc)
        + "\n\nCONTRATO OPERACIONAL DO PROJETO:\n"
        + (system_context or "Sem contexto operacional extra.")
        + "\n\nGPT_INSTRUCTIONS.md:\n"
        + (harness_rules or "Arquivo não encontrado. Se a tarefa for técnica, leia/crie o documento antes de avançar.")
        + "\n\nOPS_INFRA_OPERATOR.md:\n"
        + (ops_rules or "Arquivo não encontrado. Para Ops Infra, use as ferramentas nativas ops_infra_* e preserve validações.")
        + "\n\nPROD_READINESS_VALIDATOR.md:\n"
        + (prod_rules or "Arquivo não encontrado.")
        + "\n\nSECURITY_RULES.md:\n"
        + (security_rules or "Arquivo não encontrado.")
    )
    if is_ollama:
        system_prompt += (
            "\n\nMODO OLLAMA PERFORMANCE:\n"
            "- Responda JSON curto e válido.\n"
            "- Use pensamento com no máximo 1 frase.\n"
            "- Só chame ferramenta quando necessário.\n"
            "- Se a resposta puder ser direta, use final_answer sem consultar ferramentas.\n"
            "- final_answer é um campo JSON, não uma ferramenta.\n"
            "- Não use tool sem args obrigatórios; se faltar informação, pergunte usando final_answer.\n"
            "- Não resuma resultados longos; diga o essencial e próximo passo.\n"
        )
    
    messages = []
    for item in (conversation_history or [])[-12:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content[:4000]})
    messages.append({"role": "user", "content": user_prompt})
    
    max_steps = 12 if is_ollama else 50
    step = 0
    
    yield f"data: {json.dumps({'type': 'start', 'prompt': user_prompt})}\n\n"
    
    last_thought = ""
    last_tool = ""
    last_tool_result = ""

    while step < max_steps:
        step += 1
        yield f"data: {json.dumps({'type': 'status', 'content': f'Raciocinando (Passo {step})...'})}\n\n"
        
        try:
            raw_response = call_llm(
                provider,
                model,
                api_key,
                messages,
                system_prompt,
                ollama_base_url=ollama_base_url,
                ollama_options={
                    "num_ctx": ollama_num_ctx,
                    "num_predict": ollama_num_predict,
                    "num_thread": 0,
                    "repeat_penalty": 1.08,
                } if is_ollama else None
            )
            parsed = extract_json(raw_response)
        except Exception as le:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Erro na chamada do cérebro (LLM): {str(le)}'})}\n\n"
            return
            
        thought = parsed.get("thought", "Analisando...")
        tool = parsed.get("tool")
        args = parsed.get("args", {})
        final_answer = parsed.get("final_answer")
        last_thought = str(thought or "")

        if tool == "final_answer":
            final_answer = (
                parsed.get("final_answer")
                or (args.get("content") if isinstance(args, dict) else None)
                or (args.get("message") if isinstance(args, dict) else None)
                or (args.get("answer") if isinstance(args, dict) else None)
                or parsed.get("content")
                or thought
            )
            tool = None

        # Envia pensamento
        yield f"data: {json.dumps({'type': 'thought', 'content': thought})}\n\n"
        
        # Caso resposta final
        if final_answer:
            yield f"data: {json.dumps({'type': 'final', 'content': final_answer})}\n\n"
            return
            
        # Caso chamada de ferramenta
        if tool:
            if tool in extra_tools:
                yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool, 'args': args})}\n\n"
                tool_result = extra_tools[tool](db, project, args)
            elif tool not in enabled_tools:
                tool_result = json.dumps({"status": "error", "message": f"A ferramenta '{tool}' está desabilitada nas configurações do agente."})
            else:
                yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool, 'args': args})}\n\n"
                tool_result = execute_agent_tool(db, project, tool, args)

                
            model_tool_result = _compact_tool_result_for_local_model(tool_result) if is_ollama else tool_result

            # Log de tool result
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool, 'result': model_tool_result})}\n\n"
            last_tool = str(tool or "")
            last_tool_result = str(model_tool_result or "")
            
            # Adiciona ao histórico do chat
            messages.append({"role": "assistant", "content": json.dumps(parsed)})
            messages.append({"role": "user", "content": f"Resultado da ferramenta '{tool}': {model_tool_result}"})
        else:
            # Caso não tenha nem resposta final e nem ferramenta (erro de formatação da LLM)
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": "Erro de contrato: responda com uma ferramenta válida ou com o campo final_answer. Se não houver próxima ação objetiva, finalize com final_answer."})

    summary = (
        f"Interrompi a execução após atingir o limite operacional de {max_steps} passos para evitar loop.\n\n"
        f"**Último pensamento registrado:** {last_thought or 'Não informado.'}\n\n"
        f"**Última ferramenta usada:** {last_tool or 'Nenhuma.'}\n\n"
        "Para continuar com segurança, confirme a próxima ação objetiva ou informe a task/QA/REQ que devo executar. "
        "Se a intenção era executar um QA, envie o ID no formato `QA-XXXXXXXX` para eu buscar a anotação antes de qualquer comando."
    )
    if last_tool_result:
        summary += f"\n\n**Último resultado resumido:** `{last_tool_result[:900]}`"
    yield f"data: {json.dumps({'type': 'final', 'content': summary})}\n\n"
