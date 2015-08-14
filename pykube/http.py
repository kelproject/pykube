import requests


class HTTPClient(object):

    def __init__(self, url=None, namespace="default", version="v1", verify=True, token=None):
        self.url = url
        self.namespace = namespace
        self.version = version
        self.verify = verify
        self.token = token
        self.session = self.build_session()

    def build_session(self):
        s = requests.Session()
        if self.token is not None:
            s.headers["Authorization"] = "Bearer {}".format(self.token)
        s.verify = self.verify
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
