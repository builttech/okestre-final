from types import SimpleNamespace
from unittest.mock import patch
import json
import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from gitide_server.ops_git_access import GitAccess, GitAccessRequest

@pytest.fixture
def profile(tmp_path):
    cipher=Fernet(Fernet.generate_key())
    manager=GitAccess(tmp_path/'profile',lambda v:'fernet:'+cipher.encrypt(v.encode()).decode(),lambda v:cipher.decrypt(v.removeprefix('fernet:').encode()).decode() if v else '')
    project=SimpleNamespace(path=str(tmp_path/'project'))
    return manager,project

def request(**kw):
    return GitAccessRequest(**({'repository':'https://github.com/example/private','branch':'main','token':'test-token'}|kw))

def test_encrypted_profile_and_preserved_token(profile):
    manager,project=profile
    public=manager.save(project,request())
    assert public['has_token'] and 'token' not in public
    assert 'test-token' not in manager.path(project).read_text()
    manager.save(project,request(token='',allow_push=True))
    assert manager.require(project,'push')[1]=='test-token'
    manager.save(project,request(token='',remove_token=True))
    with pytest.raises(HTTPException):manager.require(project,'read')

@pytest.mark.parametrize('url',['https://evil.example/x/y','https://token@github.com/x/y','https://github.com/x/y?token=x'])
def test_reject_untrusted_repositories(profile,url):
    with pytest.raises(HTTPException):profile[0].save(profile[1],request(repository=url))

def test_denies_push_and_deploy(profile):
    manager,project=profile;manager.save(project,request())
    with patch('gitide_server.ops_git_access.subprocess.run') as run:
        with pytest.raises(HTTPException):manager.local(project,'push')
        run.assert_not_called()
    with pytest.raises(HTTPException):manager.check_deploy(project,'up')
    manager.check_deploy(project,'logs')

def test_remote_secret_only_in_stdin_and_output_redacted(profile):
    manager,project=profile;manager.save(project,request(allow_deploy=True))
    observed={}
    def run(access,command,**kwargs):
        observed.update(command=command,**kwargs)
        return {'stdout':'test-token','stderr':'','command':command,'exit_code':0,'status':'success'}
    result=manager.remote_sync(project,{},'/opt/app',run)
    assert observed['command']=='sh -s'
    assert 'GIT_CONFIG_VALUE_0' in observed['stdin']
    assert 'git pull --ff-only' in observed['stdin']
    assert 'test-token' not in json.dumps(result)

def test_local_git_scoped_auth_and_branch(profile):
    manager,project=profile;manager.save(project,request(allow_push=True))
    responses=[SimpleNamespace(stdout='https://github.com/example/private.git\n',returncode=0),SimpleNamespace(stdout='main\n',returncode=0),SimpleNamespace(stdout='ok',stderr='',returncode=0)]
    with patch('gitide_server.ops_git_access.subprocess.run',side_effect=responses) as run:
        assert manager.local(project,'push')['status']=='success'
        command=run.call_args.args[0]
        assert command==['git','push','https://github.com/example/private.git','HEAD:refs/heads/main']
        assert 'test-token' not in str(command)
        assert run.call_args.kwargs['env']['GIT_TERMINAL_PROMPT']=='0'

def test_provider_check_uses_saved_token_without_returning_it(profile):
    manager,project=profile;manager.save(project,request())
    response=SimpleNamespace(status_code=200,json=lambda:{'full_name':'example/private','private':True,'permissions':{'push':True}})
    with patch('gitide_server.ops_git_access.requests.get',return_value=response) as get:
        result=manager.test(project)
        assert result['private'] and 'test-token' not in json.dumps(result)
        assert get.call_args.kwargs['allow_redirects'] is False

def test_ops_encryption_fails_closed(tmp_path):
    import os
    import subprocess
    import sys
    env=os.environ.copy()
    env['GITIDE_DATA_DIR']=str(tmp_path/'isolated-server')
    script='''from gitide_server import main
from fastapi import HTTPException
original=main._ops_secret_key
main._ops_secret_key=lambda: (_ for _ in ()).throw(RuntimeError('unavailable'))
try:
 try:
  main._ops_encrypt_secret('test-only-secret')
  raise AssertionError('Encryption failure must not fall back')
 except HTTPException as error:
  assert error.status_code==500
finally:
 main._ops_secret_key=original
assert main._ops_decrypt_secret(main._ops_encrypt_secret('test-only-secret'))=='test-only-secret'
'''
    result=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr
