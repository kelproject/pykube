"""
pykube.http unittests
"""

import os

from pykube import http, config

from . import TestCase

class TestHTTPClient(TestCase):

    def test_no_auth(self):
        """
        Cluster does not require any authentication--so no credentials are provided in the user info
        """
        client = http.HTTPClient(config.KubeConfig(doc=self.sampleNoAuthConfig))

        self.assertIsNone(client.session.cert, msg="Should not send certs when not configured")
        self.assertNotIn("Authorization", client.session.headers, msg="Should not send basic auth when not configured")

    sampleNoAuthConfig = {
        "clusters": [
            {
                "name": "no-auth-cluster",
                "cluster": {
                    "server": "http://localhost:8080",
                }
            }
        ],
        "users": [
            {
                "name": "no-auth-cluster",
                "user": {}
            }
        ],
        "contexts": [
            {
                "name": "no-auth-cluster",
                "context": {
                    "cluster": "no-auth-cluster",
                    "user": "no-auth-cluster"
                }
            }
        ],
        "current-context": "no-auth-cluster"
    }
