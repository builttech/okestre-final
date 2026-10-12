from pathlib import Path

import pytest

from test_local_bridge import live


def test_local_device_panel_read_edit_and_mobile(live):
    playwright = pytest.importorskip("playwright.sync_api")
    sync_playwright, expect = playwright.sync_playwright, playwright.expect
    config, folder, marker, project = live.enroll()
    output = Path(__file__).parents[1] / "outputs/local-bridge-qa"
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_cookies([{"name": "session", "value": "owner", "url": live.url}])
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live.url + f"/local-devices?project={project}")
        expect(page.get_by_role("button", name="README.md", exact=True)).to_be_visible()
        page.get_by_role("button", name="README.md", exact=True).click()
        expect(page.locator("#content")).to_have_value(marker)
        page.locator("#content").fill(marker + " browser edit")
        page.get_by_role("button", name="Salvar no computador").click()
        expect(page.locator("#notice")).to_contain_text("Salvo no computador")
        assert folder.joinpath("README.md").read_text() == marker + " browser edit"
        # Independent local editor changes the version before the next browser save.
        folder.joinpath("README.md").write_text("external edit", encoding="utf-8")
        page.locator("#content").fill("stale browser edit")
        page.get_by_role("button", name="Salvar no computador").click()
        expect(page.locator("#notice")).to_contain_text("O arquivo mudou")
        assert folder.joinpath("README.md").read_text() == "external edit"
        page.screenshot(path=str(output / "desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(output / "mobile.png"), full_page=True)
        assert not errors
        context.close()
        browser.close()

def test_local_devices_tabs_onboarding_and_folder_cards(live):
    playwright = pytest.importorskip("playwright.sync_api")
    sync_playwright, expect = playwright.sync_playwright, playwright.expect
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        context.add_cookies([{"name": "session", "value": "owner", "url": live.url}])
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live.url + "/local-devices")
        expect(page.get_by_text("Nenhum computador cadastrado")).to_be_visible()
        page.locator("#add-device-empty").click()
        modal = page.get_by_role("dialog", name="Adicionar dispositivo")
        expect(modal).to_be_visible()
        expect(modal.get_by_label("Expiração da chave")).to_be_visible()
        modal.get_by_label("Nome do computador").fill("Notebook pessoal")
        modal.get_by_label("Expiração da chave").select_option("9")
        modal.get_by_role("button", name="Gerar chave").click()
        expect(modal.locator("#pair-code")).not_to_be_empty()
        modal.get_by_role("button", name="Concluir").click()
        expect(page.locator("#computer-cards")).to_contain_text("Notebook pessoal")
        config, folder, marker, project = live.enroll()
        page.locator("#refresh").click()
        expect(page.locator("#computer-cards")).to_contain_text("Windows de teste")
        page.get_by_role("tab", name="Dispositivos e pastas").click()
        expect(page.locator("#devices .folder-card")).to_have_count(1)
        expect(page.locator("#devices")).to_contain_text("Projeto local")
        page.get_by_role("button", name="Adicionar pasta", exact=True).click()
        expect(page.get_by_role("dialog", name="Adicionar pasta")).to_contain_text("Okestre Local")
        page.locator("#close-folder").click()
        page.locator("#devices").get_by_role("button", name="Excluir pasta").click()
        expect(page.get_by_role("dialog", name="Remover cadastro da pasta?")).to_contain_text(
            "Os arquivos físicos não serão apagados")
        page.locator("#confirm-remove-folder").click()
        expect(page.locator("#folder-empty")).to_be_visible()
        assert folder.joinpath("README.md").read_text() == marker
        assert "root_unavailable" in str(live.tool("read_file", project_id=project, filepath="README.md"))
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert not errors
        context.close()
        browser.close()
