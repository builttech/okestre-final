import argparse
import asyncio
import getpass
import json
import time
import uuid

from .config import Config
from .client import Agent


def main():
    parser = argparse.ArgumentParser(description="Okestre Local")
    parser.add_argument("--home", help="Diretório privado de configuração e histórico")
    commands = parser.add_subparsers(dest="action")
    pair = commands.add_parser("pair")
    pair.add_argument("server")
    add = commands.add_parser("add")
    add.add_argument("path")
    add.add_argument("--name", required=True)
    add.add_argument("--write", action="store_true")
    commands.add_parser("roots")
    commands.add_parser("run")
    commands.add_parser("gui")
    commands.add_parser("history")
    commands.add_parser("self-test")
    restore = commands.add_parser("restore")
    restore.add_argument("snapshot_id")
    restore.add_argument("--expected-sha256", required=True, help="Hash atual obtido ao ler o arquivo")
    args = parser.parse_args()
    config = Config(args.home)
    try:
        if args.action == "pair":
            config.pair(args.server, getpass.getpass("Código do painel da VM: "))
            print("Pareado. Adicione as pastas que deseja compartilhar.")
        elif args.action == "add":
            print("Pasta cadastrada:", config.add_root(args.path, args.name, args.write))
        elif args.action == "roots":
            print(json.dumps(config.load().get("roots", {}), ensure_ascii=False, indent=2))
        elif args.action in ("history", "restore"):
            from .executor import Executor
            with config.single_instance():
                executor = Executor(config.load().get("roots", {}), config.home)
                with executor.database() as db:
                    if args.action == "history":
                        rows = db.execute("SELECT id,root_id,filepath,created FROM snapshots ORDER BY created DESC LIMIT 100").fetchall()
                        print(json.dumps(rows, ensure_ascii=False, indent=2))
                    else:
                        row = db.execute("SELECT root_id,filepath,previous FROM snapshots WHERE id=?", (args.snapshot_id,)).fetchone()
                        if not row or row[2] is None:
                            raise ValueError("Snapshot sem versão anterior. Exclusão não é suportada por este comando.")
                        result = executor.dispatch(dict(type="call", version=1, request_id=uuid.uuid4().hex, root_id=row[0],
                            operation="write_file", arguments={"filepath": row[1], "content": row[2].decode("utf-8"), "expected_sha256": args.expected_sha256},
                            can_write=True))
                        print(json.dumps(result))
        elif args.action == "self-test":
            import tempfile
            import tkinter as tk
            from pathlib import Path
            from .executor import Executor
            with tempfile.TemporaryDirectory() as directory:
                temporary = Config(Path(directory) / "config")
                temporary.save({"roots": {}, "test": "ok"})
                assert temporary.load()["test"] == "ok"
                root = Path(directory) / "project"
                root.mkdir()
                (root / "test.txt").write_text("ok")
                identifier = temporary.add_root(root, "Teste", False)
                executor = Executor(temporary.load()["roots"], temporary.home)
                result = executor.dispatch(dict(type="call", version=1, request_id=uuid.uuid4().hex, root_id=identifier,
                    operation="read_file", arguments={"filepath": "test.txt"}, can_write=False))
                assert result["content"] == "ok"
                window = tk.Tk()
                window.withdraw()
                from .theme import apply_theme
                from tkinter import ttk
                apply_theme(window)
                window.update()
                assert ttk.Style(window).lookup("Treeview", "background") == "#202020"
                window.destroy()
            (config.home / "self-test.json").write_text(json.dumps({"config": "ok", "local_read": "ok", "tk_startup": "ok"}))
        else:
            with config.single_instance():
                if args.action == "run":
                    asyncio.run(Agent(config, print).run())
                else:
                    from .gui import run
                    run(config)
    except KeyboardInterrupt:
        pass
    except Exception:
        if args.action in (None, "gui"):
            from tkinter.messagebox import showerror
            showerror("Okestre Local", "Não foi possível iniciar. Confira se o aplicativo já está aberto e se a configuração pertence a este usuário do Windows.")
        else:
            parser.exit(1, "Falha. Confira os dados, a conexão e se o agente já está aberto.\n")


if __name__ == "__main__":
    main()
