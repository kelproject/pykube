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
    def __init__(self, code, message):
        super(HTTPError, self).__init__(message)
        self.code = code


class ObjectDoesNotExist(PyKubeError):
    pass
