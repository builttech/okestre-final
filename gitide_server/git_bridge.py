import os
import json
from git import Repo, GitCommandError

CONFIG_PATH = os.path.join(os.path.abspath(os.getenv("GITIDE_DATA_DIR", os.path.expanduser("~/.gitide"))), "config.json")

def get_github_token() -> str:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return config.get("github_access_token", "")
        except Exception:
            pass
    return ""

def get_authenticated_git_url(url: str, token: str) -> str:
    if not token or not url:
        return url
    
    clean_url = url
    if "@" in url:
        prefix = "https://" if url.startswith("https://") else "http://"
        remainder = url[len(prefix):]
        if "@" in remainder:
            clean_url = prefix + remainder.split("@", 1)[1]
            
    if clean_url.startswith("https://github.com/"):
        return clean_url.replace("https://github.com/", f"https://{token}@github.com/")
    elif clean_url.startswith("http://github.com/"):
        return clean_url.replace("http://github.com/", f"http://{token}@github.com/")
        
    return clean_url

def update_remote_url_with_token(repo: Repo):
    try:
        origin = repo.remote(name="origin")
        url = origin.url
        token = get_github_token()
        if token and ("github.com" in url):
            # Detecta se a URL já possui credenciais configuradas
            has_credentials = False
            current_token = ""
            if "@" in url:
                prefix = "https://" if url.startswith("https://") else "http://"
                remainder = url[len(prefix):]
                if "@" in remainder:
                    has_credentials = True
                    current_token = remainder.split("@", 1)[0]
            
            # Se já possui credenciais e elas não foram geradas pelo OAuth do GitIDE (não começam com gho_),
            # não sobrescrevemos para respeitar a configuração manual do usuário (PAT ghp_...)
            if has_credentials and not current_token.startswith("gho_"):
                return
                
            auth_url = get_authenticated_git_url(url, token)
            if url != auth_url:
                origin.set_url(auth_url)
    except Exception:
        pass

def get_repo(project_path: str) -> Repo:
    """Retorna uma instância de Repo se o diretório for um repositório Git."""
    abs_path = os.path.abspath(project_path)
    if not os.path.exists(os.path.join(abs_path, ".git")):
        raise ValueError("Este diretório não é um repositório Git. Use init_git primeiro.")
    return Repo(abs_path)

def init_git(project_path: str, remote_url: str = None) -> dict:
    """Inicializa um novo repositório Git local e opcionalmente adiciona a origem remota."""
    abs_path = os.path.abspath(project_path)
    os.makedirs(abs_path, exist_ok=True)
    
    if os.path.exists(os.path.join(abs_path, ".git")):
        repo = Repo(abs_path)
        status = "existente"
    else:
        repo = Repo.init(abs_path)
        status = "inicializado"
        
    if remote_url:
        # Verifica se 'origin' já existe
        try:
            origin = repo.remote(name="origin")
            # Se a URL for diferente, atualiza
            if origin.url != remote_url:
                repo.delete_remote(origin)
                repo.create_remote("origin", remote_url)
        except ValueError:
            repo.create_remote("origin", remote_url)
            
    return {
        "status": "success",
        "action": f"repositorio_{status}",
        "current_branch": repo.active_branch.name if not repo.head.is_detached else "DETACHED",
        "remotes": [r.name for r in repo.remotes]
    }

def clone_git(remote_url: str, target_path: str) -> dict:
    """Clona um repositório Git remoto para um diretório local."""
    abs_path = os.path.abspath(target_path)
    if os.path.exists(abs_path) and os.listdir(abs_path):
        raise ValueError("O diretório de destino não está vazio.")
        
    os.makedirs(abs_path, exist_ok=True)
    try:
        token = get_github_token()
        auth_url = get_authenticated_git_url(remote_url, token)
        repo = Repo.clone_from(auth_url, abs_path)
        return {
            "status": "success",
            "action": "cloned",
            "current_branch": repo.active_branch.name if not repo.head.is_detached else "DETACHED",
            "commit": repo.head.commit.hexsha
        }
    except GitCommandError as e:
        raise RuntimeError(f"Falha ao clonar repositório: {e.stderr or str(e)}")

