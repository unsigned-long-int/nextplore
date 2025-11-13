import unittest
import logging
from pathlib import Path
from unittest.mock import patch

import nextplore_sdk.logging.setup as mod


class TestSetupLogger(unittest.TestCase):
    def setUp(self):
        self._orig_handlers = list(logging.root.handlers)
        logging.root.handlers = []

        self.p_fileconfig = patch.object(mod.logging.config, 'fileConfig')
        self.mock_fileconfig = self.p_fileconfig.start()
        self.addCleanup(self.p_fileconfig.stop)

    def tearDown(self):
        logging.root.handlers = self._orig_handlers

    def test_updates_only_custom_json_formatter_handlers(self):
        custom_fmt = mod.CustomJsonFormatter()
        other_fmt = logging.Formatter('%(message)s')

        h1 = logging.StreamHandler()
        h1.formatter = custom_fmt

        h2 = logging.StreamHandler()
        h2.formatter = other_fmt

        logging.root.handlers = [h1, h2]

        service_meta = {'service': 'orders', 'version': '2.0.0'}
        cfg_path = Path('/tmp/logging.ini')

        mod.setup_logger(service_meta, cfg_path)

        self.mock_fileconfig.assert_called_once_with(cfg_path, disable_existing_loggers=False)

        self.assertIn('service', h1.formatter.service_meta)
        self.assertIn('version', h1.formatter.service_meta)
        self.assertEqual(h1.formatter.service_meta['service'], 'orders')
        self.assertEqual(h1.formatter.service_meta['version'], '2.0.0')

        self.assertFalse(hasattr(h2.formatter, 'service_meta'))

    def test_handler_without_formatter_attribute_is_ignored(self):
        class NoFormatterHandler(logging.Handler):
            def emit(self, record):
                pass

        h = NoFormatterHandler()
        custom_handler = logging.StreamHandler()
        custom_handler.formatter = mod.CustomJsonFormatter()

        logging.root.handlers = [h, custom_handler]

        service_meta = {'region': 'eu-central-1'}
        mod.setup_logger(service_meta, Path('/tmp/logging.ini'))

        self.assertEqual(custom_handler.formatter.service_meta.get('region'), 'eu-central-1')

    def test_no_handlers_does_not_crash(self):
        logging.root.handlers = []
        mod.setup_logger({'x': 'y'}, Path('/tmp/logging.ini'))
        self.mock_fileconfig.assert_called_once()
