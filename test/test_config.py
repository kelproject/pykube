"""
pykube.config unittests
"""

import os

from pykube import config, exceptions

from . import TestCase


GOOD_CONFIG_FILE_PATH = os.path.sep.join(["test", "test_config.yaml"])


class TestConfig(TestCase):

    def setUp(self):
        self.cfg = config.KubeConfig.from_file(GOOD_CONFIG_FILE_PATH)

    def tearDown(self):
        self.cfg = None

    def test_init(self):
        """
        Test Config instance creation.
        """
        # Ensure that a valid creation works
        self.assertEqual(
            GOOD_CONFIG_FILE_PATH,
            self.cfg.filename)

        # Ensure that if a file does not exist the creation fails
        self.assertRaises(
            exceptions.PyKubeError,
            config.KubeConfig.from_file,
            "doesnotexist")

    def test_set_current_context(self):
        """
        Verify set_current_context works as expected.
        """
        self.cfg.set_current_context("new_context")
        self.assertEqual(
            "new_context",
            self.cfg.current_context)

    def test_clusters(self):
        """
        Verify clusters works as expected.
        """
        self.assertEqual(
            {"server": "http://localhost"},
            self.cfg.clusters.get("thecluster", None))

    def test_users(self):
        """
        Verify users works as expected.
        """
        self.assertEqual(
            "data",
            self.cfg.users.get("admin", None))

    def test_contexts(self):
        """
        Verify contexts works as expected.
        """
        self.assertEqual(
            {"cluster": "thecluster", "user": "admin"},
            self.cfg.contexts.get("thename", None))

    def test_cluster(self):
        """
        Verify cluster works as expected.
        """
        # Without a current_context this should fail
        try:
            cluster = self.cfg.cluster
            self.fail(
                "cluster was found without a current context set: {}".format(
                    cluster))
        except exceptions.PyKubeError:
            # We should get an error
            pass

        self.cfg.set_current_context("thename")
        self.assertEqual({"server": "http://localhost"}, self.cfg.cluster)

    def test_user(self):
        """
        Verify user works as expected.
        """
        # Without a current_context this should fail
        try:
            user = self.cfg.user
            self.fail(
                "user was found without a current context set: {}".format(
                    user))
        except exceptions.PyKubeError:
            # We should get an error
            pass

        self.cfg.set_current_context("thename")
        self.assertEqual("data", self.cfg.user)
