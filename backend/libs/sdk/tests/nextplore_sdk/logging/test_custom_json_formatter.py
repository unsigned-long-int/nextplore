import json
import logging
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import nextplore_sdk.logging.custom_json_formatter as mod


class TestCustomJsonFormatter(unittest.TestCase):
    def setUp(self):
        self.fixed_now = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

        self.p_datetime = patch.object(mod, 'datetime')
        self.mock_datetime = self.p_datetime.start()
        self.mock_datetime.now.return_value = self.fixed_now

        self.formatter = mod.CustomJsonFormatter(fmt='%(asctime)s %(levelname)s %(message)s')

        self.addCleanup(self.p_datetime.stop)

    def _format_record(self, level=logging.INFO, msg='hello', name='test.logger'):
        record = logging.LogRecord(
            name=name,
            level=level,
            pathname=__file__,
            lineno=123,
            msg=msg,
            args=None,
            exc_info=None,
        )
        json_str = self.formatter.format(record)
        return json.loads(json_str)

    def test_includes_env_and_message(self):
        data = self._format_record(msg='hi there')
        self.assertIn('env', data)
        self.assertEqual(data['env'], 'dev')
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'hi there')

    def test_field_renames_levelname_and_asctime(self):
        data = self._format_record(level=logging.WARNING, msg='watch out')
        self.assertIn('level', data)
        self.assertEqual(data['level'], 'WARNING')
        self.assertNotIn('levelname', data)

        self.assertIn('timestamp', data)
        self.assertNotIn('asctime', data)

    def test_job_run_timestamp_is_frozen_at_construction(self):
        d1 = self._format_record(msg='first')
        with patch.object(mod, 'datetime') as mock_dt2:
            mock_dt2.now.return_value = datetime(2030, 1, 1, tzinfo=timezone.utc)
            d2 = self._format_record(msg='second')

        self.assertIn('job_run_timestamp', d1)
        self.assertIn('job_run_timestamp', d2)
        self.assertEqual(d1['job_run_timestamp'], self.fixed_now.isoformat())
        self.assertEqual(d2['job_run_timestamp'], self.fixed_now.isoformat())

    def test_service_meta_injected(self):
        self.formatter.service_meta = {
            'service': 'billing',
            'version': '1.2.3',
            'region': 'eu-central-1',
        }
        data = self._format_record(msg='meta test')
        self.assertEqual(data['service'], 'billing')
        self.assertEqual(data['version'], '1.2.3')
        self.assertEqual(data['region'], 'eu-central-1')
