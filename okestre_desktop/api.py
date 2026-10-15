"""Native desktop API. No HTTP command endpoint and no agent configuration writes."""
import hashlib
import json
import os
import subprocess
import threading
import uuid
import webbrowser
from functools import wraps
from pathlib import Path

import requests
from okestre_local.config import Config, server_url
from okestre_local.executor import Executor, sha
from okestre_local.paths import SafeRoot
from okestre_local.protocol import BridgeError


def result(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        try:
            with self._lock:
                return {'ok': True, 'data': method(self, *args, **kwargs)}
        except Exception as exc:
            return {'ok': False, 'error': str(exc) or type(exc).__name__}
    return call


class DesktopAPI:
    def __init__(self, home, agent_home=None):
        self._home = Path(home)
        self._home.mkdir(parents=True, exist_ok=True)
        self._file = self._home / 'workspace.json'
        self._agent = Config(agent_home)
        self._lock = threading.RLock()
        self._settings = json.loads(self._file.read_text(encoding='utf-8')) if self._file.exists() else {'projects': [], 'agent_exe': ''}
        self._executor = Executor({}, self._home / 'history')
        self._window = None
        self._diagram_url = None
        self._jobs = {}

    def _save(self):
        temp = self._file.with_suffix('.tmp')
        temp.write_text(json.dumps(self._settings, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, self._file)

    def _projects(self):
        items = [dict(p, shared=False) for p in self._settings['projects']]
        settings = self._agent.load()
        for root in settings.get('roots', {}).values():
            path = os.path.abspath(root['path'])
            existing = next((p for p in items if os.path.normcase(p['path']) == os.path.normcase(path)), None)
            if existing:
                existing['shared'] = True
            else:
                items.append({'id': hashlib.sha256(os.path.normcase(path).encode()).hexdigest()[:32],
                              'name': root['name'], 'path': path, 'shared': True})
        return items

    def _project(self, identifier):
        project = next((p for p in self._projects() if p['id'] == identifier), None)
        if project is None or not Path(project['path']).is_dir():
            raise ValueError('Projeto indisponível. Confira se a pasta existe.')
        return project

    def _dispatch(self, identifier, operation, arguments):
        project = self._project(identifier)
        self._executor.roots[identifier] = {'path': project['path'], 'writable': True}
        return self._executor.dispatch({'request_id': uuid.uuid4().hex, 'root_id': identifier,
                                       'operation': operation, 'arguments': arguments, 'can_write': True})

    @result
    def state(self):
        settings = self._agent.load()
        return {'projects': self._projects(), 'server': settings.get('server', ''),
                'paired': bool(settings.get('token')), 'paused': bool(settings.get('paused')),
                'agent_exe': self._settings.get('agent_exe', '')}

    @result
    def add_project(self, path=None):
        if path is None:
            import webview
            chosen = self._window.create_file_dialog(webview.FileDialog.FOLDER)
            if not chosen:
                return None
            path = chosen[0]
        path = str(Path(path).resolve(strict=True))
        if not Path(path).is_dir():
            raise ValueError('Escolha uma pasta.')
        with SafeRoot(path).parent('probe'):
            pass
        existing = next((p for p in self._projects() if os.path.normcase(p['path']) == os.path.normcase(path)), None)
        if existing:
            return existing
        project = {'id': uuid.uuid4().hex, 'name': Path(path).name, 'path': path}
        self._settings['projects'].append(project)
        self._save()
        return project

    @result
    def files(self, identifier, query='', offset=0):
        return self._dispatch(identifier, 'list_files', {'query': query, 'offset': offset, 'limit': 200})

    @result
    def read(self, identifier, filepath):
        project = self._project(identifier)
        root = SafeRoot(project['path'])
        root.allowed(filepath)
        data = root.read(filepath)
        if b'\x00' in data:
            raise ValueError('Arquivo binário não pode ser editado como texto.')
        return {'filepath': filepath, 'content': data.decode('utf-8'), 'newline': '\r\n' if b'\r\n' in data else '\n', 'sha256': sha(data)}

    @result
    def write(self, identifier, filepath, content, digest):
        return self._dispatch(identifier, 'write_file', {'filepath': filepath, 'content': content, 'expected_sha256': digest})

    @result
    def execute(self, identifier, command):
        value = self._dispatch(identifier, 'execute_command', {'command': command})
        self._jobs[value['command_id']] = {'project': identifier, 'command': command}
        return value

    @result
    def poll(self, identifier, command_id):
        job = self._jobs.get(command_id)
        if not job or job['project'] != identifier:
            raise ValueError('Processo não pertence a este projeto.')
        return self._dispatch(identifier, 'execute_command', {'command': job['command'], 'command_id': command_id})

    @result
    def stop(self, identifier, command_id):
        return self._dispatch(identifier, 'stop_command', {'command_id': command_id})

    @result
    def git_status(self, identifier):
        return self._dispatch(identifier, 'git_status', {})

    @result
    def git_diff(self, identifier, filepath, staged=False):
        return self._dispatch(identifier, 'git_diff', {'filepath': filepath, 'staged': staged})

    @result
    def connection(self):
        settings = self._agent.load()
        if not settings.get('token'):
            return {'status': 'not_paired', 'message': 'Nenhum pareamento encontrado no agente.'}
        if settings.get('paused'):
            return {'status': 'paused', 'message': 'Agente pausado.'}
        try:
            response = requests.get(server_url(settings['server'])+'/api/local/status',
                                    headers={'Authorization': 'Bearer '+settings['token']}, timeout=8, allow_redirects=False)
            if response.status_code in (401,403):
                return {'status':'unauthorized','message':'Credencial recusada pela VM. Confira o pareamento no agente.'}
            if response.status_code != 200:
                return {'status':'unknown','message':'Status indisponível. Atualize a VM para habilitar esta consulta.'}
            data=response.json()
            if not isinstance(data.get('online'),bool):
                raise ValueError('invalid status')
            return {'status':'online' if data['online'] else 'offline',
                    'message':'Agente conectado à VM.' if data['online'] else 'Agente desconectado da VM.'}
        except (requests.RequestException,ValueError):
            return {'status':'unknown','message':'Não foi possível consultar a VM. Os projetos locais continuam disponíveis.'}

    @result
    def choose_agent(self):
        import webview
        files=self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=('Aplicativo Windows (*.exe)',))
        if files:
            path=Path(files[0]).resolve(strict=True)
            if path.suffix.lower()!='.exe':
                raise ValueError('Selecione o OkestreLocal.exe existente.')
            self._settings['agent_exe']=str(path)
            self._save()
        return self._settings.get('agent_exe','')

    @result
    def open_agent(self):
        path=Path(self._settings.get('agent_exe',''))
        if not path.is_file() or path.suffix.lower()!='.exe':
            raise ValueError('Primeiro selecione o executável OkestreLocal.exe.')
        subprocess.Popen([str(path)],cwd=path.parent,creationflags=subprocess.CREATE_NO_WINDOW)
        return 'Abra o agente pelo ícone da bandeja se ele já estiver em execução.'

    @result
    def open_vm(self):
        url=self._agent.load().get('server')
        if not url:
            raise ValueError('Faça o pareamento no agente para registrar o endereço da VM.')
        webbrowser.open(server_url(url)+'/local-devices')
        return True

    @result
    def diagrams(self):
        import webview
        webview.create_window('Okestre · Diagramas ER',self._diagram_url,width=1300,height=850,min_size=(850,600))
        return True

    def _close(self):
        with self._lock:
            self._executor.terminal.close()
