import os
import json
import requests
import datetime

from tzlocal import get_localzone
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from .exceptions import PyKubeError


def build_session(config, gcloud_file=None):
    """
    Creates a new session for the client.
    """
    if "token" in config.user and config.user["token"]:
        s = _session_object("token")
        _set_bearer_token(s, config.user["token"])
    elif "auth-provider" in config.user:
        s = _session_object("gcp", config, gcloud_file)
    elif "client-certificate" in config.user:
        s = _session_object("client-certificate")
        s.cert = (
            config.user["client-certificate"].filename(),
            config.user["client-key"].filename(),
        )
    elif config.user.get("username") and config.user.get("password"):
        s = _session_object("basic-auth")
        s.auth = (config.user["username"], config.user["password"])
    else:  # no user present; don't configure anything
        s = _session_object()

    if "certificate-authority" in config.cluster:
        s.verify = config.cluster["certificate-authority"].filename()
    elif "insecure-skip-tls-verify" in config.cluster:
        s.verify = not config.cluster["insecure-skip-tls-verify"]
    return s


def _session_object(strategy=None, config=None, gcloud_file=None):
    if strategy in ["token", "client-certificate", "basic-auth"]:
        return requests.Session()
    elif strategy in ["gcp"]:
        return GCPSession(config, gcloud_file).create()
    else:
        return requests.Session()


def _set_bearer_token(session, token):
    """
    Set the bearer authorization token for the session.
    """
    session.headers["Authorization"] = "Bearer {}".format(token)


class GCPSession(object):

    oauth = None
    token_url = u'https://www.googleapis.com/oauth2/v4/token'
    userinfo_url = u'https://www.googleapis.com/oauth2/v1/userinfo'
    gcloud_well_known_file = os.path.join(os.path.expanduser('~'),
                                          ".config/gcloud/application_default_credentials.json")

    scope = ["https://www.googleapis.com/auth/userinfo.email",
             "https://www.googleapis.com/auth/cloud-platform",
             "https://www.googleapis.com/auth/appengine.admin",
             "https://www.googleapis.com/auth/compute",
             "https://www.googleapis.com/auth/plus.me"]

    def __init__(self, config, gcloud_file=None):
        self.config = config
        if gcloud_file:
            self.gcloud_well_known_file = gcloud_file
        self.client_id, self.client_secret, self.refresh_token = self._load_default_gcloud_credentials()
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=client, scope=self.scope)
        token = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': 'Bearer',
            'expires_in': '3600',
        }

        self.oauth.token = token

    @property
    def access_token(self):
        return self.config.user['auth-provider'].get('config', {}).get('access-token')

    @property
    def expired_token(self):
        return self.oauth.get(self.userinfo_url).status_code == 401

    def create(self):
        if not self.access_token or self.expired_token:
            # Getting access token from gcp
            self._update_token()

        return self.oauth

    def _update_token(self):
        tok = self.oauth.refresh_token(self.token_url, client_id=self.client_id,
                                       client_secret=self.client_secret,
                                       refresh_token=self.refresh_token)
        self._persist_token(tok)

    def _persist_token(self, tok):
        user_name = self.config.contexts[self.config.current_context]['user']
        user = [u['user'] for u in self.config.doc['users'] if u['name'] == user_name][0]
        if 'config' not in user['auth-provider']:
            user['auth-provider']['config'] = {}
        user['auth-provider']['config']['access-token'] = tok['access_token']
        date_expires = datetime.datetime.fromtimestamp(tok['expires_at'])
        local_tz = get_localzone()
        user['auth-provider']['config']['expiry'] = local_tz.localize(date_expires).isoformat()
        self.config.persist_doc()
        self.config.reload()

    def _load_default_gcloud_credentials(self):
        if not os.path.exists(self.gcloud_well_known_file):
            raise PyKubeError('Google cloud well known file missing, configure your gcloud session')
        with open(self.gcloud_well_known_file) as f:
            data = json.loads(f.read())
        return data['client_id'], data['client_secret'], data['refresh_token']
