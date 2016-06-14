import time


class ReplicatedMixin(object):

    scalable_attr = "replicas"

    @property
    def replicas(self):
        return self.obj["spec"]["replicas"]

    @replicas.setter
    def replicas(self, value):
        self.obj["spec"]["replicas"] = value


class ScalableMixin(object):

    @property
    def scalable(self):
        return getattr(self, self.scalable_attr)

    @scalable.setter
    def scalable(self, value):
        setattr(self, self.scalable_attr, value)

    def scale(self, replicas=None):
        count = self.scalable if replicas is None else replicas
        self.exists(ensure=True)
        if self.scalable != count:
            self.scalable = count
            self.update()
            while True:
                self.reload()
                if self.scalable == count:
                    break
                time.sleep(1)
