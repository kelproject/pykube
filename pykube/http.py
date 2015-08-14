import base64

import requests
import yaml

from .exceptions import KubernetesError


class HTTPClient(object):

    def __init__(self, kubeconfig_path, cluster_name, user_name, url=None, namespace="default", version="v1"):
        self.kubeconfig_path = kubeconfig_path
        self.cluster_name = cluster_name
        self.user_name = user_name
        self.url = url
        self.namespace = namespace
        self.version = version

        self.session = self.build_session()

    def build_session(self):
        with open(self.kubeconfig_path, "rb") as fp:
            kubeconfig = yaml.load(fp.read())

        # prepare the CA bundle
        for cluster in kubeconfig["clusters"]:
            if cluster["name"] == self.cluster_name:
                break
        else:
            raise KubernetesError("cannot find cluster `{}` cluster in {}".format(self.cluster_name, self.kubeconfig_path))
        # @@@ temporary file? need to investigate when this is opened and read by urllib3
        ca_cert_file = "/tmp/k8s-ca-cert.pem"
        with open(ca_cert_file, "wb") as fp:
            fp.write(base64.b64decode(cluster["cluster"]["certificate-authority-data"]))

        # set URL if needed
        if self.url is None:
            self.url = cluster["cluster"]["server"]

        # prepare client certificate
        for user in kubeconfig["users"]:
            if user["name"] == self.user_name:
                break
        else:
            raise KubernetesError("cannot find user `{}` cluster in {}".format(self.user_name, self.kubeconfig_path))
        # @@@ temporary files? need to investigate when these are opened and read by urllib3
        client_key_file = "/tmp/k8s-client-key.pem"
        client_cert_file = "/tmp/k8s-client-cert.pem"
        with open(client_key_file, "wb") as fp:
            fp.write(base64.b64decode(user["user"]["client-key-data"]))
        with open(client_cert_file, "wb") as fp:
            fp.write(base64.b64decode(user["user"]["client-certificate-data"]))

        # prepare requests session object
        s = requests.Session()
        s.verify = ca_cert_file
        s.cert = (client_cert_file, client_key_file)
        return s

    def get_kwargs(self, **kwargs):
        kwargs["url"] = "{}/api/{}/namespaces/{}{}".format(
            self.url,
            self.version,
            self.namespace,
            kwargs.get("url", "")
        )
        return kwargs

    def request(self, *args, **kwargs):
        return self.session.request(*args, **self.get_kwargs(**kwargs))

    def get(self, *args, **kwargs):
        return self.session.get(*args, **self.get_kwargs(**kwargs))

    def options(self, *args, **kwargs):
        return self.session.options(*args, **self.get_kwargs(**kwargs))

    def head(self, *args, **kwargs):
        return self.session.head(*args, **self.get_kwargs(**kwargs))

    def post(self, *args, **kwargs):
        return self.session.post(*args, **self.get_kwargs(**kwargs))

    def put(self, *args, **kwargs):
        return self.session.put(*args, **self.get_kwargs(**kwargs))

    def patch(self, *args, **kwargs):
        return self.session.patch(*args, **self.get_kwargs(**kwargs))

    def delete(self, *args, **kwargs):
        return self.session.delete(*args, **self.get_kwargs(**kwargs))
