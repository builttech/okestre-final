"""Launch the complete existing Okestre UI and backend in a Windows window."""
import argparse
import json
import os
import threading
import time
from pathlib import Path
from okestre_local.config import Config


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--home')
    parser.add_argument('--agent-home')
    parser.add_argument('--smoke-test')
    args=parser.parse_args()
    home=(Path(args.home) if args.home else Path(os.environ.get('LOCALAPPDATA',Path.home()))/'OkestreDesktop').resolve()
    home.mkdir(parents=True,exist_ok=True)
    runtime=None
    try:
        with Config(home/'instance').single_instance():
            from .runtime import Runtime
            runtime=Runtime(home,args.agent_home)
            url=runtime.start()
            import webview
            webview.settings['ALLOW_DOWNLOADS']=True
            webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER']=True
            webview.settings['DRAG_REGION_SELECTOR']='.topbar, .desktop-drag-region'
            webview.settings['DRAG_REGION_DIRECT_TARGET_ONLY']=True
            from .titlebar import TitlebarTheme, THEME_OBSERVER
            titlebar = TitlebarTheme()
            window=webview.create_window('Okestre Desktop',url,width=1440,height=950,min_size=(1000,700),hidden=bool(args.smoke_test),js_api=titlebar,frameless=True,easy_drag=False)
            titlebar._window = window
            window.events.shown += lambda: titlebar.set_theme('dark')
            window.events.loaded += lambda: window.evaluate_js(THEME_OBSERVER + (Path(__file__).parent/'ui'/'window-chrome.js').read_text(encoding='utf-8'))
            runtime.native._window=window
            started=threading.Event()
            def smoke():
                if started.is_set():return
                started.set()
                try:
                    ready=False
                    for _ in range(100):
                        ready=window.evaluate_js("typeof state!=='undefined' && Boolean(state.apiKey)")
                        if ready:break
                        time.sleep(.2)
                    tabs=window.evaluate_js("Array.from(document.querySelectorAll('.sidebar-nav [data-tab]')).map(e=>e.dataset.tab)")
                    data={'ready':bool(ready),'tabs':tabs,'complete_ui':all(t in tabs for t in ['tab-sdd','tab-discovery','tab-git','tab-documents','tab-ui-canvas','tab-agent','tab-qa'])}
                    Path(args.smoke_test).write_text(json.dumps(data),encoding='utf-8')
                finally:window.destroy()
            if args.smoke_test:
                window.events.loaded += lambda: threading.Thread(target=smoke,daemon=True).start()
            webview.start(gui='edgechromium',private_mode=False,storage_path=str(home/'webview'))
    except Exception as exc:
        import traceback
        (home/'startup-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        if args.smoke_test:raise
        import ctypes
        ctypes.windll.user32.MessageBoxW(0,'Não foi possível abrir o Okestre. Consulte '+str(home/'startup-error.txt')+'\n\n'+str(exc),'Okestre Desktop',16)
    finally:
        if runtime:runtime.close()


if __name__=='__main__':main()
