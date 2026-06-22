import os
import json
from git import Repo, GitCommandError

CONFIG_PATH = os.path.expanduser("~/.gitide/config.json")

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
        repo = Repo.clone_from(remote_url, abs_path)
        return {
            "status": "success",
            "action": "cloned",
            "current_branch": repo.active_branch.name,
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
            "is_clean": not any([untracked, modified, deleted, staged]),
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
        
        origin = repo.remote(name="origin")
        pull_info = origin.pull(refspec=f"{branch}")
        return {
            "status": "success",
            "action": "pull",
            "details": [str(info) for info in pull_info]
        }
    except GitCommandError as e:
        raise RuntimeError(f"Falha ao rodar git pull: {e.stderr or str(e)}")

def list_branches(project_path: str) -> dict:
    """Retorna uma lista de todas as branches locais e remotas."""
    repo = get_repo(project_path)
    
    # Tenta fazer o fetch para atualizar a lista de branches do servidor remoto
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




