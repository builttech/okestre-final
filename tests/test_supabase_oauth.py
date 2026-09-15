import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import MagicMock, patch

from gitide_server.mcp_oauth import OAuthStore
from gitide_server.integrations import Integrations
from gitide_server.supabase_oauth import SupabaseOAuth, SupabaseOAuthError, routes


class SupabaseOAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = OAuthStore(Path(self.temp.name) / 'oauth.db', 'local-secret')
        self.provider = SupabaseOAuth(self.store, 'http://localhost', 'client-id', 'client-secret')
        self.tokens = {'access_token': 'private-access', 'refresh_token': 'private-refresh', 'expires_at': time.time() + 3600}
        self.service = Integrations(self.store, supabase=self.provider)

    def authorize(self):
        query = parse_qs(urlsplit(self.provider.start(1, 'session')).query)
        self.assertEqual(query['code_challenge_method'], ['S256'])
        self.assertNotIn('private', str(query))
        with patch.object(self.provider, 'exchange', return_value=dict(self.tokens)):
            account = self.provider.finish(1, 'session', query['state'][0], 'code')
        return account, query['state'][0]

    def test_state_binding_replay_and_encryption(self):
        state = parse_qs(urlsplit(self.provider.start(1, 'session')).query)['state'][0]
        with patch.object(self.provider, 'exchange', return_value=dict(self.tokens)) as exchange:
            for owner, binding in [(2, 'session'), (1, 'other')]:
                with self.assertRaises(SupabaseOAuthError):
                    self.provider.finish(owner, binding, state, 'code')
            exchange.assert_not_called()
            account = self.provider.finish(1, 'session', state, 'code')
            with self.assertRaises(SupabaseOAuthError):
                self.provider.finish(1, 'session', state, 'code')
        self.assertEqual(self.provider.token(account), 'private-access')
        with self.store.connect() as db:
            encrypted = db.execute('SELECT data FROM supabase_accounts').fetchone()[0]
            self.assertNotIn(b'private-access', encrypted)
        self.assertNotIn('private-access', str(self.provider.metadata(1)))
        self.assertEqual(self.provider.metadata(2)['accounts'], [])

    def test_cancel_and_missing_config(self):
        with self.assertRaises(SupabaseOAuthError):
            SupabaseOAuth(self.store, 'http://localhost').start(1, 'session')
        state = parse_qs(urlsplit(self.provider.start(1, 'session')).query)['state'][0]
        with self.assertRaises(SupabaseOAuthError):
            self.provider.finish(1, 'session', state, '', denied=True)
        self.assertEqual(self.provider.metadata(1)['accounts'], [])

    def test_refresh_and_disconnect(self):
        account, _ = self.authorize()
        with self.store.connect() as db:
            data = dict(self.tokens, expires_at=0, connected_at=0)
            db.execute('UPDATE supabase_accounts SET data=? WHERE id=?', (self.provider.encode(data), account))
        with patch.object(self.provider, 'exchange', return_value=dict(self.tokens, access_token='rotated')) as exchange:
            self.assertEqual(self.provider.token(account), 'rotated')
            self.assertEqual(self.provider.token(account), 'rotated')
            exchange.assert_called_once_with({'grant_type': 'refresh_token', 'refresh_token': 'private-refresh'})
        values = dict(name='Test', account_id=account, project_ref='testref', permission='read', project_ids=[1], enabled=True, require_approval=True)
        integration = self.service.save_oauth(values, {1})
        self.service.disconnect_supabase(account, 1)
        self.assertFalse(self.service.get(integration['id'])['enabled'])
        with self.assertRaises(SupabaseOAuthError):
            self.provider.token(account)

    def test_projects_and_readonly_query(self):
        account, _ = self.authorize()
        with patch.object(self.provider, 'http', return_value=[{'id': 'testref', 'name': 'HML'}]) as http:
            self.assertEqual(self.provider.projects(account, 1)[0]['ref'], 'testref')
            with self.assertRaises(SupabaseOAuthError):
                self.provider.projects(account, 2)
        with patch.object(self.provider, 'http', return_value=[{'value': 1}]) as http:
            result = self.provider.query({'account_id': account, 'project_ref': 'testref'}, 'SELECT 1', 'read')
            self.assertEqual(result['rows'], [['1']])
            self.assertEqual(http.call_args.kwargs['json'], {'query': 'SELECT 1', 'read_only': True})
        with patch.object(self.provider, 'http', return_value=[]) as http:
            self.provider.query({'account_id': account, 'project_ref': 'testref'}, 'CREATE TABLE public.example(id int)', 'full')
            sql = http.call_args.kwargs['json']['query']
            self.assertIn('ENABLE ROW LEVEL SECURITY; COMMIT;', sql)
            self.assertFalse(http.call_args.kwargs['json']['read_only'])

    def test_http_error_redaction_no_redirects_or_retry(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = 502
        response.iter_content.return_value = [b'<html>private-secret</html>']
        request = MagicMock(return_value=response)
        provider = SupabaseOAuth(self.store, 'http://localhost', request=request)
        with self.assertRaises(SupabaseOAuthError) as error:
            provider.http('POST', '/v1/oauth/token')
        self.assertNotIn('private-secret', str(error.exception))
        request.assert_called_once()
        self.assertFalse(request.call_args.kwargs['allow_redirects'])

    def test_routes_auth_csrf_callback_and_project_binding(self):
        import test_mcp_oauth
        fixture = test_mcp_oauth.OAuthTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.provider.list_projects = lambda: [{'id': 1, 'name': 'Local'}]
        fixture.client.app.router.routes.extend(routes(self.provider, self.service, fixture.provider))
        base = '/api/integrations/supabase/'
        self.assertEqual(fixture.client.post(base + 'start').status_code, 401)
        fixture.client.cookies.set('login', 'yes')
        self.assertEqual(fixture.client.post(base + 'start').status_code, 403)
        # Match the current root session's CSRF binding without exposing it to the provider.
        from starlette.requests import Request
        binding = fixture.provider.management_csrf(Request({'type': 'http', 'headers': []}), fixture.user)
        headers = {'X-CSRF-Token': binding}
        started = fixture.client.post(base + 'start', headers=headers).json()
        state = parse_qs(urlsplit(started['authorize_url']).query)['state'][0]
        with patch.object(self.provider, 'exchange', return_value=dict(self.tokens)):
            response = fixture.client.get(base + 'callback', params={'state': state, 'code': 'code'}, follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        account = self.provider.metadata(fixture.user.id)['accounts'][0]['id']
        values = dict(name='Test', account_id=account, project_ref='testref', permission='read', project_ids=[1])
        with patch.object(self.provider, 'projects', return_value=[{'ref': 'testref'}]):
            self.assertEqual(fixture.client.post(base + 'bind', headers=headers, json=dict(values, project_ref='forbidden')).status_code, 400)
            self.assertEqual(fixture.client.post(base + 'bind', headers=headers, json=values).status_code, 200)
        self.assertNotIn('private-access', fixture.client.get(base + 'projects', params={'account_id': 'invalid'}).text)


if __name__ == '__main__':
    unittest.main()
