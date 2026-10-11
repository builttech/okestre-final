"""Small Windows tray UI. Folder sharing and write permission are explicit."""
import asyncio
import queue
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog

import pystray
from PIL import Image, ImageDraw

from .client import Agent


def run(config):
    window = tk.Tk()
    window.title("Okestre Local")
    window.geometry("780x500")
    window.minsize(620, 420)
    messages = queue.Queue()
    agent = Agent(config, lambda text: messages.put(("status", text)))
    worker = threading.Thread(target=lambda: asyncio.run(agent.run()), daemon=True)
    worker.start()
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Okestre Local", font=("Segoe UI", 18, "bold")).pack(anchor="w")
    status = tk.StringVar(value="Iniciando…")
    ttk.Label(frame, textvariable=status).pack(anchor="w", pady=(3, 14))
    ttk.Label(frame, text="Os arquivos ficam neste computador. O conteúdo solicitado passa pela VM até o GPT.", wraplength=710).pack(anchor="w")
    table = ttk.Treeview(frame, columns=("name", "path", "permission"), show="headings", height=9)
    for column, title, width in (("name", "Projeto", 160), ("path", "Pasta local", 380), ("permission", "Permissão", 120)):
        table.heading(column, text=title)
        table.column(column, width=width)
    table.pack(fill="both", expand=True, pady=14)
    controls = ttk.Frame(frame)
    controls.pack(fill="x")
    def refresh():
        table.delete(*table.get_children())
        for identifier, root in config.load().get("roots", {}).items():
            table.insert("", "end", iid=identifier, values=(root["name"], root["path"], "Leitura e edição" if root.get("writable") else "Somente leitura"))
    def guarded(function):
        def action():
            try:
                function()
                refresh()
            except Exception as exc:
                messagebox.showerror("Okestre Local", str(exc) if isinstance(exc, ValueError) else "Não foi possível concluir a operação.", parent=window)
        return action
    def pair():
        server = simpledialog.askstring("Parear computador", "Endereço HTTPS da VM:", initialvalue=config.load().get("server", ""), parent=window)
        if not server:
            return
        code = simpledialog.askstring("Parear computador", "Código gerado no painel /local-devices da VM:", show="*", parent=window)
        if not code:
            return
        if config.load().get("token") and not messagebox.askyesno("Substituir conexão", "Será necessário cadastrar as pastas novamente. Continuar?", parent=window):
            return
        status.set("Pareando…")
        def perform():
            try:
                config.pair(server, code)
                messages.put(("paired", "Pareado. Adicione as pastas e vincule-as no painel da VM."))
            except Exception:
                messages.put(("error", "Pareamento recusado. Confira o endereço e gere um novo código."))
        threading.Thread(target=perform, daemon=True).start()
    def add():
        path = filedialog.askdirectory(parent=window, title="Escolha a pasta do projeto")
        if not path:
            return
        name = simpledialog.askstring("Projeto", "Nome do projeto:", initialvalue=Path(path).name, parent=window)
        if name:
            writable = messagebox.askyesno("Permissão", "Permitir que o GPT edite arquivos desta pasta?\nEscolha Não para somente leitura.", parent=window)
            config.add_root(path, name, writable)
    def remove():
        selected = table.selection()
        if selected and messagebox.askyesno("Parar compartilhamento", "Remover esta pasta do acesso do GPT? Os arquivos serão preservados.", parent=window):
            data = config.load()
            data["roots"].pop(selected[0], None)
            config.save(data)
    def toggle():
        data = config.load()
        data["paused"] = not data.get("paused", False)
        config.save(data)
        status.set("Pausando…" if data["paused"] else "Reconectando…")
    def panel():
        server = config.load().get("server")
        if server:
            webbrowser.open(server + "/local-devices")
    for label, callback in (("Parear", pair), ("Adicionar pasta", add), ("Remover acesso", remove), ("Pausar / retomar", toggle), ("Painel da VM", panel)):
        ttk.Button(controls, text=label, command=guarded(callback)).pack(side="left", padx=(0, 6))
    ttk.Label(frame, text="Fechar a janela mantém o agente na bandeja. Use Sair no ícone para encerrar.", wraplength=710).pack(anchor="w", pady=(12, 0))
    image = Image.new("RGB", (64, 64), "#17202b")
    ImageDraw.Draw(image).ellipse((13, 13, 51, 51), outline="#74d3b0", width=7)
    def show(*_):
        messages.put(("show", ""))
    def stop(*_):
        messages.put(("stop", ""))
    icon = pystray.Icon("okestre-local", image, "Okestre Local", pystray.Menu(
        pystray.MenuItem("Abrir", show, default=True), pystray.MenuItem("Sair", stop)))
    tray = threading.Thread(target=icon.run, daemon=True)
    tray.start()
    def poll():
        while not messages.empty():
            kind, text = messages.get_nowait()
            if kind == "stop":
                agent.stopping.set()
                icon.stop()
                status.set("Encerrando operações em andamento…")
                def finish():
                    if worker.is_alive():
                        window.after(100, finish)
                    else:
                        window.destroy()
                finish()
                return
            if kind == "show":
                window.deiconify()
                window.lift()
            elif kind == "error":
                messagebox.showerror("Okestre Local", text, parent=window)
            else:
                status.set(text)
                if kind == "paired":
                    refresh()
        window.after(250, poll)
    window.protocol("WM_DELETE_WINDOW", window.withdraw)
    refresh()
    poll()
    window.mainloop()
