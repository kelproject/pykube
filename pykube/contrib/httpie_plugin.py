import inspect

from httpie.client import HTTPieHTTPAdapter
from httpie.compat import urlsplit
from httpie.plugins import TransportPlugin

import pykube


class PyKubeAdapter(HTTPieHTTPAdapter):

    def send(self, request, **kwargs):
        u = urlsplit(request.url)
        context = u.netloc
        config = pykube.KubeConfig.from_file("~/.kube/config", current_context=context)
        request.url = config.cluster["server"] + u.path

        # setup cluster API authentication

        if "token" in config.user and config.user["token"]:
            request.headers["Authorization"] = "Bearer {}".format(config.user["token"])
        elif "client-certificate" in config.user:
            kwargs["cert"] = (
                config.user["client-certificate"].filename(),
                config.user["client-key"].filename(),
            )

        # setup certificate verification

        if "certificate-authority" in config.cluster:
            kwargs["verify"] = config.cluster["certificate-authority"].filename()
        elif "insecure-skip-tls-verify" in config.cluster:
            kwargs["verify"] = not config.cluster["insecure-skip-tls-verify"]

        return super(PyKubeAdapter, self).send(request, **kwargs)


class PyKubeTransportPlugin(TransportPlugin):

    name = "PyKube Transport"
    description = "Authenticates against a Kubernetes cluster API"
    prefix = "pykube://"

    def get_adapter(self):
        # HACK work around not being given the ssl_version from httpie
        ssl_version = inspect.stack()[1][0].f_locals.get("ssl_version")
        return PyKubeAdapter(ssl_version=ssl_version)