def get_git_status(project_path: str) -> dict:
    """Retorna o estado do repositório Git (arquivos modificados, não rastreados, etc.)."""
    try:
        repo = get_repo(project_path)
        
        # Busca a URL remota de origin
        remote_url = ""
        try:
            remote_url = repo.remotes.origin.url
        except Exception:
            pass

        # Verifica se é um repositório vazio (sem commits)
        if len(repo.refs) == 0 or not repo.head.is_valid():
            return {
                "is_git": True,
                "is_empty": True,
                "untracked": repo.untracked_files,
                "modified": [],
                "deleted": [],
                "staged": [],
                "current_branch": "main",  # Git default
                "remote_url": remote_url
            }

        untracked = repo.untracked_files
        modified = [item.a_path for item in repo.index.diff(None) if item.change_type == 'M']
        deleted = [item.a_path for item in repo.index.diff(None) if item.change_type == 'D']
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        conflicted = sorted([item[0] for item in repo.index.unmerged_blobs().items()])
        
        # Busca a branch ativa
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "DETACHED HEAD"
            
        return {
            "is_git": True,
            "is_empty": False,
            "current_branch": branch,
            "untracked": untracked,
            "modified": modified,
            "deleted": deleted,
            "staged": staged,
            "conflicted": conflicted,
            "has_conflicts": bool(conflicted),
            "is_clean": not any([untracked, modified, deleted, staged, conflicted]),
            "remote_url": remote_url
        }
    except ValueError:
        return {
            "is_git": False,
            "is_empty": False,
            "current_branch": None,
            "untracked": [],
            "modified": [],
            "deleted": [],
            "staged": [],
            "is_clean": True,
            "remote_url": ""
        }
    except Exception as e:
        return {
            "is_git": True,
            "error": str(e),
            "untracked": [],
            "modified": [],
            "deleted": [],
            "staged": []
        }

def get_git_graph(project_path: str) -> dict:
    """Retorna a árvore genealógica de commits formatada como um gráfico de texto."""
    try:
        repo = get_repo(project_path)
        # Verifica se o repositório é vazio
        if len(repo.refs) == 0 or not repo.head.is_valid():
            return {
                "is_git": True,
                "is_empty": True,
                "graph": []
            }
            
        # Executa git log --graph
        log_output = repo.git.log(
            "--graph",
            "--abbrev-commit",
            "--decorate",
            "--date=relative",
            '--format=format:%h - %s (%cr) <%an>%d',
            "--all",
            "-n", "100"
        )
        
        lines = log_output.split('\n')
        return {
            "is_git": True,
            "is_empty": False,
            "graph": lines
        }
    except ValueError:
        return {
            "is_git": False,
            "is_empty": False,
            "graph": []
        }
    except Exception as e:
        return {
            "is_git": True,
            "error": str(e),
            "graph": []
        }

def get_commit_context(project_path: str) -> dict:
    """Retorna um resumo das alterações atuais para geração de mensagem de commit."""
    repo = get_repo(project_path)
    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = "DETACHED HEAD"

    staged_files = [item.a_path for item in repo.index.diff("HEAD")]
    modified_files = [item.a_path for item in repo.index.diff(None)]
    untracked_files = repo.untracked_files
    deleted_files = [item.a_path for item in repo.index.diff(None) if item.change_type == 'D']

    name_status = repo.git.diff("--name-status", "HEAD") if repo.head.is_valid() else ""
    diff_stat = repo.git.diff("--stat", "HEAD") if repo.head.is_valid() else ""
    staged_diff = repo.git.diff("--cached", "--", ".") if repo.head.is_valid() else ""
    unstaged_diff = repo.git.diff("--", ".")
    diff_text = "\n".join(part for part in [staged_diff, unstaged_diff] if part).strip()

    # Evita payload enorme para a LLM; nomes de arquivos já carregam boa parte do contexto.
    max_diff_chars = 12000
    if len(diff_text) > max_diff_chars:
        diff_text = diff_text[:max_diff_chars] + "\n\n[diff truncado]"

    return {
        "status": "success",
        "branch": branch,
        "staged": staged_files,
        "modified": modified_files,
        "deleted": deleted_files,
        "untracked": untracked_files,
        "name_status": name_status,
        "diff_stat": diff_stat,
        "diff": diff_text,
        "has_changes": bool(staged_files or modified_files or deleted_files or untracked_files)
    }

