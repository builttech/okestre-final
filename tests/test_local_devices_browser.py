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
