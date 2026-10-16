from pathlib import Path
from test_desktop import desktop
from playwright.sync_api import sync_playwright, expect


def test_system_tests_persistence_details_and_status(desktop):
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(desktop['url'])
        page.wait_for_function("typeof state!=='undefined' && Boolean(state.apiKey)")
        page.locator('#project-selector').select_option(label='Demo')
        page.locator('[data-tab="tab-system-tests"]').click()
        expect(page.locator('#e2e-rows')).to_contain_text('Nenhum teste cadastrado')
        expect(page.locator('#e2e-new')).to_be_enabled()
        assert (desktop['project']/'.documents/test/test.md').exists()
        page.locator('#e2e-new').click()
        page.locator('#e2e-title').fill('Concluir compra e confirmar persistência')
        page.locator('#e2e-task').fill('TASK-RF-0001-01-001')
        page.locator('#e2e-rf').fill('RF-0001-01')
        page.locator('#e2e-status').select_option('Aprovado')
        page.locator('#e2e-save').click()
        expect(page.locator('#e2e-save-message')).to_contain_text('registre o resultado')
        page.locator('#e2e-status').select_option('Não executado')
        page.locator('#e2e-save').click()
        expect(page.locator('#e2e-drawer')).to_have_attribute('aria-hidden','true')
        expect(page.locator('#e2e-rows')).to_contain_text('TEST-E2E-001')
        page.reload()
        page.wait_for_function("typeof state!=='undefined' && Boolean(state.apiKey)")
        page.locator('#project-selector').select_option(label='Demo')
        page.locator('[data-tab="tab-system-tests"]').click()
        page.get_by_role('button',name='Detalhes',exact=True).click()
        expect(page.locator('#e2e-title')).to_have_value('Concluir compra e confirmar persistência')
        body=page.locator('#e2e-details').input_value()
        body=body.replace('**Resultado obtido:** Não executado.','**Resultado obtido:** Pedido confirmado e persistido após recarga.').replace('**Evidências:**','**Evidências:** evidencias/compra.png')
        page.locator('#e2e-details').fill(body)
        page.locator('#e2e-status').select_option('Aprovado')
        output=Path(__file__).parents[1]/'outputs/desktop-qa'
        page.wait_for_function("document.getElementById('e2e-drawer').getBoundingClientRect().right <= innerWidth+1")
        page.screenshot(path=str(output/'system-test-detail.png'))
        page.locator('#e2e-save').click()
        expect(page.locator('#e2e-drawer')).to_have_attribute('aria-hidden','true')
        expect(page.locator('#e2e-summary')).to_contain_text('1 aprovados')
        source=(desktop['project']/'.documents/test/test.md').read_text(encoding='utf-8')
        assert '- [x] TEST-E2E-001: Concluir compra' in source
        details=(desktop['project']/'.documents/test/test.details.md').read_text(encoding='utf-8')
        assert 'Pedido confirmado' in details and 'evidencias/compra.png' in details
        page.locator('#e2e-filter').select_option('Reprovado')
        expect(page.locator('#e2e-rows')).to_contain_text('Nenhum teste corresponde')
        page.locator('#e2e-filter').select_option('')
        page.screenshot(path=str(output/'system-tests.png'))
        # Concurrent external edits must not be overwritten.
        page.get_by_role('button',name='Detalhes',exact=True).click()
        detail_path=desktop['project']/'.documents/test/test.details.md'
        detail_path.write_text(details+'\nRegistro externo\n',encoding='utf-8')
        page.locator('#e2e-title').fill('Título concorrente')
        page.locator('#e2e-save').click()
        expect(page.locator('#e2e-save-message')).to_contain_text('outra operação')
        assert 'Registro externo' in detail_path.read_text(encoding='utf-8')
        assert not errors,errors
        browser.close()
