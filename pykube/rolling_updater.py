import logging
import math
import time

from .objects import Pod
from .exceptions import KubernetesError


logger = logging.getLogger(__name__)


class RollingUpdater(object):

    def __init__(self, api, old_rc, new_rc, **kwargs):
        self.api = api
        self.old_rc = old_rc
        self.new_rc = new_rc
        self.update_period = kwargs.get("update_period", 10)
        self.max_unavailable = kwargs.get("max_unavailable", 0)
        self.max_surge = kwargs.get("max_surge", 1)

    def update(self):
        desired = self.new_rc.replicas
        original = self.old_rc.replicas
        max_unavailable = extract_max_value(self.max_unavailable, "max_unavailable", desired)
        max_surge = extract_max_value(self.max_surge, "max_surge", desired)
        min_available = original - max_unavailable
        if self.new_rc.exists():
            logger.info("ReplicationController {} already exists.".format(self.new_rc.name))
            return False
        new_selector = self.new_rc.obj["spec"]["selector"]
        old_selector = self.old_rc.obj["spec"]["selector"]
        if new_selector == old_selector:
            raise KubernetesError(
                "error: {} must specify a matching key with non-equal value in Selector for {}".format(
                    self.new_rc.name,
                    self.old_rc.name
                ))
        new_labels = self.new_rc.obj["spec"]["template"]["metadata"]["labels"]
        if new_selector != new_labels:
            raise KubernetesError(
                "The ReplicationController {} is invalid. spec.template.metadata.labels: Invalid value: {}: `selector` does not match template `labels` {}".format(
                    self.new_rc.name,
                    new_selector,
                    new_labels))

        self.create_rc(self.new_rc)
        logger.info("Created {}".format(self.new_rc.name))
        new_rc, old_rc = self.new_rc, self.old_rc

        logger.info(
            "scaling up {} from {} to {}, scaling down {} from {} to 0 (keep {} pods available, don't exceed {} pods)".format(
                new_rc.name,
                new_rc.replicas,
                desired,
                old_rc.name,
                old_rc.replicas,
                min_available,
                original + max_surge
            ),
        )

        while new_rc.replicas != desired or old_rc.replicas != 0:
            scaled_rc = self.scale_up(
                new_rc, old_rc,
                original, desired,
                max_surge, max_unavailable,
            )
            new_rc = scaled_rc
            time.sleep(self.update_period)
            scaled_rc = self.scale_down(
                new_rc, old_rc,
                desired,
                min_available, max_surge,
            )
            old_rc = scaled_rc

        logger.info("Update succeeded. Deleting {}".format(old_rc.name))
        self.cleanup(old_rc, new_rc)

    def scale_up(self, new_rc, old_rc, original, desired, max_surge, max_unavailable):
        # if we're already at the desired, do nothing.
        if new_rc.replicas == desired:
            return new_rc
        # scale up as far as we can based on the surge limit.
        increment = (original + max_surge) - (old_rc.replicas + new_rc.replicas)
        # if the old is already scaled down, go ahead and scale all the way up.
        if old_rc.replicas == 0:
            increment = desired - new_rc.replicas
        # we can't scale up without violating the surge limit, so do nothing
        if increment <= 0:
            return new_rc
        # increase the replica count, and deal with fenceposts
        new_rc.replicas = min(desired, new_rc.replicas + increment)
        # perform the scale up
        logger.info("scaling {} up to {}".format(new_rc.name, new_rc.replicas))
        new_rc.scale()
        return new_rc

    def scale_down(self, new_rc, old_rc, desired, min_available, max_surge):
        # already scaled down; do nothing.
        if old_rc.replicas == 0:
            return old_rc
        # block until there are any pods ready
        _, new_available = self.poll_for_ready_pods(old_rc, new_rc)
        # the old controller is considered as part of the total because we want
        # to maintain minimum availability even with a volatile old controller.
        # scale down as much as possible while maintaining minimum availability.
        decrement = old_rc.replicas + new_available - min_available
        # the decrement normally shouldn't drop below zero because the available
        # count always start below the old replica count, but the old replica
        # count can decrement due to externalities like pods death in the replica
        # set. this will be considered a transient condition; do nothing and try
        # again later with new readiness values.
        #
        # if the most we can scale is zero, it means we can't scale down without
        # violating the minimum. do nothing and try again later when conditions
        # may have changed.
        if decrement <= 0:
            return old_rc
        # reduce the replica count, and deal with fenceposts
        old_rc.replicas = max(0, old_rc.replicas - decrement)
        # if the new is already fully scaled and available up to the desired size,
        # go ahead and scale old all the way down
        if new_rc.replicas == desired and new_available == desired:
            old_rc.replicas = 0
        # perform scale down
        logger.info("scaling {} down to {}".format(old_rc.name, old_rc.replicas))
        old_rc.scale()
        return old_rc

    def cleanup(self, old_rc, new_rc):
        old_rc.delete()

    def poll_for_ready_pods(self, old_rc, new_rc):
        controllers = [old_rc, new_rc]
        old_ready = 0
        new_ready = 0
        any_ready = False

        while True:
            for controller in controllers:
                pods = Pod.objects(self.api).filter(
                    namespace=controller.namespace,
                    selector=controller.obj["spec"]["selector"],
                )
                for pod in pods:
                    if pod.ready:
                        if controller.name == old_rc.name:
                            old_ready += 1
                        elif controller.name == new_rc.name:
                            new_ready += 1
                        any_ready = True
            if any_ready:
                break
            time.sleep(1)

        return old_ready, new_ready

    def create_rc(self, rc):
        rc.replicas = 0
        rc.create()


def extract_max_value(field, name, value):
    assert type(field) in {int, str}, "{} is not an int or str".format(type(field))
    if isinstance(field, int):
        assert field >= 0, "{} must be >= 0".format(name)
        return field
    if isinstance(field, str):
        v = int(field.replace("%", ""))
        assert v >= 0, "{} must be >= 0".format(name)
        return math.ceil(float(value) * (float(v) / 100.))
