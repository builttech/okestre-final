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

from .protocol import BridgeError
from .client import Agent
from .theme import apply_theme


def run(config):
    window = tk.Tk()
    window.title("Okestre Local")
    window.geometry("960x580")
    window.minsize(720, 480)
    apply_theme(window)
    messages = queue.Queue()
    agent = Agent(config, lambda text: messages.put(("status", text)))
    worker = threading.Thread(target=lambda: asyncio.run(agent.run()), daemon=True)
    worker.start()
    brand = ttk.Frame(window, padding=(20, 12))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)
    brand.grid(row=0, column=0, sticky="ew")
    ttk.Label(brand, text="Okestre", style="Brand.TLabel").pack(side="left")
    ttk.Label(brand, text="  /  Local", style="Muted.TLabel").pack(side="left")
    status = tk.StringVar(value="Iniciando…")
    status_badge = ttk.Label(brand, textvariable=status, style="Status.TLabel", wraplength=400)
    status_badge.pack(side="right")
    frame = ttk.Frame(window, padding=(20, 8, 20, 18))
    frame.grid(row=1, column=0, sticky="nsew")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(2, weight=1)
    heading = ttk.Frame(frame)
    heading.grid(row=0, column=0, sticky="ew")
    ttk.Label(heading, text="Projetos compartilhados", style="Title.TLabel").pack(side="left")
    header_actions = ttk.Frame(heading)
    header_actions.pack(side="right")
    description = ttk.Label(frame, text="Seus arquivos ficam neste computador. Compartilhe apenas as pastas que o GPT pode acessar.",
                            style="Muted.TLabel", wraplength=860)
    description.grid(row=1, column=0, sticky="w", pady=(10, 20))
    table_frame = ttk.Frame(frame)
    table_frame.grid(row=2, column=0, sticky="nsew")
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)
    table = ttk.Treeview(table_frame, columns=("name", "path", "permission"), show="headings", height=1)
    for column, title, width, minimum in (("name", "Projeto", 180, 120), ("path", "Pasta local", 450, 220), ("permission", "Permissão", 170, 140)):
        table.heading(column, text=title, anchor="w")
        table.column(column, width=width, minwidth=minimum, anchor="w", stretch=column == "path")
    table.grid(row=0, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
    horizontal.grid(row=1, column=0, sticky="ew")
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    footer = ttk.Frame(frame)
    footer.grid(row=3, column=0, sticky="ew", pady=(14, 0))
    count = tk.StringVar()
    ttk.Label(footer, textvariable=count, style="Muted.TLabel").pack(side="left")
    controls = ttk.Frame(footer)
    controls.pack(side="right")
    def refresh():
        table.delete(*table.get_children())
        roots = config.load().get("roots", {})
        count.set(str(len(roots)) + " pasta(s) compartilhada(s)")
        for identifier, root in roots.items():
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
        server = simpledialog.askstring("Parear computador", "Endereço HTTPS do Connect (sem /connect-device):", initialvalue=config.load().get("server", ""), parent=window)
        if not server:
            return
        code = simpledialog.askstring("Parear computador", "Código gerado no painel /connect-device:", show="*", parent=window)
        if not code:
            return
        if config.load().get("token") and not messagebox.askyesno("Substituir conexão", "Será necessário cadastrar as pastas novamente. Continuar?", parent=window):
            return
        status.set("Pareando…")
        def perform():
            try:
                config.pair(server, code)
                messages.put(("paired", "Pareado. Adicione as pastas e vincule-as no painel do Connect."))
            except Exception as exc:
                message = str(exc) if isinstance(exc, BridgeError) else "Não foi possível concluir o pareamento. A conexão anterior foi preservada."
                messages.put(("error", message))
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
            webbrowser.open(server + "/connect-device")
    ttk.Button(header_actions, text="Parear", command=guarded(pair)).pack(side="left", padx=(0, 8))
    ttk.Button(header_actions, text="Abrir Connect", command=guarded(panel)).pack(side="left")
    for label, callback, button_style in (("Adicionar pasta", add, "Primary.TButton"), ("Remover acesso", remove, "TButton"), ("Pausar / retomar", toggle, "TButton")):
        ttk.Button(controls, text=label, style=button_style, command=guarded(callback)).pack(side="left", padx=(8, 0))
    hint = ttk.Label(frame, text="Fechar a janela mantém o agente na bandeja. Para encerrar, use Sair no ícone.",
                    style="Muted.TLabel", wraplength=860)
    hint.grid(row=4, column=0, sticky="w", pady=(18, 0))
    def resized(event):
        if event.widget is window:
            description.configure(wraplength=max(300, event.width - 48))
            hint.configure(wraplength=max(300, event.width - 48))
    window.bind("<Configure>", resized, add=True)
    status.trace_add("write", lambda *_: status_badge.configure(
        style="Connected.Status.TLabel" if status.get() == "Conectado" else "Status.TLabel"))
    image = Image.new("RGB", (64, 64), "#202020")
    ImageDraw.Draw(image).ellipse((13, 13, 51, 51), outline="#ececec", width=7)
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
                status.set("Pareamento ou operação não concluída.")
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
