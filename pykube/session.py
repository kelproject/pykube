import os
import json
import requests
import datetime
import time

from tzlocal import get_localzone
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from oauth2client.service_account import ServiceAccountCredentials

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
    """
    Creates a session for Google Cloud Platform
    """

    oauth = None
    token_url = u'https://www.googleapis.com/oauth2/v4/token'
    tokeninfo_url = u"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}"
    gcloud_credentials_file = os.path.join(os.path.expanduser('~'),
                                           ".config/gcloud/application_default_credentials.json")

    scope = [
        "https://www.googleapis.com/auth/cloud-platform",
    ]

    def __init__(self, config, gcloud_file=None):
        """
        Initialize the parameters for this session using OAuth2

        :Parameters:
           - `config`: The configuration instance
           - `gcloud_file`: Override gcloud credentials file location
        """
        self.config = config
        if gcloud_file:
            self.gcloud_credentials_file = gcloud_file
        self.credentials = self._load_default_gcloud_credentials()

        client = BackendApplicationClient(client_id=self.credentials.get('client_id'))
        self.oauth = OAuth2Session(client=client, scope=self.scope)
        token = {
            'access_token': self.access_token,
            'refresh_token': self.credentials.get('refresh_token'),
            'token_type': 'Bearer',
            'expires_in': '3600',
        }

        self.oauth.token = token

    @property
    def access_token(self):
        auth = self.config.user['auth-provider'].get('config')
        # The config key might be there with None value
        if not auth:
            return None
        return auth.get('access-token')

    @property
    def expired_token(self):
        token_info = self.oauth.get(self.tokeninfo_url.format(self.access_token)).text
        token_js = json.loads(token_info)
        return 'error' in token_js

    def create(self):
        """
        Creates a requests oauth2 object
        """
        if not self.access_token or self.expired_token:
            # Getting access token from gcp
            self._update_token()

        return self.oauth

    def _update_token(self):
        """
        If the OAuth2 access token is missing or expired, this retrieves a new one
        """
        if self.credentials.get("type") == "authorized_user":
            tok = self.oauth.refresh_token(self.token_url, client_id=self.credentials.get('client_id'),
                                           client_secret=self.credentials.get('client_secret'),
                                           refresh_token=self.credentials.get('refresh_token'))
        elif self.credentials.get("type") == "service_account":
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.gcloud_credentials_file,
                                                                           scopes=self.scope)
            new_token = credentials.get_access_token()

            tok = {
                'access_token': new_token.access_token,
                'token_type': 'Bearer',
                'expires_at': time.time() + new_token.expires_in,
            }
            self.oauth.token = tok
        else:
            raise PyKubeError("Missing type in credentials file")

        self._persist_token(tok)

    def _persist_token(self, tok):
        user_name = self.config.contexts[self.config.current_context]['user']
        user = [u['user'] for u in self.config.doc['users'] if u['name'] == user_name][0]
        if 'config' not in user['auth-provider']:
            user['auth-provider']['config'] = {}
        if not user['auth-provider']['config']:
            user['auth-provider']['config'] = {}
        user['auth-provider']['config']['access-token'] = tok['access_token']
        date_expires = datetime.datetime.fromtimestamp(tok['expires_at'])
        local_tz = get_localzone()
        user['auth-provider']['config']['expiry'] = local_tz.localize(date_expires).isoformat()
        self.config.persist_doc()
        self.config.reload()

    def _load_default_gcloud_credentials(self):
        # Checking if GOOGLE_APPLICATION_CREDENTIALS overrides gclod cred file
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            self.gcloud_credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if not os.path.exists(self.gcloud_credentials_file):
            raise PyKubeError('Google cloud well known file missing, configure your gcloud session')
        with open(self.gcloud_credentials_file) as f:
            data = json.loads(f.read())
        return data
