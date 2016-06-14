"""
pykube.http unittests
"""
import pykube

from . import TestCase


class TestHTTPClient(TestCase):

    def ensure_no_auth(self, client):
        self.assertIsNone(client.session.cert, msg="Should not send certs when not configured")
        self.assertNotIn("Authorization", client.session.headers, msg="Should not send basic auth when not configured")

    def test_no_auth_with_empty_user(self):
        """
        Cluster does not require any authentication--so no credentials are provided in the user info
        """
        config = {
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
        client = pykube.HTTPClient(pykube.KubeConfig(doc=config))
        self.ensure_no_auth(client)

    def test_no_auth_with_no_user(self):
        config = {
            "clusters": [
                {
                    "name": "no-auth-cluster",
                    "cluster": {
                        "server": "http://localhost:8080",
                    }
                }
            ],
            "contexts": [
                {
                    "name": "no-auth-cluster",
                    "context": {
                        "cluster": "no-auth-cluster"
                    }
                }
            ],
            "current-context": "no-auth-cluster"
        }
        client = pykube.HTTPClient(pykube.KubeConfig(doc=config))
        self.ensure_no_auth(client)
