"""Browser regression for audit filters and navigation to a connection."""
import asyncio
import unittest
from pathlib import Path
from urllib.parse import urlsplit

import test_mcp_oauth
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    sync_playwright = None


@unittest.skipUnless(sync_playwright, "Install playwright and Edge for browser tests")
class AuditBrowserTests(unittest.TestCase):
    def test_filters_navigation_and_layout(self):
        fixture = test_mcp_oauth.OAuthTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.provider.list_projects = lambda: [{"id": 7, "name": "Projeto de teste"}]
        tokens = fixture.exchange(fixture.approve()["code"][0]).json()
        grant = asyncio.run(fixture.provider.load_access_token(tokens["access_token"]))
        for index in range(27):
            fixture.provider.audit.record(grant=grant, tool="read_file" if index % 2 else "patch_file",
                project_id=7, outcome="success" if index % 2 else "denied", duration_ms=10)
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
                if parsed.path == "/audit-test":
                    route.fulfill(content_type="text/html", body='''<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/mcp-connections.css">
<style>body{font:14px system-ui;background:#111;color:#eee;margin:24px}button{padding:8px;cursor:pointer}main{max-width:1100px;margin:auto}</style>
<main><div id="audit"></div><div id="connections" hidden></div></main>
<script src="/static/mcp-connections.js"></script><script src="/static/mcp-audit.js"></script>
<script>const audit=mountMcpAudit(document.getElementById('audit'));
const connections=mountMcpConnections(document.getElementById('connections'));audit.load();
window.addEventListener('gitide:mcp-show-connection',e=>{connections.selectConnection(e.detail);
document.getElementById('audit').hidden=true;document.getElementById('connections').hidden=false;connections.load()});</script>''')
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
            page.goto("http://localhost/audit-test")
            expect(page.locator('[data-audit-count]')).to_have_text('1–25 de 27')
            page.get_by_role("button", name="Próxima página do histórico").click()
            expect(page.locator('[data-audit-count]')).to_have_text('26–27 de 27')
            page.get_by_label("Resultado", exact=True).select_option("success")
            page.get_by_label("Ferramenta", exact=True).select_option("read_file")
            page.get_by_label("Projeto", exact=True).select_option("7")
            page.get_by_role("button", name="Filtrar", exact=True).click()
            expect(page.locator('[data-audit-count]')).to_have_text('1–13 de 13')
            expect(page.get_by_role("cell", name="Acesso negado", exact=True)).to_have_count(0)
            page.screenshot(path=str(output / "mcp-audit-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            self.assertTrue(page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            page.screenshot(path=str(output / "mcp-audit-mobile.png"))
            page.get_by_label("Até", exact=True).fill("2000-01-01T00:00")
            page.get_by_role("button", name="Filtrar", exact=True).click()
            expect(page.get_by_text("Nenhuma chamada encontrada.")).to_be_visible()
            page.get_by_role("button", name="Limpar", exact=True).click()
            expect(page.locator('[data-audit-count]')).to_have_text('1–25 de 27')
            failure[0] = True
            page.get_by_role("button", name="Atualizar histórico").click()
            expect(page.get_by_text("Servico indisponivel")).to_be_visible()
            failure[0] = False
            page.get_by_role("button", name="Atualizar histórico").click()
            expect(page.get_by_text("Servico indisponivel")).not_to_be_visible()
            page.get_by_role("button", name="Ver conexão", exact=True).first.click()
            expect(page.get_by_role("heading", name="Conexões MCP")).to_be_visible()
            expect(page.get_by_role("cell", name="Ativa", exact=True)).to_be_visible()
            self.assertEqual(errors, [])
            browser.close()


if __name__ == "__main__":
    unittest.main()
