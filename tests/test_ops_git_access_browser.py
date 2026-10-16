from test_desktop import desktop
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

def test_git_access_screen_save_reload_remove(desktop):
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.goto(desktop['url']);page.wait_for_function("typeof state!=='undefined' && Boolean(state.apiKey)")
        page.locator('#project-selector').select_option(label='Demo')
        page.locator('[data-tab="tab-ops-infra"]').click()
        page.locator('[data-ops-flow-tab="git-access"]').click()
        expect(page.locator('#ops-git-save')).to_be_enabled()
        page.locator('#ops-git-repo').fill('https://github.com/example/private')
        page.locator('#ops-git-token').fill('test-only-not-a-real-token')
        page.locator('#ops-git-save').click()
        expect(page.locator('#ops-git-status')).to_have_text('Acessos e autorizações salvos.')
        expect(page.locator('#ops-git-token')).to_have_value('')
        path=desktop['home']/'server/git-access'
        assert 'test-only-not-a-real-token' not in next(path.glob('*.json')).read_text()
        headers=page.evaluate('getHeaders()')
        project_id=page.evaluate('state.activeProjectId')
        url=desktop['origin']+f'/api/projects/{project_id}/ops-infra/git-access'
        data=page.request.get(url,headers=headers).json()
        assert data['has_token'] and 'token' not in data
        assert page.request.post(url+'/action',headers=headers,data={'action':'push'}).status==403
        page.screenshot(path=str(Path(__file__).parents[1]/'outputs/desktop-qa/ops-git-access.png'))
        page.once('dialog',lambda d:d.accept())
        page.locator('#ops-git-remove').click()
        expect(page.locator('#ops-git-status')).to_have_text('Token removido.')
        assert not page.request.get(url,headers=headers).json()['has_token']
        browser.close()
