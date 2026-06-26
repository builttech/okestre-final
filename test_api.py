import os
import shutil
import unittest
import tempfile
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gitide_server.database import Base, Project, ActivityLog, FileSnapshot
import gitide_server.vcs as vcs

class TestGitIDEVCS(unittest.TestCase):
    def setUp(self):
        # 1. Cria diretório temporário para simular a pasta do projeto do usuário
        self.test_dir = tempfile.mkdtemp()
        
        # 2. Cria banco de dados SQLite em memória para teste
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        # 3. Registra o projeto no banco de dados de teste
        self.project = Project(
            name="Projeto de Teste",
            path=self.test_dir,
            git_remote=None
        )
        self.db.add(self.project)
        self.db.commit()
        self.db.refresh(self.project)

    def tearDown(self):
        # Limpa o banco de dados e apaga a pasta temporária
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        shutil.rmtree(self.test_dir)

    def test_safe_path(self):
        # Teste de caminho válido
        path = vcs.get_safe_path(self.project.path, "src/main.py")
        self.assertTrue(path.endswith(os.path.join("src", "main.py")))
        
        # Teste de directory traversal (deve falhar)
        with self.assertRaises(ValueError):
            vcs.get_safe_path(self.project.path, "../fora_do_workspace.txt")
            
        with self.assertRaises(ValueError):
            vcs.get_safe_path(self.project.path, "/etc/passwd")

    def test_file_write_and_snapshot(self):
        filename = "code.py"
        content1 = "print('Hello World')"
        
        # 1. Escreve o arquivo pela primeira vez
        res = vcs.write_project_file(self.db, self.project, filename, content1)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["action"], "created")
        self.assertIsNotNone(res.get("snapshot_id"))
        
        # Verifica no disco
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, filename)))
        
        # Verifica se o snapshot foi criado no DB
        snapshots = self.db.query(FileSnapshot).filter(FileSnapshot.project_id == self.project.id).all()
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].filepath, filename)
        self.assertEqual(snapshots[0].content, content1)

        # 2. Escreve o mesmo conteúdo (não deve gerar novo snapshot)
        res_no_change = vcs.write_project_file(self.db, self.project, filename, content1)
        self.assertEqual(res_no_change["action"], "no_change")
        
        snapshots = self.db.query(FileSnapshot).filter(FileSnapshot.project_id == self.project.id).all()
        self.assertEqual(len(snapshots), 1)

        # 3. Altera o conteúdo (deve gerar novo snapshot)
        content2 = "print('Hello World 2')"
        res_update = vcs.write_project_file(self.db, self.project, filename, content2)
        self.assertEqual(res_update["action"], "updated")
        
        snapshots = self.db.query(FileSnapshot).filter(FileSnapshot.project_id == self.project.id).order_by(FileSnapshot.id.asc()).all()
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(snapshots[1].content, content2)

    def test_file_read(self):
        filename = "config.json"
        content = '{"port": 8080}'
        
        # Escreve o arquivo
        vcs.write_project_file(self.db, self.project, filename, content)
        
        # Lê o arquivo
        read_content = vcs.read_project_file(self.project.path, filename)
        self.assertEqual(read_content, content)
        
        # Lê arquivo inexistente (deve lançar erro)
        with self.assertRaises(FileNotFoundError):
            vcs.read_project_file(self.project.path, "inexistente.txt")

    def test_file_delete_and_snapshot(self):
        filename = "temp.txt"
        content = "remover"
        
        # Escreve
        vcs.write_project_file(self.db, self.project, filename, content)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, filename)))
        
        # Deleta
        res = vcs.delete_project_file(self.db, self.project, filename)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["action"], "deleted")
        
        # Verifica se saiu do disco
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, filename)))
        
        # Verifica se o snapshot do arquivo deletado foi mantido no DB
        last_snap = self.db.query(FileSnapshot).filter(
            FileSnapshot.project_id == self.project.id,
            FileSnapshot.filepath == filename
        ).order_by(FileSnapshot.id.desc()).first()
        
        self.assertIsNotNone(last_snap)
        self.assertEqual(last_snap.content, content)

    def test_rollback(self):
        filename = "main.py"
        vcs.write_project_file(self.db, self.project, filename, "versao 1")  # Snapshot 1
        
        # Salva ID do primeiro snapshot
        first_snap = self.db.query(FileSnapshot).filter(
            FileSnapshot.project_id == self.project.id,
            FileSnapshot.filepath == filename
        ).first()
        first_snap_id = first_snap.id
        
        # Sobrescreve com versão 2
        vcs.write_project_file(self.db, self.project, filename, "versao 2")  # Snapshot 2
        
        # Verifica que o disco está na versão 2
        self.assertEqual(vcs.read_project_file(self.project.path, filename), "versao 2")
        
        # Executa rollback para versão 1
        res = vcs.rollback_project_file(self.db, self.project, first_snap_id)
        self.assertEqual(res["status"], "success")
        
        # Verifica se o arquivo voltou para o conteúdo do primeiro snapshot
        self.assertEqual(vcs.read_project_file(self.project.path, filename), "versao 1")

    def test_list_files(self):
        # Escreve alguns arquivos normais
        vcs.write_project_file(self.db, self.project, "index.html", "html")
        vcs.write_project_file(self.db, self.project, "src/app.py", "app")
        
        # Escreve arquivos em pastas ignoradas
        vcs.write_project_file(self.db, self.project, "node_modules/express/index.js", "npm")
        vcs.write_project_file(self.db, self.project, ".git/config", "git config")
        vcs.write_project_file(self.db, self.project, "src/__pycache__/app.pyc", "pyc cache")
        
        files = vcs.list_project_files(self.project.path)
        file_paths = [f["path"] for f in files]
        
        # Deve listar os arquivos do workspace principal
        self.assertIn("index.html", file_paths)
        self.assertIn("src/app.py", file_paths)
        
        # NÃO deve listar arquivos em pastas ignoradas ou com extensões de cache
        self.assertNotIn("node_modules/express/index.js", file_paths)
        self.assertNotIn(".git/config", file_paths)
        self.assertNotIn("src/__pycache__/app.pyc", file_paths)

    def test_gitideignore(self):
        # 1. Cria o arquivo .gitideignore com padrões
        ignore_content = "\n".join([
            "*.env",
            "secrets/",
            "config/local.json"
        ])
        with open(os.path.join(self.test_dir, ".gitideignore"), 'w', encoding='utf-8') as f:
            f.write(ignore_content)
            
        # 2. Testa load_gitideignore
        patterns = vcs.load_gitideignore(self.project.path)
        self.assertIn("*.env", patterns)
        self.assertIn("secrets/", patterns)
        self.assertIn("config/local.json", patterns)
        
        # 3. Testa is_ignored
        self.assertTrue(vcs.is_ignored(self.project.path, ".gitideignore"))
        self.assertTrue(vcs.is_ignored(self.project.path, ".env"))
        self.assertTrue(vcs.is_ignored(self.project.path, "src/.env"))
        self.assertTrue(vcs.is_ignored(self.project.path, "secrets/pass.txt"))
        self.assertTrue(vcs.is_ignored(self.project.path, "config/local.json"))
        self.assertFalse(vcs.is_ignored(self.project.path, "src/main.py"))
        
        # 4. Testa list_project_files (arquivos ignorados não devem aparecer)
        os.makedirs(os.path.join(self.test_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "secrets"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "config"), exist_ok=True)
        
        with open(os.path.join(self.test_dir, "src/main.py"), "w") as f: f.write("print(1)")
        with open(os.path.join(self.test_dir, "src/.env"), "w") as f: f.write("KEY=123")
        with open(os.path.join(self.test_dir, "secrets/pass.txt"), "w") as f: f.write("123456")
        with open(os.path.join(self.test_dir, "config/local.json"), "w") as f: f.write("{}")
        
        files = vcs.list_project_files(self.project.path)
        paths = [f["path"] for f in files]
        self.assertIn("src/main.py", paths)
        self.assertNotIn("src/.env", paths)
        self.assertNotIn("secrets/pass.txt", paths)
        self.assertNotIn("config/local.json", paths)
        self.assertNotIn(".gitideignore", paths)
        
        # 5. Testa bloqueios em read/write/delete/patch/rollback
        with self.assertRaises(ValueError):
            vcs.write_project_file(self.db, self.project, "src/.env", "novo_conteudo")
            
        with self.assertRaises(ValueError):
            vcs.read_project_file(self.project.path, "src/.env")
            
        with self.assertRaises(ValueError):
            vcs.delete_project_file(self.db, self.project, "src/.env")
            
        with self.assertRaises(ValueError):
            vcs.patch_project_file(self.db, self.project, "src/.env", "old", "new")
            
        with self.assertRaises(ValueError):
            vcs.read_project_file(self.project.path, ".gitideignore")


