from six.moves.urllib.parse import urlencode


everything = object()


class Query:

    def __init__(self, api, endpoint, api_obj_class):
        self.api = api
        self.endpoint = endpoint
        self.api_obj_class = api_obj_class
        self.namespace = "default"
        self.selector = everything

    def all(self):
        return self

    def filter(self, namespace=None, selector=None):
        if namespace is not None:
            self.namespace = namespace
        if selector is not None:
            self.selector = selector
        return self

    @property
    def query_cache(self):
        if not hasattr(self, "_query_cache"):
            params = {}
            if self.selector is not everything:
                params["labelSelector"] = as_selector(self.selector)
            query_string = urlencode(params)
            r = self.api.get(
                url="{}{}".format(self.endpoint, "?{}".format(query_string) if query_string else ""),
                namespace=self.namespace,
            )
            r.raise_for_status()
            cache = []
            for obj in r.json()["items"]:
                cache.append(self.api_obj_class(self.api, obj))
            self._query_cache = cache
        return self._query_cache

    def __iter__(self):
        return iter(self.query_cache)


class ObjectManager:

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __call__(self, api):
        return Query(api, self.endpoint, self.api_obj_class)

    def __get__(self, obj, api_obj_class):
        assert obj is None, "cannot invoke objects on resource object."
        self.api_obj_class = api_obj_class
        return self


def as_selector(value):
    if isinstance(value, str):
        return value
    s = []
    for k, v in value.items():
        bits = k.split("__")
        assert len(bits) <= 2, "too many __ in selector"
        if len(bits) == 1:
            label = bits[0]
            op = "eq"
        else:
            label = bits[0]
            op = bits[1]
        # map operator to selector
        if op == "eq":
            s.append("{} = {}".format(label, v))
        elif op == "neq":
            s.append("{} != {}".format(label, v))
        elif op == "in":
            s.append("{} in ({})".format(label, ",".join(v)))
        elif op == "notin":
            s.append("{} notin ({})".format(label, ",".join(v)))
        else:
            raise ValueError("{} is not a valid comparsion operator".format(op))
    return ",".join(s)
