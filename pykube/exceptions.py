"""
Exceptions.
"""


class KubernetesError(Exception):
    """
    Base exception for all Kubernetes errors.
    """
    pass


class PyKubeError(KubernetesError):
    """
    PyKube specific errors.
    """
    pass


class HTTPError(PyKubeError):
    pass


class ObjectDoesNotExist(PyKubeError):
    pass
