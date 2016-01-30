
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

    @property
    def replicas(self):
        return self.obj["spec"]["replicas"]

    @replicas.setter
    def replicas(self, value):
        self.obj["spec"]["replicas"] = value


class Pod(APIObject):

    @property
    def ready(self):
        cs = self.obj["status"]["conditions"]
        condition = next((c for c in cs if c["type"] == "Ready"), None)
        return condition is not None and condition["status"] == "True"
