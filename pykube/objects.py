import json
import time

from .query import ObjectManager


DEFAULT_NAMESPACE = "default"


class APIObject:

    objects = ObjectManager()
    namespace = None

    def __init__(self, api, obj):
        self.api = api
        self.obj = obj

    @property
    def name(self):
        return self.obj["metadata"]["name"]

    def api_kwargs(self, **kwargs):
        kw = {}
        collection = kwargs.pop("collection", False)
        if collection:
            kw["url"] = self.endpoint
        else:
            kw["url"] = "{}/{}".format(self.endpoint, self.name)
        if self.namespace is not None:
            kw["namespace"] = self.namespace
        kw.update(kwargs)
        return kw

    def create(self):
        r = self.api.post(**self.api_kwargs(data=json.dumps(self.obj), collection=True))
        r.raise_for_status()
        self.obj = r.json()

    def reload(self):
        r = self.api.get(**self.api_kwargs())
        r.raise_for_status()
        self.obj = r.json()

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
        r = self.api.patch(
            url="replicationcontrollers/{}".format(self.name),
            namespace=self.namespace,
            headers={
                "Content-Type": "application/strategic-merge-patch+json",
            },
            data=json.dumps({
                "spec": {
                    "replicas": replicas,
                },
            })
        )
        r.raise_for_status()
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
