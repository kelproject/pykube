"""
HTTP request related code.
"""

import datetime
import json
import posixpath
import re
import shlex
import subprocess

try:
    import google.auth
    from google.auth.transport.requests import Request as GoogleAuthRequest
    google_auth_installed = True
except ImportError:
    google_auth_installed = False

import requests.adapters

from six.moves import http_client
from six.moves.urllib.parse import urlparse

from .exceptions import HTTPError
from .utils import jsonpath_installed, jsonpath_parse


_ipv4_re = re.compile(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")


class KubernetesHTTPAdapterSendMixin(object):

    def _persist_credentials(self, config, token, expiry):
        user_name = config.contexts[config.current_context]["user"]
        user = [u["user"] for u in config.doc["users"] if u["name"] == user_name][0]
        auth_config = user["auth-provider"].setdefault("config", {})
        auth_config["access-token"] = token
        auth_config["expiry"] = expiry
        config.persist_doc()
        config.reload()

    def _auth_gcp(self, request, token, expiry, config):
        original_request = request.copy()

        credentials = google.auth.default()[0]
        credentials.token = token
        credentials.expiry = expiry

        should_persist = not credentials.valid

        auth_request = GoogleAuthRequest()
        credentials.before_request(auth_request, request.method, request.url, request.headers)

        if should_persist and config:
            self._persist_credentials(config, credentials.token, credentials.expiry)

        def retry(send_kwargs):
            credentials.refresh(auth_request)
            response = self.send(original_request, **send_kwargs)
            if response.ok and config:
                self._persist_credentials(config, credentials.token, credentials.expiry)
            return response

        return retry

    def send(self, request, **kwargs):
        if "kube_config" in kwargs:
            config = kwargs.pop("kube_config")
        else:
            config = self.kube_config

        _retry_attempt = kwargs.pop("_retry_attempt", 0)
        retry_func = None

        # setup cluster API authentication

        if "token" in config.user and config.user["token"]:
            request.headers["Authorization"] = "Bearer {}".format(config.user["token"])
        elif "auth-provider" in config.user:
            auth_provider = config.user["auth-provider"]
            if auth_provider.get("name") == "gcp":
                dependencies = [
                    google_auth_installed,
                    jsonpath_installed,
                ]
                if not all(dependencies):
                    raise ImportError("missing dependencies for GCP support (try pip install pykube[gcp]")
                auth_config = auth_provider.get("config", {})
                if "cmd-path" in auth_config:
                    output = subprocess.check_output(
                        [auth_config["cmd-path"]] + shlex.split(auth_config["cmd-args"])
                    )
                    parsed = json.loads(output)
                    token = jsonpath_parse(auth_config["token-key"], parsed)
                    expiry = datetime.datetime.strptime(
                        jsonpath_parse(auth_config["expiry-key"], parsed),
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    retry_func = self._auth_gcp(request, token, expiry, None)
                else:
                    retry_func = self._auth_gcp(
                        request,
                        auth_config.get("access-token"),
                        auth_config.get("expiry"),
                        config,
                    )
            # @@@ support oidc
        elif "client-certificate" in config.user:
            kwargs["cert"] = (
                config.user["client-certificate"].filename(),
                config.user["client-key"].filename(),
            )
        elif config.user.get("username") and config.user.get("password"):
            request.prepare_auth((config.user["username"], config.user["password"]))

        # setup certificate verification

        if "certificate-authority" in config.cluster:
            kwargs["verify"] = config.cluster["certificate-authority"].filename()
        elif "insecure-skip-tls-verify" in config.cluster:
            kwargs["verify"] = not config.cluster["insecure-skip-tls-verify"]

        send = super(KubernetesHTTPAdapterSendMixin, self).send
        response = send(request, **kwargs)

        _retry_status_codes = {http_client.UNAUTHORIZED}

        if response.status_code in _retry_status_codes and retry_func and _retry_attempt < 2:
            send_kwargs = {
                "_retry_attempt": _retry_attempt + 1,
                "kube_config": config,
            }
            send_kwargs.update(kwargs)
            return retry_func(send_kwargs=send_kwargs)

        return response


class KubernetesHTTPAdapter(KubernetesHTTPAdapterSendMixin, requests.adapters.HTTPAdapter):

    def __init__(self, kube_config, **kwargs):
        self.kube_config = kube_config
        super(KubernetesHTTPAdapter, self).__init__(**kwargs)


class HTTPClient(object):
    """
    Client for interfacing with the Kubernetes API.
    """

    _session = None

    def __init__(self, config):
        """
        Creates a new instance of the HTTPClient.

        :Parameters:
           - `config`: The configuration instance
        """
        self.config = config
        self.url = self.config.cluster["server"]

        session = requests.Session()
        session.mount("https://", KubernetesHTTPAdapter(self.config))
        session.mount("http://", KubernetesHTTPAdapter(self.config))
        self.session = session

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        pr = urlparse(value)
        self._url = pr.geturl()

    @property
    def version(self):
        """
        Get Kubernetes API version
        """
        response = self.get(version="", base="/version")
        response.raise_for_status()
        data = response.json()
        return (data["major"], data["minor"])

    def resource_list(self, api_version):
        cached_attr = "_cached_resource_list"
        if not hasattr(self, cached_attr):
            r = self.get(version=api_version)
            r.raise_for_status()
            setattr(self, cached_attr, r.json())
        return getattr(self, cached_attr)

    def get_kwargs(self, **kwargs):
        """
        Creates a full URL to request based on arguments.

        :Parametes:
           - `kwargs`: All keyword arguments to build a kubernetes API endpoint
        """
        version = kwargs.pop("version", "v1")
        if version == "v1":
            base = kwargs.pop("base", "/api")
        elif "/" in version:
            base = kwargs.pop("base", "/apis")
        else:
            if "base" not in kwargs:
                raise TypeError("unknown API version; base kwarg must be specified.")
            base = kwargs.pop("base")
        bits = [base, version]
        # Overwrite (default) namespace from context if it was set
        if "namespace" in kwargs:
            n = kwargs.pop("namespace")
            if n is not None:
                if n:
                    namespace = n
                else:
                    namespace = self.config.namespace
                if namespace:
                    bits.extend([
                        "namespaces",
                        namespace,
                    ])
        url = kwargs.get("url", "")
        if url.startswith("/"):
            url = url[1:]
        bits.append(url)
        kwargs["url"] = self.url + posixpath.join(*bits)
        return kwargs

    def raise_for_status(self, resp):
        try:
            resp.raise_for_status()
        except Exception:
            # attempt to provide a more specific exception based around what
            # Kubernetes returned as the error.
            if resp.headers["content-type"] == "application/json":
                payload = resp.json()
                if payload["kind"] == "Status":
                    raise HTTPError(resp.status_code, payload["message"])
            raise

    def request(self, *args, **kwargs):
        """
        Makes an API request based on arguments.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.request(*args, **self.get_kwargs(**kwargs))

    def get(self, *args, **kwargs):
        """
        Executes an HTTP GET.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.get(*args, **self.get_kwargs(**kwargs))

    def options(self, *args, **kwargs):
        """
        Executes an HTTP OPTIONS.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.options(*args, **self.get_kwargs(**kwargs))

    def head(self, *args, **kwargs):
        """
        Executes an HTTP HEAD.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.head(*args, **self.get_kwargs(**kwargs))

    def post(self, *args, **kwargs):
        """
        Executes an HTTP POST.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.post(*args, **self.get_kwargs(**kwargs))

    def put(self, *args, **kwargs):
        """
        Executes an HTTP PUT.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.put(*args, **self.get_kwargs(**kwargs))

    def patch(self, *args, **kwargs):
        """
        Executes an HTTP PATCH.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.patch(*args, **self.get_kwargs(**kwargs))

    def delete(self, *args, **kwargs):
        """
        Executes an HTTP DELETE.

        :Parameters:
           - `args`: Non-keyword arguments
           - `kwargs`: Keyword arguments
        """
        return self.session.delete(*args, **self.get_kwargs(**kwargs))
