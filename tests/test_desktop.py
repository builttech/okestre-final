import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests
from okestre_local.config import Config


@pytest.fixture
def desktop(tmp_path):
    home = tmp_path / 'desktop'
    home.mkdir()
    project = tmp_path / 'Demo'
    project.mkdir()
    (project / 'sample.txt').write_text('Desktop file', encoding='utf-8')
    subprocess.run(['git', 'init', str(project)], capture_output=True, check=True)
    agent = Config(tmp_path / 'agent')
    agent.save({'roots': {}, 'server': 'https://example.invalid', 'token': 'test', 'device_id': 'test'})
    before = agent.file.read_bytes()
    (home / 'workspace.json').write_text(json.dumps({'projects': [{'id': 'demo', 'name': 'Demo', 'path': str(project)}], 'agent_exe': ''}))
    ready = tmp_path / 'ready.json'
    stop = tmp_path / 'stop'
    script = '''import sys,time,json
from pathlib import Path
from okestre_desktop.runtime import Runtime
r=Runtime(sys.argv[1],sys.argv[2])
try:
 Path(sys.argv[3]).write_text(json.dumps({'url':r.start(),'origin':r.origin,'key':r.secret}))
 while not Path(sys.argv[4]).exists():time.sleep(.1)
finally:r.close()
'''
    with (tmp_path / 'server.log').open('w') as log:
        process = subprocess.Popen([sys.executable, '-c', script, str(home), str(agent.home), str(ready), str(stop)], stdout=log, stderr=log)
        try:
            for _ in range(300):
                if ready.exists(): break
                if process.poll() is not None: pytest.fail((tmp_path / 'server.log').read_text())
                time.sleep(.1)
            assert ready.exists()
            yield dict(json.loads(ready.read_text()), project=project, home=home)
        finally:
            stop.touch()
            try: process.wait(15)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
    assert agent.file.read_bytes() == before


def test_full_desktop_browser_and_security(desktop):
    from playwright.sync_api import sync_playwright, expect
    origin = desktop['origin']
    assert requests.get(origin + '/api/info').status_code in (401, 403)
    assert requests.get(origin, headers={'Host': 'evil.example'}).status_code == 403
    assert requests.post(origin + '/desktop/action', headers={'Origin': 'https://evil.example'}).status_code == 403
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 950})
        page.goto(desktop['url'])
        page.wait_for_function("typeof state!=='undefined' && Boolean(state.apiKey)")
        tabs = page.locator('.nav-item[data-tab]').evaluate_all('(els)=>els.map(e=>e.dataset.tab)')
        for tab in ['tab-files','tab-documents','tab-terminal','tab-git','tab-agent','tab-sdd','tab-discovery','tab-qa','tab-database']:
            assert tab in tabs
        assert len(tabs) == 15
        headers = page.evaluate('getHeaders()')
        projects = page.request.get(origin + '/api/projects', headers=headers).json()
        project_id = next(x['id'] for x in projects if x['name'] == 'Demo')
        base = origin + f'/api/projects/{project_id}'
        assert page.request.get(base + '/files/read?filepath=sample.txt', headers=headers).json()['content'] == 'Desktop file'
        response = page.request.post(base + '/files/write', headers=headers, data={'filepath':'sample.txt','content':'Edited by complete app'})
        assert response.ok, response.text()
        assert (desktop['project'] / 'sample.txt').read_text() == 'Edited by complete app'
        response = page.request.get(base + '/git/status', headers=headers)
        assert response.ok, response.text()
        assert 'sample.txt' in response.text()
        page.evaluate('(id)=>{state.activeProjectId=id}', project_id)
        page.locator('[data-tab="tab-terminal"]').click()
        page.locator('#terminal-input').fill('echo full-desktop-terminal')
        page.locator('#terminal-form').evaluate('(el)=>el.requestSubmit()')
        expect(page.locator('#terminal-output')).to_contain_text('full-desktop-terminal')
        expect(page.locator('#terminal-output')).to_contain_text('completed')
        page.locator('[data-tab="tab-sdd"]').click()
        output = Path(__file__).parents[1] / 'outputs/desktop-qa'
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output/'full-desktop.png'), full_page=True)
        assert page.request.post(origin + '/desktop/action', data={'action':'state'}).status == 403
        assert page.request.get(desktop['url']).status == 404
        page.goto(origin + '/local-devices')
        assert 'OkestreLocal' in page.content()
        page.goto(origin + '/diagrams')
        expect(page.locator('#preview svg')).to_be_visible(timeout=20000)
        page.get_by_role('button', name='Salvar no projeto', exact=True).click()
        expect(page.locator('#project-save-confirm')).to_be_enabled()
        page.get_by_label('Projeto de destino').select_option(str(project_id))
        page.get_by_label('Arquivo no projeto').fill('modelo.mmd')
        page.get_by_role('button', name='Salvar arquivo', exact=True).click()
        expect(page.locator('#project-dialog')).not_to_be_visible()
        saved = desktop['project'] / '.documents/diagramas/modelo.mmd'
        assert 'erDiagram' in saved.read_text(encoding='utf-8')
        assert 'CUSTOMER' in saved.read_text(encoding='utf-8')
        expect(page.locator('#diagram-list')).to_contain_text('modelo.mmd')
        page.reload()
        expect(page.locator('#diagram-list')).to_contain_text('modelo.mmd')
        page.once('dialog', lambda dialog: dialog.accept())
        page.locator('#diagram-list').get_by_role('button', name='Abrir').click()
        expect(page.locator('#title')).to_have_value('modelo')

        with page.expect_download() as download:
            page.get_by_role('button', name='Exportar SVG', exact=True).click()
        assert '<svg' in Path(download.value.path()).read_text(encoding='utf-8')
        with page.expect_download() as download:
            page.get_by_role('button', name='Exportar Mermaid', exact=True).click()
        assert 'erDiagram' in Path(download.value.path()).read_text(encoding='utf-8')
        command = 'ping -n 60 127.0.0.1 > nul'
        action_headers = {'X-Desktop-Key':desktop['key']}
        job = page.request.post(origin + '/desktop/action', headers=action_headers, data={'action':'execute','project_id':project_id,'command':command}).json()['data']
        assert job['status'] == 'running'
        time.sleep(31)
        job = page.request.post(origin + '/desktop/action', headers=action_headers, data={'action':'poll','project_id':project_id,'command':command,'command_id':job['command_id']}).json()['data']
        assert job['status'] == 'running' and not job['timed_out']
        job = page.request.post(origin + '/desktop/action', headers=action_headers, data={'action':'stop','project_id':project_id,'command_id':job['command_id']}).json()['data']
        assert job['status'] != 'running'
        browser.close()
    assert (desktop['home']/'server').is_dir()
