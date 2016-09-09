"""
Configuration code.
"""

import base64
import copy
import tempfile
import os

import yaml

from pykube import exceptions


class KubeConfig(object):
    """
    Main configuration class.
    """

    @classmethod
    def from_service_account(cls, path="/var/run/secrets/kubernetes.io/serviceaccount"):
        with open(os.path.join(path, "token")) as fp:
            token = fp.read()
        host = os.environ.get("PYKUBE_KUBERNETES_SERVICE_HOST")
        if host is None:
            host = os.environ["KUBERNETES_SERVICE_HOST"]
        port = os.environ.get("PYKUBE_KUBERNETES_SERVICE_PORT")
        if port is None:
            port = os.environ["KUBERNETES_SERVICE_PORT"]
        doc = {
            "clusters": [
                {
                    "name": "self",
                    "cluster": {
                        "server": "https://{}:{}".format(host, port),
                        "certificate-authority": os.path.join(path, "ca.crt"),
                    },
                },
            ],
            "users": [
                {
                    "name": "self",
                    "user": {
                        "token": token,
                    },
                },
            ],
            "contexts": [
                {
                    "name": "self",
                    "context": {
                        "cluster": "self",
                        "user": "self",
                    },
                }
            ],
            "current-context": "self",
        }
        self = cls(doc)
        return self

    @classmethod
    def from_file(cls, filename):
        """
        Creates an instance of the KubeConfig class from a kubeconfig file.

        :Parameters:
           - `filename`: The full path to the configuration file
        """
        filename = os.path.expanduser(filename)
        if not os.path.isfile(filename):
            raise exceptions.PyKubeError("Configuration file {} not found".format(filename))
        with open(filename) as f:
            doc = yaml.safe_load(f.read())
        self = cls(doc)
        self.filename = filename
        return self

    @classmethod
    def from_url(cls, url):
        """
        Creates an instance of the KubeConfig class from a single URL (useful
        for interacting with kubectl proxy).
        """
        doc = {
            "clusters": [
                {
                    "name": "self",
                    "cluster": {
                        "server": url,
                    },
                },
            ],
            "contexts": [
                {
                    "name": "self",
                    "context": {
                        "cluster": "self",
                    },
                }
            ],
            "current-context": "self",
        }
        self = cls(doc)
        return self

    def __init__(self, doc):
        """
        Creates an instance of the KubeConfig class.
        """
        self.doc = doc
        self._current_context = None
        if "current-context" in doc and doc["current-context"]:
            self.set_current_context(doc["current-context"])

    def set_current_context(self, value):
        """
        Sets the context to the provided value.

        :Parameters:
           - `value`: The value for the current context
        """
        self._current_context = value

    @property
    def current_context(self):
        if self._current_context is None:
            raise exceptions.PyKubeError("current context not set; call set_current_context")
        return self._current_context

    @property
    def clusters(self):
        """
        Returns known clusters by exposing as a read-only property.
        """
        if not hasattr(self, "_clusters"):
            cs = {}
            for cr in self.doc["clusters"]:
                cs[cr["name"]] = c = copy.deepcopy(cr["cluster"])
                if "server" not in c:
                    c["server"] = "http://localhost"
                BytesOrFile.maybe_set(c, "certificate-authority")
            self._clusters = cs
        return self._clusters

    @property
    def users(self):
        """
        Returns known users by exposing as a read-only property.
        """
        if not hasattr(self, "_users"):
            us = {}
            if "users" in self.doc:
                for ur in self.doc["users"]:
                    us[ur["name"]] = u = copy.deepcopy(ur["user"])
                    BytesOrFile.maybe_set(u, "client-certificate")
                    BytesOrFile.maybe_set(u, "client-key")
            self._users = us
        return self._users

    @property
    def contexts(self):
        """
        Returns known contexts by exposing as a read-only property.
        """
        if not hasattr(self, "_contexts"):
            cs = {}
            for cr in self.doc["contexts"]:
                cs[cr["name"]] = copy.deepcopy(cr["context"])
            self._contexts = cs
        return self._contexts

    @property
    def cluster(self):
        """
        Returns the current selected cluster by exposing as a
        read-only property.
        """
        return self.clusters[self.contexts[self.current_context]["cluster"]]

    @property
    def user(self):
        """
        Returns the current user by exposing as a read-only property.
        """
        return self.users.get(self.contexts[self.current_context].get("user", ""), {})

    @property
    def namespace(self):
        """
        Returns the current context namespace by exposing as a read-only property.
        """
        return self.contexts[self.current_context].get("namespace", "default")

    def persist_doc(self):
        if not hasattr(self, "filename") or not self.filename:
            # Config was provided as string, not way to persit it
            return
        with open(self.filename, "w") as f:
            yaml.safe_dump(self.doc, f, encoding='utf-8',
                           allow_unicode=True, default_flow_style=False)

    def reload(self):
        if hasattr(self, "_users"):
            delattr(self, "_users")
        if hasattr(self, "_contexts"):
            delattr(self, "_contexts")
        if hasattr(self, "_clusters"):
            delattr(self, "_clusters")


class BytesOrFile(object):
    """
    Implements the same interface for files and byte input.
    """

    @classmethod
    def maybe_set(cls, d, key):
        file_key = key
        data_key = "{}-data".format(key)
        if data_key in d:
            d[file_key] = cls(data=d[data_key])
            del d[data_key]
        elif file_key in d:
            d[file_key] = cls(filename=d[file_key])

    def __init__(self, filename=None, data=None):
        """
        Creates a new instance of BytesOrFile.

        :Parameters:
           - `filename`: A full path to a file
           - `data`: base64 encoded bytes
        """
        self._filename = None
        self._bytes = None
        if filename is not None and data is not None:
            raise TypeError("filename or data kwarg must be specified, not both")
        elif filename is not None:
            if not os.path.isfile(filename):
                raise exceptions.PyKubeError("'{}' file does not exist".format(filename))
            self._filename = filename
        elif data is not None:
            self._bytes = base64.b64decode(data)
        else:
            raise TypeError("filename or data kwarg must be specified")

    def bytes(self):
        """
        Returns the provided data as bytes.
        """
        if self._filename:
            with open(self._filename, "rb") as f:
                return f.read()
        else:
            return self._bytes

    def filename(self):
        """
        Returns the provided data as a file location.
        """
        if self._filename:
            return self._filename
        else:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(self._bytes)
            return f.name