def deploy_git(project_path: str, commit_message: str, branch: str = None) -> dict:
    """
    Executa o deploy (Git commit + push):
    1. Executa git add .
    2. Cria um commit com a mensagem especificada
    3. Dá push para a branch ativa (ou especificada) no remote origin.
    """
    repo = get_repo(project_path)
    
    # Se nenhuma branch for especificada, usa a ativa
    if not branch:
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "main"

    try:
        # Atualiza a URL com o token caso necessário
        update_remote_url_with_token(repo)
        
        # 1. Adiciona todas as modificações
        repo.git.add(A=True)
        
        # Verifica se há modificações para commitar
        if not repo.is_dirty(untracked_files=True):
            # Tenta dar push mesmo assim, caso haja commits locais não enviados
            try:
                origin = repo.remote(name="origin")
                push_info = origin.push(refspec=f"{branch}:{branch}")
                return {
                    "status": "success",
                    "action": "push_only",
                    "details": "Nenhuma alteração para commitar. Push executado para commits pendentes.",
                    "push_summary": [str(info.summary) for info in push_info]
                }
            except Exception as pe:
                return {
                    "status": "success",
                    "action": "no_changes_and_push_failed",
                    "details": f"Sem alterações locais. Push também falhou (talvez sem commits locais): {str(pe)}"
                }
        
        # 2. Commit
        commit = repo.index.commit(commit_message)
        
        # 3. Push para origin
        try:
            origin = repo.remote(name="origin")
            push_info = origin.push(refspec=f"{branch}:{branch}")
            push_summary = [str(info.summary) for info in push_info]
        except Exception as pe:
            push_summary = [f"Erro no push: {str(pe)}"]
            
        return {
            "status": "success",
            "action": "commit_and_push",
            "commit_sha": commit.hexsha,
            "branch": branch,
            "push_summary": push_summary
        }
        
    except GitCommandError as e:
        raise RuntimeError(f"Erro no Git: {e.stderr or str(e)}")

def pull_git(project_path: str, branch: str = None) -> dict:
    """Puxa alterações do repositório remoto."""
    repo = get_repo(project_path)
    
    if not branch:
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "main"
            
    try:
        # Atualiza a URL com o token caso necessário
        update_remote_url_with_token(repo)
        
        # Git 2.27+ can refuse pulls on divergent branches unless the strategy is
        # explicit. The GitIDE "Sincronizar" action uses merge semantics.
        output = repo.git.pull("--no-rebase", "origin", branch)
        return {
            "status": "success",
            "action": "pull",
            "details": output.splitlines() or ["Already up to date."]
        }
    except GitCommandError as e:
        raise RuntimeError(f"Falha ao rodar git pull: {e.stderr or str(e)}")

def list_branches(project_path: str, force_fetch: bool = False) -> dict:
    """Retorna uma lista de todas as branches locais e remotas."""
    repo = get_repo(project_path)
    
    # Tenta fazer o fetch para atualizar a lista de branches do servidor remoto apenas se solicitado
    if force_fetch:
        try:
            update_remote_url_with_token(repo)
            if len(repo.remotes) > 0:
                repo.remotes.origin.fetch()
        except Exception:
            pass
        
    try:
        current_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED"
    except (TypeError, AttributeError):
        current_branch = "main"
        
    local_branches = [b.name for b in repo.branches]
    remote_branches = []
    
    try:
        for ref in repo.references:
            if ref.name.startswith("origin/") and not ref.name.endswith("HEAD"):
                remote_branches.append(ref.name[len("origin/"):])
    except Exception:
        pass
        
    all_branches = list(dict.fromkeys(local_branches + remote_branches))
    
    return {
        "status": "success",
        "current_branch": current_branch,
        "local": local_branches,
        "remote": list(dict.fromkeys(remote_branches)),
        "all": all_branches
    }


