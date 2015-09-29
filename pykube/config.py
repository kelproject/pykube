import base64
import copy
import tempfile

import yaml


class KubeConfig(object):

    def __init__(self, filename):
        self.filename = filename
        self.doc = None
        self.current_context = None

    def parse(self):
        if self.doc is not None:
            return
        with open(self.filename) as f:
            self.doc = yaml.load(f.read())
        if "current-context" in self.doc and self.doc["current-context"]:
            self.set_current_context(self.doc["current-context"])

    def set_current_context(self, value):
        self.current_context = value

    @property
    def clusters(self):
        if not hasattr(self, "_clusters"):
            self.parse()
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
        if not hasattr(self, "_users"):
            self.parse()
            us = {}
            for ur in self.doc["users"]:
                us[ur["name"]] = u = copy.deepcopy(ur["user"])
                BytesOrFile.maybe_set(u, "client-certificate")
                BytesOrFile.maybe_set(u, "client-key")
            self._users = us
        return self._users

    @property
    def contexts(self):
        if not hasattr(self, "_contexts"):
            self.parse()
            cs = {}
            for cr in self.doc["contexts"]:
                cs[cr["name"]] = copy.deepcopy(cr["context"])
            self._contexts = cs
        return self._contexts

    @property
    def cluster(self):
        self.parse()
        if self.current_context is None:
            raise Exception("current context not set; call set_current_context")
        return self.clusters[self.contexts[self.current_context]["cluster"]]

    @property
    def user(self):
        self.parse()
        if self.current_context is None:
            raise Exception("current context not set; call set_current_context")
        return self.users[self.contexts[self.current_context]["user"]]


class BytesOrFile(object):

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
        self._filename = None
        self._bytes = None
        if data.startswith("/"):
            self._filename = data
        else:
            self._bytes = base64.b64decode(data)

    def bytes(self):
        if self._filename:
            with open(self._filename, "rb") as f:
                return f.read()
        else:
            return self._bytes

    def filename(self):
        if self._filename:
            return self._filename
        else:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(self._bytes)
            return f.name
