from pathlib import Path
import json
import pytest
from test_local_bridge import live, eventually

@pytest.mark.parametrize("route", ["/connect-device", "/local-devices"])
def test_wizard_multiple_projects_and_mobile(live, tmp_path, route):
    playwright = pytest.importorskip("playwright.sync_api")
    config, folder, marker, project = live.enroll()
    for name in ("sendget", "meu-site"):
        root = tmp_path / name
        root.mkdir()
        config.add_root(root, name, writable=name == "sendget")
    device_id = config.load()["device_id"]
    eventually(lambda: len(json.loads(live.bridge.store.get(device_id)["roots"])) == 3, seconds=12)
    output = Path(__file__).parents[1] / "outputs/local-bridge-qa"
    output.mkdir(parents=True, exist_ok=True)
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 1000})
        context.add_cookies([{"name": "session", "value": "owner", "url": live.url}])
        page = context.new_page()
        errors, calls = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: calls.append(request.url))
        page.goto(live.url + route)
        expect = playwright.expect
        expect(page.locator("#step-1")).to_be_visible()
        expect(page.locator("#step-2")).to_be_hidden()
        expect(page.get_by_role("heading", name="Arquivos locais")).to_have_count(0)
        page.get_by_role("button", name="Continuar para projetos").click()
        expect(page.locator("#step-2")).to_be_visible()
        expect(page.get_by_text("Já adicionado", exact=True)).to_have_count(1)
        page.get_by_label("Selecionar todas as pastas disponíveis").check()
        page.get_by_label("Nome do projeto meu-site", exact=True).fill("Site principal")
        page.get_by_role("button", name="Atualizar pastas", exact=True).click()
        expect(page.get_by_label("Nome do projeto meu-site", exact=True)).to_have_value("Site principal")
        expect(page.get_by_label("Selecionar meu-site", exact=True)).to_be_checked()
        page.screenshot(path=str(output / "wizard-projects-desktop.png"), full_page=True)
        page.get_by_role("button", name="Adicionar 2 projeto(s) selecionado(s)", exact=True).click()
        expect(page.locator("#step-3")).to_be_visible()
        expect(page.locator("#connected-projects .card")).to_have_count(3)
        expect(page.locator("#mcp-url")).to_have_value(live.url + "/mcp/")
        expect(page.locator("#notice")).to_contain_text("2 projeto(s) adicionado(s)")
        page.get_by_role("button", name="Adicionar mais projetos").click()
        expect(page.locator("#add-projects")).to_be_disabled()
        expect(page.get_by_text("Já adicionado", exact=True)).to_have_count(3)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(output / "wizard-projects-mobile.png"), full_page=True)
        page.get_by_role("button", name="Ver projetos conectados").click()
        page.screenshot(path=str(output / "wizard-gpt-mobile.png"), full_page=True)
        assert not any("/api/local/call" in url for url in calls)
        assert folder.joinpath("README.md").read_text() == marker
        assert not errors
        context.close()
        browser.close()

def test_empty_state_pairing_and_error_keeps_step(live):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context()
        context.add_cookies([{"name": "session", "value": "owner", "url": live.url}])
        page = context.new_page()
        page.goto(live.url + "/connect-device")
        expect = playwright.expect
        expect(page.locator("#pair-details")).to_have_attribute("open", "")
        expect(page.locator("#to-projects")).to_be_disabled()
        page.get_by_label("Nome do computador").fill("Meu notebook")
        page.get_by_role("button", name="Gerar código", exact=True).click()
        expect(page.locator("#pair-result")).to_be_visible()
        expect(page.locator("#server-url")).to_have_value(live.url)
        assert len(page.locator("#pair-code").input_value()) > 20
        page.route("**/api/local/devices", lambda route: route.fulfill(status=503, content_type="application/json", body="{}"))
        page.get_by_role("button", name="Atualizar conexão").click()
        expect(page.locator("#notice")).to_contain_text("Não foi possível")
        expect(page.locator("#step-1")).to_be_visible()
        context.close()
        browser.close()
