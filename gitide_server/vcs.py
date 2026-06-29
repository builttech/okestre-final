import os
import hashlib
import fnmatch
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from gitide_server.database import Project, FileSnapshot, ActivityLog

def get_safe_path(project_path: str, filepath: str) -> str:
    """
    Retorna o caminho completo e seguro para um arquivo dentro do projeto,
    prevenindo ataques de directory traversal (../).
    """
    # Normaliza caminhos
    abs_project_path = os.path.abspath(project_path)
    # Se o filepath for absoluto, tenta torná-lo relativo ao projeto
    if os.path.isabs(filepath):
        # Se for no Windows e começar com a mesma unidade, remove a unidade se necessário
        # Simplificamos combinando e verificando se continua dentro do diretório do projeto
        filepath = os.path.relpath(filepath, abs_project_path)
    
    full_path = os.path.abspath(os.path.join(abs_project_path, filepath))
    
    # Verifica se o caminho final começa com o diretório do projeto
    if not full_path.startswith(abs_project_path):
        raise ValueError(f"Caminho inválido ou fora do workspace do projeto: {filepath}")
        
    return full_path

def load_gitideignore(project_path: str) -> list[str]:
    """Lê os padrões de ignorar definidos no arquivo .gitideignore."""
    ignore_path = os.path.join(project_path, ".gitideignore")
    if not os.path.exists(ignore_path):
        return []
    
    patterns = []
    try:
        with open(ignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Normaliza contra contra-barras do Windows
                    patterns.append(line.replace('\\', '/'))
    except Exception:
        pass
    return patterns

def is_ignored(project_path: str, filepath: str) -> bool:
    """Verifica se um arquivo/caminho relativo corresponde a algum padrão do .gitideignore."""
    patterns = load_gitideignore(project_path)
    # Se não há padrões, bloqueia por padrão apenas o próprio arquivo .gitideignore
    if not patterns:
        return filepath.replace('\\', '/') == ".gitideignore"
        
    # Normaliza o caminho de entrada para ser relativo ao projeto com barras normais
    abs_project_path = os.path.abspath(project_path)
    if os.path.isabs(filepath):
        abs_file_path = os.path.abspath(filepath)
    else:
        abs_file_path = os.path.abspath(os.path.join(abs_project_path, filepath))
        
    rel_path = os.path.relpath(abs_file_path, abs_project_path).replace('\\', '/')
    
    # Bloqueia a leitura do próprio arquivo .gitideignore por segurança
    if rel_path == ".gitideignore":
        return True

    for pattern in patterns:
        # Se for um diretório e terminar com /
        if pattern.endswith('/'):
            if rel_path.startswith(pattern) or rel_path.startswith(pattern[:-1] + '/'):
                return True
        else:
            # Caso contrário, testa fnmatch no caminho completo ou em partes dele
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
            # Caso seja uma pasta sem / no final (ex: 'secrets'), valida se o caminho começa com 'secrets/'
            if rel_path.startswith(pattern + '/'):
                return True
                
    return False

def compute_sha256(content: str) -> str:
    """Calcula a hash SHA256 do conteúdo de um arquivo."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def list_project_files(project_path: str) -> list[dict]:
    """
    Lista recursivamente todos os arquivos de um projeto, 
    ignorando diretórios comuns de build, dependências ou controle de versão.
    """
    abs_project_path = os.path.abspath(project_path)
    if not os.path.exists(abs_project_path):
        raise FileNotFoundError(f"Diretório do projeto não existe: {project_path}")
        
    ignore_dirs = {
        '.git', '.gitide', 'node_modules', '__pycache__', '.venv', 'venv', 
        'env', '.next', 'dist', 'build', '.idea', '.vscode', 'tmp', '.gemini'
    }
    ignore_extensions = {'.pyc', '.pyo', '.pyd', '.db', '.sqlite', '.sqlite3', '.zip', '.tar', '.gz'}
    
    patterns = load_gitideignore(abs_project_path)
    file_list = []
    
    for root, dirs, files in os.walk(abs_project_path):
        # Modifica dirs in-place para que o os.walk não entre em diretórios ignorados
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in ignore_extensions:
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, abs_project_path).replace('\\', '/')
            
            if is_ignored(project_path, rel_path):
                continue
                
            try:
                stat = os.stat(full_path)
                file_list.append({
                     "path": rel_path,
                     "size": stat.st_size,
                     "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception:
                # Ignora arquivos que não podem ser lidos (ex: bloqueados pelo SO)
                continue
                
    return file_list

def read_project_file(project_path: str, filepath: str) -> str:
    """Lê o conteúdo de um arquivo no projeto."""
    if is_ignored(project_path, filepath):
        raise ValueError(f"Acesso ao arquivo bloqueado pelo .gitideignore: {filepath}")
    full_path = get_safe_path(project_path, filepath)
        
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    if os.path.isdir(full_path):
        raise IsADirectoryError(f"O caminho especificado é um diretório: {filepath}")
        
    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_project_file(db: Session, project: Project, filepath: str, content: str, activity_log_id: int = None) -> dict:
    """
    Escreve conteúdo em um arquivo.
    Se o arquivo já existia, salva a nova versão como um FileSnapshot
    no banco de dados antes/depois da escrita para controle de versão.
    """
    if is_ignored(project.path, filepath):
        raise ValueError(f"Acesso ao arquivo bloqueado pelo .gitideignore: {filepath}")
    full_path = get_safe_path(project.path, filepath)
        
    # Cria os diretórios pais se não existirem
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Verifica se o arquivo já existia e qual era seu conteúdo
    existed = os.path.exists(full_path)
    old_content = ""
    if existed:
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                old_content = f.read()
        except Exception:
            pass
            
    # Escreve o novo conteúdo no disco
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    # Calcula hash do novo conteúdo
    new_hash = compute_sha256(content)
    
    # Se o arquivo mudou ou se é um novo arquivo, cria um snapshot da nova versão
    if not existed or compute_sha256(old_content) != new_hash:
        snapshot = FileSnapshot(
            project_id=project.id,
            filepath=filepath.replace('\\', '/'),
            content=content,
            hash=new_hash,
            activity_log_id=activity_log_id,
            timestamp=datetime.utcnow()
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return {"status": "success", "action": "updated" if existed else "created", "snapshot_id": snapshot.id}
        
    return {"status": "success", "action": "no_change"}

def delete_project_file(db: Session, project: Project, filepath: str, activity_log_id: int = None) -> dict:
    """
    Exclui um arquivo ou diretório do projeto. Para arquivos, salva um snapshot
    final do conteúdo para permitir restauração posterior.
    """
    if is_ignored(project.path, filepath):
        raise ValueError(f"Acesso ao arquivo bloqueado pelo .gitideignore: {filepath}")
    full_path = get_safe_path(project.path, filepath)
        
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Arquivo ou pasta não encontrado para exclusão: {filepath}")

    rel_path = filepath.replace('\\', '/').rstrip('/')

    if os.path.isdir(full_path):
        if os.path.abspath(full_path) == os.path.abspath(project.path):
            raise ValueError("Não é permitido excluir a raiz do workspace.")
        shutil.rmtree(full_path)
        db.commit()
        return {"status": "success", "action": "deleted_directory", "filepath": rel_path}
        
    # Salva o snapshot final antes de deletar
    content = ""
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        raise IOError(f"Não foi possível ler o arquivo antes de excluir: {str(e)}")
        
    snapshot = FileSnapshot(
        project_id=project.id,
        filepath=filepath.replace('\\', '/'),
        content=content,
        hash=compute_sha256(content),
        activity_log_id=activity_log_id,
        timestamp=datetime.utcnow()
    )
    db.add(snapshot)
    
    # Remove o arquivo do disco
    os.remove(full_path)
    db.commit()
    
    return {"status": "success", "action": "deleted", "filepath": rel_path, "snapshot_id": snapshot.id}

def rollback_project_file(db: Session, project: Project, snapshot_id: int) -> dict:
    """
    Restaura um arquivo para o estado salvo em um snapshot específico.
    """
    snapshot = db.query(FileSnapshot).filter(
        FileSnapshot.id == snapshot_id,
        FileSnapshot.project_id == project.id
    ).first()
    
    if not snapshot:
        raise ValueError(f"Snapshot ID {snapshot_id} não encontrado para este projeto.")
        
    if is_ignored(project.path, snapshot.filepath):
        raise ValueError(f"Acesso ao arquivo bloqueado pelo .gitideignore: {snapshot.filepath}")
        
    full_path = get_safe_path(project.path, snapshot.filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Escreve o conteúdo do snapshot de volta para o disco
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(snapshot.content)
        
    # Registra o log de rollback
    log = ActivityLog(
        project_id=project.id,
        action_type="ROLLBACK",
        details=f"Restaurado arquivo '{snapshot.filepath}' para a versão do snapshot #{snapshot_id}"
    )
    db.add(log)
    db.commit()
    
    return {
        "status": "success", 
        "filepath": snapshot.filepath, 
        "snapshot_id": snapshot_id,
        "timestamp": snapshot.timestamp.isoformat()
    }

def detect_and_snapshot_workspace_changes(db: Session, project: Project, activity_log_id: int = None) -> list[dict]:
    """
    Rastreia arquivos no workspace e cria snapshots para qualquer arquivo que foi
    criado, modificado ou excluído desde o último snapshot registrado.
    """
    try:
        physical_files = list_project_files(project.path)
    except Exception:
        return []
        
    physical_map = {f["path"]: f for f in physical_files}
    
    # Busca o último snapshot de cada arquivo no banco de dados
    from sqlalchemy import func
    subquery = db.query(
        FileSnapshot.filepath,
        func.max(FileSnapshot.id).label("max_id")
    ).filter(FileSnapshot.project_id == project.id).group_by(FileSnapshot.filepath).subquery()
    
    last_snapshots = db.query(FileSnapshot).join(
        subquery,
        (FileSnapshot.id == subquery.c.max_id)
    ).all()
    
    db_map = {snap.filepath: snap for snap in last_snapshots}
    
    detected_changes = []
    
    # Rastreia criações e modificações
    for rel_path, file_info in physical_map.items():
        full_path = os.path.join(project.path, rel_path)
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                current_content = f.read()
        except Exception:
            continue
            
        current_hash = compute_sha256(current_content)
        last_snap = db_map.get(rel_path)
        
        # Se não há snapshot gravado ou o conteúdo físico difere do último snapshot
        if not last_snap or last_snap.hash != current_hash:
            new_snap = FileSnapshot(
                project_id=project.id,
                filepath=rel_path,
                content=current_content,
                hash=current_hash,
                activity_log_id=activity_log_id,
                timestamp=datetime.utcnow()
            )
            db.add(new_snap)
            detected_changes.append({
                "filepath": rel_path,
                "type": "created" if not last_snap else "modified"
            })
            
    # Rastreia exclusões (arquivos que tinham snapshots ativos com conteúdo, mas sumiram do disco)
    for rel_path, last_snap in db_map.items():
        if rel_path not in physical_map:
            # Só cria o snapshot de exclusão se o último snapshot não era vazio
            if last_snap.content != "":
                empty_hash = compute_sha256("")
                new_snap = FileSnapshot(
                    project_id=project.id,
                    filepath=rel_path,
                    content="",
                    hash=empty_hash,
                    activity_log_id=activity_log_id,
                    timestamp=datetime.utcnow()
                )
                db.add(new_snap)
                detected_changes.append({
                    "filepath": rel_path,
                    "type": "deleted"
                })
                
    if detected_changes:
        db.commit()
        
    return detected_changes

def patch_project_file(db: Session, project: Project, filepath: str, target_content: str, replacement_content: str, allow_multiple: bool = False, activity_log_id: int = None) -> dict:
    """
    Substitui um trecho específico de um arquivo.
    Lança ValueError se as condições de busca/substituição não forem atendidas.
    """
    if is_ignored(project.path, filepath):
        raise ValueError(f"Acesso ao arquivo bloqueado pelo .gitideignore: {filepath}")
        
    content = read_project_file(project.path, filepath)
    occurrences = content.count(target_content)
    
    if occurrences == 0:
        raise ValueError("Texto alvo não encontrado no arquivo.")
        
    if occurrences > 1 and not allow_multiple:
        raise ValueError("O texto alvo foi encontrado múltiplas vezes. Use allow_multiple=True para substituir todas.")
        
    new_content = content.replace(target_content, replacement_content)
    return write_project_file(db, project, filepath, new_content, activity_log_id=activity_log_id)

