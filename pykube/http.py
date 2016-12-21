"""
HTTP request related code.
"""

import posixpath
import re

from six.moves.urllib.parse import urlparse

from .session import build_session
from .exceptions import HTTPError


_ipv4_re = re.compile(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")


class HTTPClient(object):
    """
    Client for interfacing with the Kubernetes API.
    """

    _session = None

    def __init__(self, config, gcloud_file=None):
        """
        Creates a new instance of the HTTPClient.

        :Parameters:
           - `config`: The configuration instance
           - `gcloud_file`: For GCP deployments, override gcloud credentials file location
        """
        self.config = config
        self.gcloud_file = gcloud_file
        self.url = self.config.cluster["server"]

    @property
    def session(self):
        if not self._session:
            self._session = build_session(self.config, self.gcloud_file)
        return self._session

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
        response = self.get('/version')
        data = response.json()
        return (data['major'], data['minor'])

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
