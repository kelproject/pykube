"""
HTTP request related code.
"""

import posixpath
import re
import sys

import requests

from six.moves.urllib.parse import urlparse

from .exceptions import PyKubeError, HTTPError


_ipv4_re = re.compile(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")


class HTTPClient(object):
    """
    Client for interfacing with the Kubernetes API.
    """

    def __init__(self, config):
        """
        Creates a new instance of the HTTPClient.

        :Parameters:
           - `config`: The configuration instance
        """
        self.config = config
        self.url = self.config.cluster["server"]
        self.session = self.build_session()

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        pr = urlparse(value)
        if sys.version_info < (3, 5) and ("::" in pr.hostname or _ipv4_re.match(pr.hostname)):
            raise PyKubeError("IP address hostnames are not supported with Python < 3.5. Please see https://github.com/kelproject/pykube/issues/29 for more info.")
        self._url = pr.geturl()

    def build_session(self):
        """
        Creates a new session for the client.
        """
        s = requests.Session()
        if "certificate-authority" in self.config.cluster:
            s.verify = self.config.cluster["certificate-authority"].filename()
        if "token" in self.config.user and self.config.user["token"]:
            s.headers["Authorization"] = "Bearer {}".format(self.config.user["token"])
        else:
            s.cert = (
                self.config.user["client-certificate"].filename(),
                self.config.user["client-key"].filename(),
            )
        return s

    def get_kwargs(self, **kwargs):
        """
        Creates a full URL to request based on arguments.

        :Parametes:
           - `kwargs`: All keyword arguments to build a kubernetes API endpoint
        """
        version = kwargs.pop("version", "v1")
        if version == "v1":
            base = kwargs.pop("base", "/api")
        elif any(map(version.startswith, ["extensions/", "batch/"])):
            base = kwargs.pop("base", "/apis")
        else:
            if "base" not in kwargs:
                raise TypeError("unknown API version; base kwarg must be specified.")
            base = kwargs.pop("base")
        bits = [base, version]
        if "namespace" in kwargs:
            bits.extend([
                "namespaces",
                kwargs.pop("namespace"),
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
                    raise HTTPError(payload["message"])
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
