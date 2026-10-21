"""Run the existing Okestre application on an authenticated loopback listener."""
import json
import os
import secrets
import socket
import threading
import time
from pathlib import Path

import uvicorn
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool
from okestre_local.config import Config
from okestre_local.terminal import Terminal


class Runtime:
    def __init__(self, home, agent_home=None):
        self.home=Path(home).resolve()
        self.home.mkdir(parents=True,exist_ok=True)
        self.sock=socket.socket()
        self.sock.bind(('127.0.0.1',0))
        self.port=self.sock.getsockname()[1]
        self.origin=f'http://127.0.0.1:{self.port}'
        self.secret=secrets.token_urlsafe(32)
        self.launched=False
        self.terminal=Terminal()
        self.lock=threading.RLock()
        os.environ['GITIDE_DATA_DIR']=str(self.home/'server')
        os.environ['GITIDE_PUBLIC_URL']=self.origin
        # Import only after the isolated data directory has been configured.
        from gitide_server import main as existing
        self.existing=existing
        self.app=existing.app
        from .api import DesktopAPI
        self.native=DesktopAPI(self.home,agent_home)
        self._import_projects()
        from .qa_bridge import QABridge
        self.qa_bridge=QABridge(self)
        root=Path(__file__).resolve().parent
        self.assets=json.loads((root/'ui'/'asset-map.json').read_text(encoding='utf-8'))

        @self.app.middleware('http')
        async def desktop(request, call_next):
            host=request.headers.get('host','')
            if host!=f'127.0.0.1:{self.port}':
                return JSONResponse({'detail':'desktop_origin_denied'},403)
            if request.url.path.startswith('/desktop/qa/'):
                return await self.qa_bridge.handle(request,call_next)
            if request.headers.get('origin',self.origin)!=self.origin:
                return JSONResponse({'detail':'desktop_origin_denied'},403)
            path=request.url.path
            if path=='/desktop-launch/'+self.secret and request.method=='GET' and not self.launched:
                self.launched=True
                with existing.SessionLocal() as db:
                    user=db.query(existing.User).filter_by(role='root',is_active=True).first()
                    cookie=existing.sign_session(user.id)
                response=RedirectResponse('/',303)
                response.set_cookie('gitide_session',cookie,httponly=True,samesite='strict')
                return response
            if not existing.get_current_user_from_request(request):
                return await call_next(request)
            if path in ('/','/design-canvas') and request.method=='GET':
                name='index.html' if path=='/' else 'konva-designer.html'
                html=(Path(existing.STATIC_DIR)/name).read_text(encoding='utf-8')
                for url,local in self.assets.items(): html=html.replace(url,local)
                html=html.replace('</body>',f'<script>window.OKESTRE_DESKTOP_KEY={json.dumps(self.secret)};</script><script src="/desktop/assets/full.js"></script></body>')
                return HTMLResponse(html,headers={'Cache-Control':'no-store'})
            if path=='/local-devices':
                html=(root/'ui'/'connection.html').read_text(encoding='utf-8').replace('__DESKTOP_KEY__',self.secret)
                return HTMLResponse(html,headers={'Cache-Control':'no-store'})
            if path=='/desktop/action' and request.method=='POST':
                if request.headers.get('x-desktop-key')!=self.secret:
                    return JSONResponse({'detail':'desktop_key_required'},403)
                body=await request.body()
                if len(body)>10000:return JSONResponse({'detail':'request_too_large'},413)
                try:
                    data=json.loads(body)
                    name=data['action']
                    if name=='qa_pair':return JSONResponse(self.qa_bridge.issue())
                    if name=='qa_revoke':return JSONResponse(self.qa_bridge.revoke())
                    if name in ('state','connection','choose_agent','open_agent','open_vm'):
                        return JSONResponse(await run_in_threadpool(getattr(self.native,name)))
                    if name in ('execute','poll','stop'):
                        return JSONResponse({'ok':True,'data':await run_in_threadpool(self._terminal,data)})
                    raise ValueError('unsupported_action')
                except Exception as exc:
                    return JSONResponse({'ok':False,'error':str(exc)},400)
            return await call_next(request)
        from fastapi.staticfiles import StaticFiles
        self.app.mount('/desktop/assets',StaticFiles(directory=root/'ui'),name='desktop-assets')
        self.server=uvicorn.Server(uvicorn.Config(self.app,host='127.0.0.1',port=self.port,log_config=None,access_log=False,ws_max_size=8388608))
        self.thread=threading.Thread(target=lambda:self.server.run(sockets=[self.sock]),daemon=True)

    def _import_projects(self):
        # Reuse known folders, not the relay's device-only records.
        existing=self.existing
        with existing.SessionLocal() as db:
            for item in self.native._projects():
                if not Path(item['path']).is_dir():continue
                if db.query(existing.Project).filter(existing.Project._path==item['path']).first():continue
                name=item['name'];index=2
                while db.query(existing.Project).filter_by(name=name).first():
                    name=f"{item['name']} ({index})";index+=1
                db.add(existing.Project(name=name,path=item['path'],storage_kind='server'))
            db.commit()

    def _terminal(self,data):
        with self.lock:
            with self.existing.SessionLocal() as db:
                project=db.get(self.existing.Project,int(data['project_id']))
                if project is None or project.storage_kind=='device':raise ValueError('invalid_project')
                root=str(project.id)
                if data['action']=='stop':return self.terminal.stop(root,int(data['command_id']))
                command=data.get('command','')
                if not isinstance(command,str) or len(command)>8000:raise ValueError('invalid_command')
                return self.terminal.execute(root,project.path,command,data.get('command_id'))

    def start(self):
        self.thread.start()
        for _ in range(200):
            if self.server.started:return self.origin+'/desktop-launch/'+self.secret
            if not self.thread.is_alive():break
            time.sleep(.05)
        raise RuntimeError('O servidor local não iniciou. Consulte startup-error.txt.')

    def close(self):
        with self.lock:self.terminal.close()
        self.native._close()
        self.server.should_exit=True
        self.thread.join(5)
        self.sock.close()
