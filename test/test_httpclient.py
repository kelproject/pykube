"""
pykube.http unittests
"""
import copy
import logging

import pykube

from . import TestCase

BASE_CONFIG = {
    "clusters": [
        {
            "name": "test-cluster",
            "cluster": {
                "server": "http://localhost:8080",
            }
        }
    ],
    "contexts": [
        {
            "name": "test-cluster",
            "context": {
                "cluster": "test-cluster",
                "user": "test-user",
            }
        }
    ],
    "users": [
        {
            'name': 'test-user',
            'user': {},
        }
    ],
    "current-context": "test-cluster",
}

_log = logging.getLogger(__name__)


class TestHTTPClient(TestCase):
    def setUp(self):
        self.config = copy.deepcopy(BASE_CONFIG)

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

    def test_build_session_bearer_token(self):
        """Test that HTTPClient correctly parses the token
        """
        self.config.update({
            'users': [
                {
                    'name': 'test-user',
                    'user': {
                        'token': 'test'
                    },
                },
            ]
        })
        _log.info('Built config: %s', self.config)

        client = pykube.HTTPClient(pykube.KubeConfig(doc=self.config))
        _log.debug('Checking headers %s', client.session.headers)
        self.assertIn('Authorization', client.session.headers)
        self.assertEqual(client.session.headers['Authorization'], 'Bearer test')