class TestGitIDEAPI(unittest.TestCase):
    def setUp(self):
        # 1. Cria diretório temporário para simular a pasta do projeto do usuário
        self.test_dir = tempfile.mkdtemp()
        
        # 2. Cria banco de dados SQLite temporário em arquivo para teste
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        
        # 3. Registra o projeto no banco de dados de teste
        from gitide_server.database import PendingCommand
        self.project = Project(
            id=1,
            name="Projeto de Teste API",
            path=self.test_dir,
            git_remote=None
        )
        self.db.add(self.project)
        self.db.commit()
        
        # Override get_db dependecy
        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()
        
        # Override get_api_key dependency to bypass authentication in tests
        def override_get_api_key():
            return "test_api_key"
            
        from gitide_server.main import app, get_api_key, get_db
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_api_key] = override_get_api_key
        
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def tearDown(self):
        from gitide_server.main import app
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except Exception:
            pass
        shutil.rmtree(self.test_dir)

    def test_execute_command_from_dashboard(self):
        payload = {"command": "echo hello"}
        headers = {"X-GitIDE-Source": "dashboard"}
        
        response = self.client.post("/api/projects/1/execute", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
    def test_execute_command_external_requires_approval(self):
        from gitide_server.database import PendingCommand
        payload = {"command": "echo forbidden"}
        
        response = self.client.post("/api/projects/1/execute", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "pending_approval")
        self.assertIn("command_id", data)
        command_id = data["command_id"]
        
        # Verifica se o comando foi salvo como pendente no DB
        pending = self.db.query(PendingCommand).filter(PendingCommand.id == command_id).first()
        self.assertIsNotNone(pending)
        self.assertEqual(pending.command, "echo forbidden")
        self.assertEqual(pending.status, "pending")
        
        # Tenta listar os comandos pendentes via API do Dashboard
        response_list = self.client.get("/api/projects/1/execute/pending")
        self.assertEqual(response_list.status_code, 200)
        cmds = response_list.json()
        self.assertTrue(any(c["id"] == command_id for c in cmds))
        
        # Aprova o comando via API do Dashboard
        response_approve = self.client.post(f"/api/projects/1/execute/pending/{command_id}/approve")
        self.assertEqual(response_approve.status_code, 200)
        self.assertEqual(response_approve.json()["status"], "success")
        
        # Verifica no DB que o status mudou para approved
        self.db.refresh(pending)
        self.assertEqual(pending.status, "approved")
        
        # Repete a chamada externa da IA (agora deve executar)
        response_retry = self.client.post("/api/projects/1/execute", json=payload)
        self.assertEqual(response_retry.status_code, 200)
        data_retry = response_retry.json()
        self.assertEqual(data_retry["status"], "success")
        
        # Verifica no DB que o status mudou para executed
        self.db.refresh(pending)
        self.assertEqual(pending.status, "executed")

if __name__ == "__main__":
    unittest.main()
