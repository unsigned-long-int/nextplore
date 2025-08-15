import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, ANY
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text as sa_text

from api.router.test_integration_router import test_integration


class TestTestIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.payload = SimpleNamespace(
            service_type='postgres',
            auth_method='password',
            host='db.local',
            port=5432,
            database_name='analytics',
            username='alice',
            password='secret',
            kerberos_principal=None,
            windows_domain=None,
            extra_options={'sslmode': 'require'},
        )

    @patch('api.router.test_integration_router.fetch_engine')
    @patch('api.router.test_integration_router.build_connection_string')
    async def test_success_happy_path(self, mock_build_conn_str, mock_fetch_engine):
        mock_build_conn_str.return_value = 'postgresql://...'
        engine = MagicMock()
        ctx = MagicMock()
        conn = MagicMock()
        ctx.__enter__.return_value = conn
        ctx.__exit__ = MagicMock(return_value=None)
        engine.connect.return_value = ctx
        mock_fetch_engine.return_value = engine

        result = await test_integration(self.payload)
        self.assertIsNone(result)

        mock_build_conn_str.assert_called_once()
        mock_fetch_engine.assert_called_once_with('postgresql://...', connect_args={'connect_timeout': 5})
        engine.connect.assert_called_once()
        conn.execute.assert_called_once_with(ANY) 

        called_arg = conn.execute.call_args[0][0]
        self.assertEqual(str(called_arg), str(sa_text('SELECT 1')))

    @patch('api.router.test_integration_router.fetch_engine')
    @patch('api.router.test_integration_router.build_connection_string')
    async def test_sqlalchemy_error_raises_424(self, mock_build_conn_str, mock_fetch_engine):
        mock_build_conn_str.return_value = 'postgresql://...'
        engine = MagicMock()
        ctx = MagicMock()
        conn = MagicMock()
        conn.execute.side_effect = SQLAlchemyError('boom')
        ctx.__enter__.return_value = conn
        ctx.__exit__ = MagicMock(return_value=None)
        engine.connect.return_value = ctx
        mock_fetch_engine.return_value = engine

        with self.assertRaises(HTTPException) as ctx_exc:
            await test_integration(self.payload)

        exc = ctx_exc.exception
        self.assertEqual(exc.status_code, 424)
        self.assertEqual(exc.detail, {'message': 'Database error: boom'})

    @patch('api.router.test_integration_router.fetch_engine')
    @patch('api.router.test_integration_router.build_connection_string')
    async def test_unexpected_error_raises_500(self, mock_build_conn_str, mock_fetch_engine):
        mock_build_conn_str.side_effect = RuntimeError('oops')

        with self.assertRaises(HTTPException) as ctx_exc:
            await test_integration(self.payload)

        exc = ctx_exc.exception
        self.assertEqual(exc.status_code, 500)
        self.assertEqual(exc.detail, {'message': 'Unexpected error: oops'})

        mock_fetch_engine.assert_not_called()
