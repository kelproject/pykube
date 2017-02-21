"""
Python client for Kubernetes
"""

from .config import KubeConfig  # noqa
from .exceptions import KubernetesError, PyKubeError, ObjectDoesNotExist  # noqa
from .http import HTTPClient  # noqa
from .objects import (  # noqa
    ConfigMap,
    DaemonSet,
    Deployment,
    Endpoint,
    Event,
    HorizontalPodAutoscaler,
    Ingress,
    Job,
    Namespace,
    Node,
    PersistentVolume,
    PersistentVolumeClaim,
    PetSet,
    Pod,
    ReplicationController,
    ReplicaSet,
    ResourceQuota,
    Secret,
    Service,
    ServiceAccount,
    StatefulSet,
    ThirdPartyResource,
    Role,
    ClusterRole,
    RoleBinding,
    ClusterRoleBinding,
)
from .query import now, all_ as all, everything  # noqa
