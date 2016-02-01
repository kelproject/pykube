import copy
import json
import time

import jsonpatch

from .exceptions import ObjectDoesNotExist
from .query import ObjectManager


DEFAULT_NAMESPACE = "default"


class APIObject:

    objects = ObjectManager()
    namespace = None

    def __init__(self, api, obj):
        self.api = api
        self.set_obj(obj)

    def set_obj(self, obj):
        self.obj = obj
        self._original_obj = copy.deepcopy(obj)

    @property
    def name(self):
        return self.obj["metadata"]["name"]

    def api_kwargs(self, **kwargs):
        kw = {}
        collection = kwargs.pop("collection", False)
        if collection:
            kw["url"] = self.endpoint
        else:
            kw["url"] = "{}/{}".format(self.endpoint, self._original_obj["metadata"]["name"])
        if self.namespace is not None:
            kw["namespace"] = self.namespace
        kw.update(kwargs)
        return kw

    def exists(self, ensure=False):
        r = self.api.get(**self.api_kwargs())
        if r.status_code not in {200, 404}:
            r.raise_for_status()
        if not r.ok:
            if ensure:
                raise ObjectDoesNotExist("{} does not exist.".format(self.name))
            else:
                return False
        return True

    def create(self):
        r = self.api.post(**self.api_kwargs(data=json.dumps(self.obj), collection=True))
        r.raise_for_status()
        self.set_obj(r.json())

    def reload(self):
        r = self.api.get(**self.api_kwargs())
        r.raise_for_status()
        self.set_obj(r.json())

    def update(self):
        patch = jsonpatch.make_patch(self._original_obj, self.obj)
        r = self.api.patch(**self.api_kwargs(
            headers={"Content-Type": "application/json-patch+json"},
            data=str(patch),
        ))
        r.raise_for_status()
        self.set_obj(r.json())

    def delete(self):
        r = self.api.delete(**self.api_kwargs())
        if r.status_code != 404:
            r.raise_for_status()


class Namespace(APIObject):

    endpoint = "namespaces"


class Node(APIObject):

    endpoint = "nodes"


class NamespacedAPIObject(APIObject):

    objects = ObjectManager(namespace=DEFAULT_NAMESPACE)

    @property
    def namespace(self):
        if self.obj["metadata"].get("namespace"):
            return self.obj["metadata"]["namespace"]
        else:
            return DEFAULT_NAMESPACE


class Service(NamespacedAPIObject):

    endpoint = "services"


class Endpoint(NamespacedAPIObject):

    endpoint = "endpoints"


class Secret(NamespacedAPIObject):

    endpoint = "secrets"


class ReplicationController(NamespacedAPIObject):

    endpoint = "replicationcontrollers"

    @property
    def replicas(self):
        return self.obj["spec"]["replicas"]

    @replicas.setter
    def replicas(self, value):
        self.obj["spec"]["replicas"] = value

    def scale(self, replicas=None):
        if replicas is None:
            replicas = self.replicas
        self.exists(ensure=True)
        self.replicas = replicas
        self.update()
        while True:
            self.reload()
            if self.replicas == replicas:
                break
            time.sleep(1)


class Pod(NamespacedAPIObject):

    endpoint = "pods"

    @property
    def ready(self):
        cs = self.obj["status"]["conditions"]
        condition = next((c for c in cs if c["type"] == "Ready"), None)
        return condition is not None and condition["status"] == "True"
