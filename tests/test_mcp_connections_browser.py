"""Optional Edge test for connection management against the real OAuth handlers."""
import unittest
from pathlib import Path
from urllib.parse import urlsplit

import test_mcp_oauth
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    sync_playwright = None


@unittest.skipUnless(sync_playwright, "Install playwright and Edge for browser tests")
class ConnectionsBrowserTests(unittest.TestCase):
    def test_manage_ui(self):
        fixture = test_mcp_oauth.OAuthTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.client.cookies.set("login", "yes")
        static = Path(__file__).resolve().parents[1] / "gitide_server" / "static"
        output = Path(__file__).resolve().parents[1] / "outputs"
        output.mkdir(exist_ok=True)
        failure = [False]
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))

            def handle(route):
                req = route.request
                parsed = urlsplit(req.url)
                if parsed.path == "/settings-test":
                    route.fulfill(content_type="text/html", body='''<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/mcp-connections.css">
<style>body{font:14px system-ui;background:#111;color:#eee;margin:24px}button{padding:8px;cursor:pointer}#panel{max-width:1100px;margin:auto}</style>
<main id="panel"></main><script src="/static/mcp-connections.js"></script>
<script>window.manager=mountMcpConnections(document.getElementById('panel'));manager.load()</script>''')
                elif parsed.path.startswith("/static/"):
                    path = static / Path(parsed.path).name
                    route.fulfill(content_type="text/css" if path.suffix == ".css" else "text/javascript", body=path.read_text(encoding="utf-8"))
                elif failure[0]:
                    route.fulfill(status=503, content_type="application/json", body='{"detail":"Servico indisponivel"}')
                else:
                    response = fixture.client.request(req.method, parsed.path + "?" + parsed.query,
                        content=req.post_data, headers={**req.headers, "Cookie": "login=yes"})
                    route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)

            page.route("http://localhost/**", handle)
            page.goto("http://localhost/settings-test")
            expect(page.get_by_text("Nenhuma conexão OAuth autorizada.")).to_be_visible()
            fixture.exchange(fixture.approve()["code"][0])
            page.get_by_role("button", name="Atualizar conexões").click()
            expect(page.get_by_role("cell", name="Ativa", exact=True)).to_be_visible()
            page.screenshot(path=str(output / "mcp-connections-desktop.png"))
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            page.get_by_role("button", name="Revogar Test client").click()
            expect(page.get_by_role("dialog")).to_be_visible()
            page.screenshot(path=str(output / "mcp-connections-mobile.png"))
            page.get_by_role("button", name="Cancelar", exact=True).click()
            self.assertEqual(fixture.provider.connections.page(0, 10)["items"][0]["status"], "active")
            page.get_by_role("button", name="Revogar Test client").click()
            page.get_by_role("button", name="Revogar conexão", exact=True).click()
            expect(page.get_by_role("cell", name="Revogada", exact=True)).to_be_visible()
            expect(page.get_by_role("dialog")).not_to_be_visible()
            failure[0] = True
            page.get_by_role("button", name="Atualizar conexões").click()
            expect(page.get_by_text("Servico indisponivel")).to_be_visible()
            failure[0] = False
            page.get_by_role("button", name="Atualizar conexões").click()
            expect(page.get_by_text("Servico indisponivel")).not_to_be_visible()
            self.assertEqual(errors, [])
            browser.close()


if __name__ == "__main__":
    unittest.main()
