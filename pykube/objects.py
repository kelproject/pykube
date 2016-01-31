import json
import time

from .query import ObjectManager


class APIObject:

    def __init__(self, api, obj):
        self.api = api
        self.obj = obj

    @property
    def name(self):
        return self.obj["metadata"]["name"]

    @property
    def namespace(self):
        return self.obj["metadata"]["namespace"]

    def create(self):
        r = self.api.post(
            url=self.endpoint,
            namespace=self.namespace,
            data=json.dumps(self.obj),
        )
        r.raise_for_status()
        self.obj = r.json()

    def reload(self):
        r = self.api.get(
            url="{}/{}".format(self.endpoint, self.name),
            namespace=self.namespace,
        )
        r.raise_for_status()
        self.obj = r.json()

    def delete(self):
        r = self.api.delete(
            url="{}/{}".format(self.endpoint, self.name),
            namespace=self.namespace,
        )
        r.raise_for_status()


class ReplicationController(APIObject):

    endpoint = "replicationcontrollers"
    objects = ObjectManager(endpoint)

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


class Pod(APIObject):

    endpoint = "pods"
    objects = ObjectManager(endpoint)

    @property
    def ready(self):
        cs = self.obj["status"]["conditions"]
        condition = next((c for c in cs if c["type"] == "Ready"), None)
        return condition is not None and condition["status"] == "True"
