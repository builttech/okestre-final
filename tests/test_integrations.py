import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from gitide_server.integrations import Integrations, sql_level
from gitide_server.mcp_oauth import OAuthStore


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = OAuthStore(Path(self.temp.name) / 'test.db', 'test-secret')
        self.service = Integrations(self.store)
        self.values = dict(name='Test', host='db.test.supabase.co', username='postgres', password='secret-db', project_ids=[1], permission='full')
        self.config = self.service.save(self.values, {1})

    def test_encryption_validation_and_update(self):
        with self.store.connect() as db:
            self.assertNotIn(b'secret-db', db.execute('SELECT data FROM integrations').fetchone()[0])
        self.assertNotIn('password', self.service.list()[0])
        self.service.save(dict(self.values, password=''), {1}, self.config['id'])
        self.assertEqual(self.service.get(self.config['id'])['password'], 'secret-db')
        for host in ('127.0.0.1', 'db.test.supabase.co.evil.com', 'localhost', 'x.supabase.co'):
            with self.assertRaises(ValueError):
                self.service.save(dict(self.values, host=host), {1})
        with self.assertRaises(ValueError):
            self.service.save(self.values, {2})

    def test_parser(self):
        self.assertEqual(sql_level('SELECT 1'), 'read')
        self.assertEqual(sql_level('WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x'), 'write')
        self.assertEqual(sql_level('SELECT public.dangerous()'), 'full')
        self.assertEqual(sql_level('CREATE TABLE t(id int)'), 'full')
        self.assertEqual(sql_level('SELECT * INTO t2 FROM t'), 'full')
        for sql in ('SELECT 1; DELETE FROM t', 'BEGIN', 'SET ROLE postgres', "COPY t TO PROGRAM 'x'", ''):
            with self.assertRaises(ValueError):
                sql_level(sql)

    def test_approval_binding_single_use_and_revision(self):
        args = (self.config['id'], 1, 'DELETE FROM public.t', 'connection-a', True)
        with patch.object(self.service, 'query', return_value={'rows': []}) as query:
            pending = self.service.execute(*args)
            identifier = pending['approval_id']
            self.service.decide(identifier, True)
            with self.assertRaises(ValueError):
                self.service.execute(*args[:3], 'connection-b', True, identifier)
            self.assertEqual(self.service.execute(*args, identifier)['status'], 'completed')
            self.assertEqual(self.service.execute(*args, identifier)['status'], 'executed')
            query.assert_called_once()
            pending = self.service.execute(*args)
            self.service.decide(pending['approval_id'], True)
            self.service.save(self.values, {1}, self.config['id'])
            with self.assertRaises(ValueError):
                self.service.execute(*args, pending['approval_id'])

    def test_permission_intersection(self):
        for permission, sql in [('read', 'DELETE FROM t'), ('write', 'DROP TABLE t'), ('write', 'SELECT public.f()')]:
            self.service.save(dict(self.values, permission=permission), {1}, self.config['id'])
            with self.assertRaises(PermissionError):
                self.service.execute(self.config['id'], 1, sql, 'a', True)
        self.service.save(dict(self.values, enabled=False), {1}, self.config['id'])
        with self.assertRaises(PermissionError):
            self.service.execute(self.config['id'], 1, 'SELECT 1', 'a', True)

    def test_management_authentication_and_csrf(self):
        import test_mcp_oauth
        from gitide_server.integration_routes import routes
        fixture = test_mcp_oauth.OAuthTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.client.app.router.routes.extend(routes(fixture.provider, self.service))
        self.assertEqual(fixture.client.get('/api/integrations').status_code, 401)
        fixture.client.cookies.set('login', 'yes')
        response = fixture.client.get('/api/integrations')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('secret-db', response.text)
        self.assertEqual(fixture.client.delete('/api/integrations/' + self.config['id']).status_code, 403)
        fixture.user.role = 'member'
        self.assertEqual(fixture.client.get('/api/integrations').status_code, 403)

    def test_driver_readonly_limits_and_redaction(self):
        from unittest.mock import MagicMock
        from types import SimpleNamespace
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.description = [SimpleNamespace(name='value')]
        cursor.fetchmany.return_value = [('value',)] * 201
        service = Integrations(self.store, connect=MagicMock(return_value=conn))
        result = service.query(service.get(self.config['id']), 'SELECT 1', 'read')
        self.assertEqual(len(result['rows']), 200)
        self.assertTrue(result['truncated'])
        conn.set_session.assert_called_once_with(readonly=True, autocommit=False)
        self.assertEqual(service.connect.call_args.kwargs['sslmode'], 'verify-full')
        conn.commit.assert_called_once()
        conn.close.assert_called_once()
        service.connect.side_effect = RuntimeError('secret-db')
        with self.assertRaises(ValueError) as error:
            service.test(self.config['id'])
        self.assertNotIn('secret-db', str(error.exception))


if __name__ == '__main__':
    unittest.main()
