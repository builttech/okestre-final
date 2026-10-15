import json
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path

from okestre_desktop.api import DesktopAPI
from okestre_desktop.app import prepare_ui
from okestre_local.config import Config
from test_local_bridge import live


def test_desktop_files_terminal_git_and_agent_config_unchanged(tmp_path):
    project=tmp_path/'project';project.mkdir()
    content='linha\n'*450
    (project/'file.txt').write_bytes(content.encode())
    agent=Config(tmp_path/'agent');agent.save({'roots':{},'server':'https://example.invalid','token':'secret','device_id':'test'})
    before=agent.file.read_bytes()
    api=DesktopAPI(tmp_path/'desktop',agent.home)
    item=api.add_project(str(project))['data'];identifier=item['id']
    assert api.state()['data']['projects'][0]['path']==str(project)
    read=api.read(identifier,'file.txt')['data']
    assert read['content']==content
    assert api.write(identifier,'file.txt',content+'edited',read['sha256'])['ok']
    assert not api.write(identifier,'file.txt','stale',read['sha256'])['ok']
    assert not api.read(identifier,'../outside.txt')['ok']
    assert not api.read(identifier,'.env')['ok']
    result=api.execute(identifier,'echo desktop-test')['data']
    assert 'desktop-test' in result['output']
    assert api.poll(identifier,result['command_id'])['ok']
    subprocess.run(['git','init',str(project)],capture_output=True,check=True)
    assert 'file.txt' in api.git_status(identifier)['data']['output']
    api._close()
    assert agent.file.read_bytes()==before
    assert len(DesktopAPI(tmp_path/'desktop',agent.home).state()['data']['projects'])==1


def test_device_status_requires_device_token(live):
    assert live.client.get('/api/local/status').status_code==401
    config,folder,marker,project=live.enroll()
    response=live.client.get('/api/local/status',headers={'Authorization':'Bearer '+config.load()['token']})
    assert response.status_code==200 and response.json()=={'online':True}
    assert response.headers['cache-control']=='no-store'
    live.active=False
    assert live.client.get('/api/local/status',headers={'Authorization':'Bearer '+config.load()['token']}).status_code==401


def test_desktop_browser_with_real_native_api(tmp_path):
    from playwright.sync_api import sync_playwright, expect
    home=tmp_path/'desktop';home.mkdir()
    ui=prepare_ui(home)
    project=tmp_path/'Demo';project.mkdir();(project/'README.md').write_text('Desktop file')
    api=DesktopAPI(home,tmp_path/'agent')
    api.add_project(str(project))
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ui)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1400,'height':900})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.expose_function('nativeCall',lambda method,args:getattr(api,method)(*args))
            page.add_init_script('window.pywebview={api:new Proxy({}, {get:(_,name)=>(...args)=>window.nativeCall(name,args)})};')
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            page.evaluate("window.dispatchEvent(new Event('pywebviewready'))")
            page.get_by_role('button',name='Demo',exact=False).click()
            page.get_by_role('button',name='README.md',exact=True).click()
            expect(page.locator('#content')).to_have_value('Desktop file')
            page.locator('#content').fill('Edited in Desktop')
            page.get_by_role('button',name='Salvar',exact=True).click()
            expect(page.locator('#notice')).to_have_text('Arquivo salvo.')
            assert (project/'README.md').read_text()=='Edited in Desktop'
            page.get_by_role('button',name='Terminal',exact=True).click()
            page.get_by_label('Comando',exact=True).fill('echo browser-terminal')
            page.get_by_role('button',name='Executar',exact=True).click()
            expect(page.locator('#terminal-output')).to_contain_text('browser-terminal')
            page.get_by_role('button',name='Arquivos',exact=True).click()
            output=Path(__file__).parents[1]/'outputs/desktop-qa';output.mkdir(exist_ok=True,parents=True)
            page.screenshot(path=str(output/'desktop.png'),full_page=True)
            assert not errors
            browser.close()
    finally:
        api._close();server.shutdown();server.server_close();thread.join(3)
