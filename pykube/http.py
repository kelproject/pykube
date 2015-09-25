import requests


class HTTPClient(object):

    def __init__(self, config, version="v1"):
        self.config = config
        self.url = self.config.cluster["server"]
        self.version = version
        self.session = self.build_session()

    def build_session(self):
        s = requests.Session()
        if "certificate-authority" in self.config.cluster:
            s.verify = self.config.cluster["certificate-authority"].filename()
        if "token" in self.config.user and self.config.user["token"]:
            s.headers["Authorization"] = "Bearer {}".format(self.config.user["token"])
        else:
            s.cert = (
                self.config.user["client-certificate"].filename(),
                self.config.user["client-key"].filename(),
            )
        return s

    def get_kwargs(self, **kwargs):
        kwargs["url"] = "{}/api/{}/namespaces/{}{}".format(
            self.url,
            self.version,
            kwargs.pop("namespace", "default"),
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
