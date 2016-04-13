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

    def __init__(self, doc):
        """
        Creates an instance of the KubeConfig class.
        """
        self.doc = doc
        self.current_context = None
        if "current-context" in doc and doc["current-context"]:
            self.set_current_context(doc["current-context"])

    def set_current_context(self, value):
        """
        Sets the context to the provided value.

        :Parameters:
           - `value`: The value for the current context
        """
        self.current_context = value

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
        if self.current_context is None:
            raise exceptions.PyKubeError("current context not set; call set_current_context")
        return self.clusters[self.contexts[self.current_context]["cluster"]]

    @property
    def user(self):
        """
        Returns the current user by exposing as a read-only property.
        """
        if self.current_context is None:
            raise exceptions.PyKubeError("current context not set; call set_current_context")
        return self.users[self.contexts[self.current_context]["user"]]


class BytesOrFile(object):
    """
    Implements the same interface for files and byte input.
    """

    @classmethod
    def maybe_set(cls, d, key):
        file_key = key
        data_key = "{}-data".format(key)
        if data_key in d:
            d[file_key] = cls(d[data_key])
            del d[data_key]
        elif file_key in d:
            d[file_key] = cls(d[file_key])

    def __init__(self, data):
        """
        Creates a new instance of BytesOrFile.

        :Parameters:
           - `data`: A full path to a file or base64 encoded bytes
        """
        self._filename = None
        self._bytes = None
        if data.startswith("/"):
            self._filename = data
        else:
            self._bytes = base64.b64decode(data)

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
