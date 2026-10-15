"""Standalone WebView2 desktop. The relay agent remains a separate application."""
import argparse
import json
import os
import shutil
import threading
from pathlib import Path

from okestre_local.config import Config
from .api import DesktopAPI


def prepare_ui(home):
    base=Path(__file__).resolve().parents[1]
    target=home/'ui'
    target.mkdir(parents=True,exist_ok=True)
    for path in (base/'okestre_desktop'/'ui').iterdir():
        if path.is_file(): shutil.copyfile(path,target/path.name)
    diagram=target/'diagrams'
    diagram.mkdir(exist_ok=True)
    static=base/'gitide_server'/'static'
    for name in ('er-diagram.css','er-diagram.js'):
        shutil.copyfile(static/name,diagram/name)
    html=(static/'er-diagram.html').read_text(encoding='utf-8').replace('/static/','').replace('<a href="/" class="brand">← Okestre</a>','<span class="brand">Okestre Desktop</span>')
    (diagram/'index.html').write_text(html,encoding='utf-8')
    (diagram/'vendor').mkdir(exist_ok=True)
    for name in ('mermaid-11.12.0.min.js','mermaid-LICENSE'):
        shutil.copyfile(static/'vendor'/name,diagram/'vendor'/name)
    return target


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--home')
    parser.add_argument('--agent-home')
    parser.add_argument('--smoke-test',help='Write native renderer diagnostics to a JSON file, then exit.')
    args=parser.parse_args()
    home=Path(args.home) if args.home else Path(os.environ.get('LOCALAPPDATA',Path.home()))/'OkestreDesktop'
    home=home.resolve()
    home.mkdir(parents=True,exist_ok=True)
    import webview
    try:
        with Config(home/'instance').single_instance():
            ui=prepare_ui(home)
            api=DesktopAPI(home,args.agent_home)
            api._diagram_url=str(ui/'diagrams'/'index.html')
            webview.settings['ALLOW_DOWNLOADS']=True
            webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER']=True
            window=webview.create_window('Okestre Desktop',str(ui/'index.html'),js_api=api,width=1400,height=900,min_size=(950,640),hidden=bool(args.smoke_test))
            api._window=window
            window.events.closed += api._close
            def smoke():
                import time
                try:
                    for _ in range(60):
                        value=window.evaluate_js('Boolean(window.desktopReady)')
                        if value: break
                        time.sleep(.25)
                    diagram=webview.create_window('Diagram QA',api._diagram_url,hidden=True)
                    rendered=False
                    for _ in range(60):
                        try:
                            rendered=diagram.evaluate_js('Boolean(document.querySelector("#preview svg"))')
                            if rendered: break
                        except Exception:
                            pass
                        time.sleep(.25)
                    result={'ready':bool(value),'diagram_rendered':bool(rendered),'title':window.evaluate_js('document.title'),'state':api.state()}
                    diagram.destroy()
                    Path(args.smoke_test).write_text(json.dumps(result),encoding='utf-8')
                finally:
                    window.destroy()
            if args.smoke_test:
                window.events.loaded += lambda: threading.Thread(target=smoke,daemon=True).start()
            webview.start(gui='edgechromium',private_mode=False,storage_path=str(home/'webview'))
    except Exception as exc:
        (home/'startup-error.txt').write_text(str(exc),encoding='utf-8')
        if args.smoke_test: raise
        import ctypes
        ctypes.windll.user32.MessageBoxW(0,'Não foi possível abrir o Okestre Desktop. Confira o WebView2 e se o aplicativo já está aberto.\n\n'+str(exc),'Okestre Desktop',16)


if __name__=='__main__':
    main()
