"""
pykube.http unittests
"""

import os

from pykube.http import HTTPClient
from pykube.config import KubeConfig

from . import TestCase

GOOD_CONFIG_FILE_PATH = os.path.sep.join(["test", "test_config_with_context.yaml"])


class TestHttp(TestCase):

    def setUp(self):
        self.cfg = KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)

    def tearDown(self):
        self.cfg = None

    def test_build_session_basic(self):
        """
        """
        session = HTTPClient(self.cfg).session
        self.assertEqual(session.auth, ('adm', 'somepassword'))
