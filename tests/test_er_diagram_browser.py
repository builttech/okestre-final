from pathlib import Path
import pytest
from test_local_bridge import live


def test_er_editor_roundtrip_export_and_mobile(live, tmp_path):
    from playwright.sync_api import sync_playwright, expect
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width':1440,'height':1000}, accept_downloads=True)
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(live.url+'/static/er-diagram.html')
        expect(page.locator('#preview svg')).to_be_visible(timeout=20000)
        expect(page.locator('#counts')).to_have_text('8 entidades · 9 relações')
        page.get_by_role('button',name='Código',exact=True).click()
        source=page.locator('#source').input_value()
        assert 'erDiagram\n  direction TB' in source
        assert 'CUSTOMER }|..|{ DELIVERY-ADDRESS : "has"' in source
        assert 'Nome Nome FK "tetre"' in source
        page.get_by_role('button',name='Aplicar código',exact=True).click()
        expect(page.locator('#svg-export')).to_be_enabled()
        with page.expect_download() as d:
            page.get_by_role('button',name='Exportar Mermaid',exact=True).click()
        assert Path(d.value.path()).read_text(encoding='utf-8')==source
        page.get_by_role('button',name='Entidades',exact=True).click()
        page.get_by_role('button',name='+ Entidade',exact=True).click()
        page.get_by_label('Nome da entidade',exact=True).fill('PAYMENT')
        page.get_by_label('Nome da entidade',exact=True).press('Tab')
        page.get_by_role('button',name='+ Atributo',exact=True).click()
        page.get_by_label('Chave',exact=True).select_option('PK,FK')
        expect(page.locator('#source')).to_have_value(__import__('re').compile('PAYMENT \\{'))
        page.locator('#direction').select_option('LR')
        expect(page.locator('#svg-export')).to_be_enabled()
        page.reload()
        expect(page.locator('#counts')).to_have_text('9 entidades · 9 relações')
        expect(page.locator('#direction')).to_have_value('LR')
        page.get_by_role('button',name='Código',exact=True).click()
        before=page.locator('#source').input_value()
        page.locator('#source').fill('erDiagram\n invalid <script>')
        page.get_by_role('button',name='Aplicar código',exact=True).click()
        expect(page.locator('#message')).to_contain_text('Linha 2')
        expect(page.locator('#counts')).to_have_text('9 entidades · 9 relações')
        page.locator('#source').fill(before)
        page.get_by_role('button',name='Aplicar código',exact=True).click()
        expect(page.locator('#svg-export')).to_be_enabled()
        with page.expect_download() as d:
            page.get_by_role('button',name='Exportar SVG',exact=True).click()
        assert '<svg' in Path(d.value.path()).read_text(encoding='utf-8')
        output=Path(__file__).parents[1]/'outputs/local-bridge-qa'
        output.mkdir(exist_ok=True,parents=True)
        page.screenshot(path=str(output/'er-diagram-desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(output/'er-diagram-mobile.png'),full_page=True)
        assert not errors, errors
        browser.close()

def test_import_and_visual_relationships(live, tmp_path):
    from playwright.sync_api import sync_playwright, expect
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page()
        page.on('dialog',lambda d:d.accept())
        page.goto(live.url+'/static/er-diagram.html')
        expect(page.locator('#preview svg')).to_be_visible()
        source='erDiagram\n  direction TB\n  A {\n  }\n  B {\n    int id PK "Identifier"\n  }\n'
        path=tmp_path/'import.mmd';path.write_text(source)
        page.locator('#file').set_input_files(path)
        expect(page.locator('#counts')).to_have_text('2 entidades · 0 relações')
        page.get_by_role('button',name='Relações',exact=True).click()
        page.get_by_role('button',name='+ Relação',exact=True).click()
        page.get_by_label('Cardinalidade da origem',exact=True).select_option('many')
        page.get_by_label('Cardinalidade do destino',exact=True).select_option('many')
        page.get_by_label('Linha',exact=True).select_option('no')
        page.get_by_label('Rótulo',exact=True).fill('has')
        page.get_by_label('Rótulo',exact=True).press('Tab')
        expect(page.locator('#source')).to_have_value(__import__('re').compile('A }\\|\\.\\.\\|\\{ B : "has"'))
        page.get_by_role('button',name='Entidades',exact=True).click()
        page.get_by_label('Nome da entidade',exact=True).fill('CUSTOMER')
        page.get_by_label('Nome da entidade',exact=True).press('Tab')
        expect(page.locator('#source')).to_have_value(__import__('re').compile('CUSTOMER }\\|'))
        page.get_by_role('button',name='Excluir entidade',exact=True).click()
        expect(page.locator('#counts')).to_have_text('1 entidades · 0 relações')
        expect(page.locator('#svg-export')).to_be_enabled()
        browser.close()
