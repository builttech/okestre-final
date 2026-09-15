import unittest
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch
import test_mcp_oauth
from gitide_server.integrations import Integrations
from gitide_server.integration_routes import routes
from gitide_server.supabase_oauth import SupabaseOAuth, routes as supabase_routes
from urllib.parse import parse_qs
import time
try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    sync_playwright = None


@unittest.skipUnless(sync_playwright, 'Requires Playwright and Edge')
class IntegrationBrowserTests(unittest.TestCase):
    def test_form_permissions_approvals_and_layout(self):
        fixture = test_mcp_oauth.OAuthTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.provider.list_projects = lambda: [{'id': 7, 'name': 'Projeto de teste'}]
        provider = SupabaseOAuth(fixture.provider.store, 'http://localhost')
        service = Integrations(fixture.provider.store, supabase=provider)
        fixture.client.app.router.routes.extend(supabase_routes(provider, service, fixture.provider))
        fixture.client.app.router.routes.extend(routes(fixture.provider, service))
        static = Path(__file__).resolve().parents[1] / 'gitide_server/static'
        output = Path(__file__).resolve().parents[1] / 'outputs'
        with sync_playwright() as playwright, patch.object(service, 'test', return_value={'rows': [['postgres']]}):
            browser = playwright.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            errors = []
            test_failure = [None]
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('dialog', lambda dialog: dialog.accept())
            def handle(route):
                req = route.request
                parsed = urlsplit(req.url)
                if parsed.path == '/integration-test':
                    route.fulfill(content_type='text/html', body='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/static/mcp-connections.css"><link rel="stylesheet" href="/static/integrations.css">
<style>body{font:14px system-ui;background:#111;color:#eee;margin:24px}button{padding:8px}main{max-width:1100px;margin:auto}</style>
<main id="panel"></main><script src="/static/integrations.js"></script><script>mountIntegrations(document.querySelector('main')).load()</script>''')
                elif parsed.path.startswith('/static/'):
                    path = static / Path(parsed.path).name
                    route.fulfill(content_type='text/css' if path.suffix == '.css' else 'text/javascript', body=path.read_text(encoding='utf-8'))
                elif parsed.path.endswith('/test') and test_failure[0]:
                    status, content_type, body = test_failure[0]
                    route.fulfill(status=status, content_type=content_type, body=body)
                else:
                    response = fixture.client.request(req.method, parsed.path + '?' + parsed.query, content=req.post_data,
                        headers={**req.headers, 'Cookie': 'login=yes'})
                    route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)
            page.route('http://localhost/**', handle)
            page.goto('http://localhost/integration-test')
            expect(page.get_by_text('Nenhuma integração cadastrada.')).to_be_visible()
            page.get_by_role('button', name='Conectar Supabase').click()
            expect(page.locator('[data-message]')).to_contain_text('OAuth não configurado')
            page.get_by_role('button', name='PostgreSQL avançado').click()
            for key, value in {'name': 'Supabase HML', 'host': 'db.test.supabase.co', 'username': 'reader', 'password': 'private-secret'}.items():
                page.locator(f'[name="{key}"]').fill(value)
            page.locator('[name="permission"]').select_option('full')
            page.locator('[name="project_ids"]').check()
            page.screenshot(path=str(output / 'supabase-integration-desktop.png'))
            page.set_viewport_size({'width': 390, 'height': 844})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.screenshot(path=str(output / 'supabase-integration-mobile.png'))
            page.get_by_role('button', name='Salvar integração').click()
            expect(page.get_by_role('cell', name='Supabase HML · PostgreSQL')).to_be_visible()
            page.get_by_role('button', name='Testar conexão', exact=True).click()
            expect(page.get_by_text('Conexão PostgreSQL validada.')).to_be_visible()
            for status, content_type, body, expected in [
                (502, 'text/html', '<!DOCTYPE html><h1>private-proxy-detail</h1>', 'Servidor ou proxy indisponível (HTTP 502)'),
                (200, 'text/html', '<!DOCTYPE html><h1>private-proxy-detail</h1>', 'Resposta inesperada da API (HTTP 200)'),
                (401, 'text/html', '<!DOCTYPE html>Login', 'Sessão expirada ou autenticação necessária (HTTP 401)'),
                (500, 'application/json', '{invalid', 'Resposta JSON inválida da API (HTTP 500)'),
                (502, 'application/json', '{"detail":"Falha na verificacao TLS."}', 'Falha na verificacao TLS. (HTTP 502)'),
            ]:
                test_failure[0] = (status, content_type, body)
                page.get_by_role('button', name='Testar conexão', exact=True).click()
                expect(page.locator('[data-message]')).to_contain_text(expected)
                expect(page.locator('[data-message]')).not_to_contain_text('private-proxy-detail')
            test_failure[0] = None
            page.get_by_role('button', name='Testar conexão', exact=True).click()
            expect(page.get_by_text('Conexão PostgreSQL validada.')).to_be_visible()
            config = service.list()[0]
            pending = service.execute(config['id'], 7, 'DELETE FROM public.example', 'test-connection', True)
            page.get_by_role('button', name='Atualizar integrações').click()
            expect(page.get_by_text('DELETE FROM public.example', exact=True)).to_be_visible()
            page.get_by_role('button', name='Aprovar SQL', exact=True).click()
            expect(page.get_by_text('Nenhuma solicitação pendente.')).to_be_visible()
            with service.store.connect() as db:
                self.assertEqual(db.execute('SELECT state FROM integration_approvals WHERE id=?', (pending['approval_id'],)).fetchone()[0], 'approved')
            page.get_by_role('button', name='Editar integração').click()
            expect(page.locator('[name="password"]')).to_have_value('')
            page.locator('[name="enabled"]').uncheck()
            page.get_by_role('button', name='Salvar integração').click()
            expect(page.get_by_role('cell', name='Desativada')).to_be_visible()
            page.get_by_role('button', name='Excluir integração').click()
            expect(page.get_by_text('Nenhuma integração cadastrada.')).to_be_visible()
            provider.client_id, provider.client_secret = 'test-client', 'private-client-secret'
            state = parse_qs(urlsplit(provider.start(fixture.user.id, 'session')).query)['state'][0]
            with patch.object(provider, 'exchange', return_value={'access_token': 'private-access', 'refresh_token': 'private-refresh', 'expires_at': time.time() + 3600}):
                account = provider.finish(fixture.user.id, 'session', state, 'test-code')
            with patch.object(provider, 'projects', return_value=[{'ref': 'testref', 'name': 'Supabase OAuth HML', 'status': 'ACTIVE_HEALTHY'}]):
                page.get_by_role('button', name='Atualizar integrações').click()
                page.get_by_role('button', name='Vincular projeto Supabase').click()
                expect(page.locator('[name="host"]')).not_to_be_visible()
                expect(page.locator('[name="password"]')).to_be_disabled()
                page.locator('[name="name"]').fill('OAuth HML')
                page.locator('[name="project_ref"]').select_option('testref')
                page.locator('[name="project_ids"]').check()
                page.screenshot(path=str(output / 'supabase-oauth-mobile.png'))
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.set_viewport_size({'width': 1280, 'height': 800})
                page.screenshot(path=str(output / 'supabase-oauth-desktop.png'))
                page.get_by_role('button', name='Salvar integração').click()
                expect(page.get_by_role('cell', name='OAuth HML · OAuth')).to_be_visible()
                page.get_by_role('button', name='Editar integração').click()
                page.get_by_role('button', name='Desconectar autorização').click()
                expect(page.get_by_role('cell', name='Desativada')).to_be_visible()
            self.assertEqual(provider.metadata(fixture.user.id)['accounts'], [])
            page.route('https://api.supabase.com/v1/oauth/authorize?**', lambda route: route.fulfill(content_type='text/html', body='Authorization fixture'))
            page.get_by_role('button', name='Conectar Supabase', exact=True).click()
            expect(page).to_have_url(__import__('re').compile(r'https://api\.supabase\.com/v1/oauth/authorize\?.*code_challenge='))
            self.assertEqual(errors, [])
            browser.close()