def create_branch(project_path: str, branch_name: str) -> dict:
    """Cria uma nova branch e faz o checkout dela."""
    repo = get_repo(project_path)
    
    try:
        if branch_name in [b.name for b in repo.branches]:
            repo.git.checkout(branch_name)
            action = "checkout_existing"
        else:
            repo.git.checkout("-b", branch_name)
            action = "created_and_checked_out"
            
        return {
            "status": "success",
            "action": action,
            "current_branch": branch_name
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao criar/alternar branch: {str(e)}")

def merge_branch(project_path: str, branch_name: str) -> dict:
    """Mescla a branch especificada na branch atual."""
    repo = get_repo(project_path)
    try:
        current_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED"
        
        # Executa o merge
        stdout = repo.git.merge(branch_name)
        
        return {
            "status": "success",
            "current_branch": current_branch,
            "merged_branch": branch_name,
            "detail": stdout
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao mesclar branch '{branch_name}': {str(e)}")

def get_active_branch(project_path: str) -> str:
    """Retorna o nome da branch ativa."""
    repo = get_repo(project_path)
    if repo.head.is_detached:
        return "DETACHED"
    return repo.active_branch.name

def get_remote_url(project_path: str) -> str:
    """Retorna a URL remota origin do repositório, se existir."""
    repo = get_repo(project_path)
    try:
        return repo.remotes.origin.url
    except Exception:
        return ""

def push_git(project_path: str, branch: str = None) -> dict:
    """Dá push para o repositório remoto."""
    repo = get_repo(project_path)
    if not branch:
        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = "main"
            
    try:
        update_remote_url_with_token(repo)
        origin = repo.remote(name="origin")
        push_info = origin.push(refspec=f"{branch}:{branch}")
        return {
            "status": "success",
            "action": "pushed",
            "details": f"Push executado com sucesso na branch {branch}.",
            "push_summary": [str(info.summary) for info in push_info]
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao dar push: {str(e)}")

def abort_merge(project_path: str) -> dict:
    """Aborta uma mesclagem em andamento (git merge --abort)."""
    repo = get_repo(project_path)
    try:
        repo.git.merge(abort=True)
        return {
            "status": "success",
            "action": "merge_aborted",
            "details": "Mesclagem abortada com sucesso."
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao abortar mesclagem: {str(e)}")

def _safe_project_path(project_path: str, filepath: str) -> str:
    if os.path.isabs(filepath) or ".." in filepath.replace("\\", "/").split("/"):
        raise ValueError("Caminho de arquivo inválido.")
    root = os.path.abspath(project_path)
    full_path = os.path.abspath(os.path.join(root, filepath))
    if not full_path.startswith(root):
        raise ValueError("Caminho de arquivo fora do projeto.")
    return full_path

def parse_conflict_blocks(content: str) -> list:
    lines = content.splitlines(keepends=True)
    blocks = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<< "):
            start = i
            ours_label = lines[i].strip().replace("<<<<<<<", "").strip() or "ours"
            i += 1
            ours_start = i
            while i < len(lines) and not lines[i].startswith("======="):
                i += 1
            if i >= len(lines):
                break
            separator = i
            i += 1
            theirs_start = i
            while i < len(lines) and not lines[i].startswith(">>>>>>> "):
                i += 1
            if i >= len(lines):
                break
            end = i
            theirs_label = lines[i].strip().replace(">>>>>>>", "").strip() or "theirs"
            blocks.append({
                "index": len(blocks),
                "start_line": start + 1,
                "end_line": end + 1,
                "ours_label": ours_label,
                "theirs_label": theirs_label,
                "ours": "".join(lines[ours_start:separator]),
                "theirs": "".join(lines[theirs_start:end]),
                "raw": "".join(lines[start:end + 1])
            })
        i += 1
    return blocks

def list_conflicts(project_path: str) -> dict:
    repo = get_repo(project_path)
    files = sorted([item[0] for item in repo.index.unmerged_blobs().items()])
    result = []
    for filepath in files:
        full_path = _safe_project_path(project_path, filepath)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(full_path, "r", encoding="latin-1") as f:
                content = f.read()
        blocks = parse_conflict_blocks(content)
        result.append({
            "filepath": filepath,
            "blocks_count": len(blocks),
            "blocks": blocks
        })
    return {"status": "success", "files": result}

def get_conflict_file(project_path: str, filepath: str) -> dict:
    full_path = _safe_project_path(project_path, filepath)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(full_path, "r", encoding="latin-1") as f:
            content = f.read()
    return {
        "status": "success",
        "filepath": filepath,
        "content": content,
        "blocks": parse_conflict_blocks(content)
    }

def resolve_conflict_file(project_path: str, filepath: str, resolutions: list, stage_file: bool = True) -> dict:
    repo = get_repo(project_path)
    full_path = _safe_project_path(project_path, filepath)
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = parse_conflict_blocks(content)
    resolution_map = {item["index"]: item for item in resolutions}
    for block in reversed(blocks):
        if block["index"] not in resolution_map:
            continue
        resolution = resolution_map[block["index"]]
        mode = resolution.get("resolution")
        if mode == "ours":
            replacement = block["ours"]
        elif mode == "theirs":
            replacement = block["theirs"]
        elif mode == "manual":
            replacement = resolution.get("content") or ""
        else:
            raise ValueError(f"Resolução inválida para bloco {block['index']}: {mode}")
        content = content.replace(block["raw"], replacement, 1)

    remaining = parse_conflict_blocks(content)
    with open(full_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)

    if stage_file and not remaining:
        repo.git.add(filepath)

    return {
        "status": "success",
        "filepath": filepath,
        "remaining_blocks": len(remaining),
        "staged": stage_file and not remaining
    }

def set_remote_token(project_path: str, token: str) -> dict:
    """Configura o Personal Access Token (PAT) na URL de origin do Git."""
    repo = get_repo(project_path)
    try:
        origin = repo.remote(name="origin")
        url = origin.url
        if not url:
            raise ValueError("O repositório não possui um controle remoto 'origin' configurado.")
            
        # Reconstrói a URL injetando o token
        auth_url = get_authenticated_git_url(url, token)
        origin.set_url(auth_url)
        return {
            "status": "success",
            "new_url": auth_url.split("@")[-1] if "@" in auth_url else auth_url,
            "details": "Token configurado com sucesso no controle remoto origin."
        }
    except Exception as e:
        raise RuntimeError(f"Erro ao configurar token: {str(e)}")


