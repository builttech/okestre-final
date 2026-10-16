"""Project-scoped GitHub access. Secrets stay outside project folders."""
import base64
import hashlib
import json
import os
import re
import shlex
import subprocess
import threading
from pathlib import Path
import requests
from fastapi import HTTPException
from pydantic import BaseModel, Field

_lock = threading.RLock()
class GitAccessRequest(BaseModel):
    repository: str = Field('', max_length=250)
    branch: str = Field('main', max_length=160)
    token: str = Field('', max_length=2000)
    remove_token: bool = False
    allow_read: bool = True
    allow_push: bool = False
    allow_deploy: bool = False

class GitActionRequest(BaseModel):
    action: str

class GitAccess:
    def __init__(self, home, encrypt, decrypt):
        self.home=Path(home)/'git-access'
        self.encrypt=encrypt
        self.decrypt=decrypt

    def path(self, project):
        key=hashlib.sha256(os.path.normcase(os.path.abspath(project.path)).encode()).hexdigest()
        return self.home/(key+'.json')

    def load(self, project):
        path=self.path(project)
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    def public(self, project):
        data=self.load(project)
        return {k:v for k,v in data.items() if k!='token'} | {'configured':bool(data), 'has_token':bool(data.get('token'))}

    def save(self, project, req):
        repository=req.repository.strip().removesuffix('.git')
        match=re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',repository)
        branch=req.branch.strip()
        if not match or any(x in ('.','..') for x in match.groups()):
            raise HTTPException(400,'Use https://github.com/organizacao/repositorio sem credenciais na URL.')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*',branch) or any(x in branch for x in ('..','//','@{')) or branch.endswith(('/', '.', '.lock')):
            raise HTTPException(400,'Branch inválida.')
        if any(c.isspace() for c in req.token):raise HTTPException(400,'Token inválido.')
        with _lock:
            old=self.load(project)
            token='' if req.remove_token else self.encrypt(req.token) if req.token else old.get('token','')
            if not token and not req.remove_token:raise HTTPException(400,'Informe o token do GitHub.')
            data={'repository':repository+'.git','branch':branch,'allow_read':req.allow_read,'allow_push':req.allow_push,'allow_deploy':req.allow_deploy,'token':token}
            self.home.mkdir(parents=True,exist_ok=True)
            path=self.path(project);temp=path.with_suffix('.tmp')
            temp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(temp,path)
        return self.public(project)

    def require(self, project, permission):
        data=self.load(project)
        if not data or not data.get('allow_'+permission):raise HTTPException(403,'Operação não autorizada na aba Git / Acessos: '+permission)
        token=self.decrypt(data.get('token',''))
        if not token:raise HTTPException(400,'Token ausente ou indisponível. Cadastre novamente.')
        return data,token

    def check_deploy(self, project, action):
        data=self.load(project)
        if data and action not in ('ps','status','logs') and not data.get('allow_deploy'):
            raise HTTPException(403,'Deploy não autorizado na aba Git / Acessos.')

    def test(self, project):
        data,token=self.require(project,'read')
        slug=data['repository'].removeprefix('https://github.com/').removesuffix('.git')
        try:
            response=requests.get('https://api.github.com/repos/'+slug,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'},timeout=15,allow_redirects=False)
        except requests.RequestException:raise HTTPException(502,'Não foi possível consultar o GitHub.')
        if response.status_code!=200:raise HTTPException(400,'GitHub recusou a consulta (HTTP '+str(response.status_code)+'). Confira token, repositório e autorização da organização.')
        info=response.json()
        return {'status':'success','repository':info.get('full_name'),'private':info.get('private'),'permissions_reported':info.get('permissions',{}),'message':'Repositório acessível. Esta consulta não comprova permissão de push nem aprovação de deploy.'}

    def auth_env(self, data, token):
        env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
        auth='AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+token).encode()).decode()
        env.update(GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='3',GIT_CONFIG_KEY_0='http.'+data['repository']+'.extraheader',GIT_CONFIG_VALUE_0=auth,GIT_CONFIG_KEY_1='credential.helper',GIT_CONFIG_VALUE_1='',GIT_CONFIG_KEY_2='http.followRedirects',GIT_CONFIG_VALUE_2='false')
        return env,auth

    def local(self, project, action):
        if action not in ('fetch','pull','push'):raise HTTPException(400,'Ação Git inválida.')
        data,token=self.require(project,'push' if action=='push' else 'read')
        env,auth=self.auth_env(data,token)
        opts={'cwd':project.path,'text':True,'capture_output':True,'timeout':120,'env':env}
        if os.name=='nt':opts['creationflags']=subprocess.CREATE_NO_WINDOW
        try:
            origin=subprocess.run(['git','remote','get-url','origin'],**opts)
            remote=origin.stdout.strip().replace('git@github.com:','https://github.com/').removesuffix('.git')
            if origin.returncode or remote!=data['repository'].removesuffix('.git'):raise HTTPException(400,'O origin local deve corresponder ao repositório cadastrado, sem token na URL.')
            current=subprocess.run(['git','branch','--show-current'],**opts)
            if current.stdout.strip()!=data['branch']:raise HTTPException(400,'Selecione localmente a branch cadastrada antes de executar.')
            args={'fetch':['fetch',data['repository'],data['branch']], 'pull':['pull','--ff-only',data['repository'],data['branch']], 'push':['push',data['repository'],'HEAD:refs/heads/'+data['branch']]}[action]
            result=subprocess.run(['git']+args,**opts)
        except subprocess.TimeoutExpired:raise HTTPException(504,'Tempo esgotado na operação Git. Confira o estado antes de repetir.')
        except OSError:raise HTTPException(400,'Git não está disponível neste computador.')
        def clean(value):return value.replace(token,'[redacted]').replace(auth,'[redacted]')[-16000:]
        return {'status':'success' if result.returncode==0 else 'error','exit_code':result.returncode,'stdout':clean(result.stdout),'stderr':clean(result.stderr)}

    def remote_sync(self, project, access, app_path, run_ssh):
        data,token=self.require(project,'deploy')
        if not data.get('allow_read'):raise HTTPException(403,'Leitura Git não autorizada.')
        _,auth=self.auth_env(data,token)
        q=shlex.quote;url=q(data['repository']);branch=q(data['branch']);path=q(app_path)
        script='set -eu\nset +x\nexport GIT_TERMINAL_PROMPT=0\nexport GIT_CONFIG_COUNT=3\n'
        script+='export GIT_CONFIG_KEY_0='+q('http.'+data['repository']+'.extraheader')+'\nexport GIT_CONFIG_VALUE_0='+q(auth)+'\n'
        script+="export GIT_CONFIG_KEY_1=credential.helper\nexport GIT_CONFIG_VALUE_1=''\nexport GIT_CONFIG_KEY_2=http.followRedirects\nexport GIT_CONFIG_VALUE_2=false\n"
        script+=f'''if [ -d {path}/.git ]; then
cd {path}
test "$(git remote get-url origin)" = {url} || {{ echo 'Origin diferente do cadastrado'; exit 2; }}
test "$(git branch --show-current)" = {branch} || {{ echo 'Branch diferente da cadastrada'; exit 2; }}
git pull --ff-only {url} {branch}
else
git clone --single-branch --branch {branch} {url} {path}
fi
cd {path}
git log -1 --oneline
'''
        result=run_ssh(access,'sh -s',timeout=240,stdin=script)
        for key in ('stdout','stderr','command'):
            if key in result:result[key]=result[key].replace(token,'[redacted]').replace(auth,'[redacted]')
        return result
