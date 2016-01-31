import json
import time

from .query import ObjectManager


class APIObject:

    def __init__(self, obj):
        self.obj = obj

    @property
    def name(self):
        return self.obj["metadata"]["name"]

    @property
    def namespace(self):
        return self.obj["metadata"]["namespace"]


class ReplicationController(APIObject):

    objects = ObjectManager("replicationcontrollers")

    @property
    def replicas(self):
        return self.obj["spec"]["replicas"]

    @replicas.setter
    def replicas(self, value):
        self.obj["spec"]["replicas"] = value

    def scale(self, api, replicas):
        r = api.patch(
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
            r = api.get(
                url="replicationcontrollers/{}".format(self.name),
                namespace=self.namespace,
            )
            r.raise_for_status()
            data = r.json()
            if data["status"]["replicas"] == replicas:
                break
            time.sleep(1)
        return ReplicationController(data)


class Pod(APIObject):

    objects = ObjectManager("pods")

    @property
    def ready(self):
        cs = self.obj["status"]["conditions"]
        condition = next((c for c in cs if c["type"] == "Ready"), None)
        return condition is not None and condition["status"] == "True"
