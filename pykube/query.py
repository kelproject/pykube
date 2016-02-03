from six.moves.urllib.parse import urlencode

from .exceptions import ObjectDoesNotExist


everything = object()


class Query(object):

    def __init__(self, api, endpoint, api_obj_class, namespace=None):
        self.api = api
        self.endpoint = endpoint
        self.api_obj_class = api_obj_class
        self.namespace = namespace
        self.selector = everything

    def all(self):
        return self

    def get_by_name(self, name):
        r = self.api.get(
            url="{}/{}".format(self.endpoint, name),
            namespace=self.namespace,
        )
        if not r.ok:
            if r.status_code == 404:
                raise ObjectDoesNotExist("{} does not exist.".format(name))
            r.raise_for_status()
        return self.api_obj_class(self.api, r.json())

    def get(self, *args, **kwargs):
        if "name" in kwargs:
            return self.get_by_name(kwargs["name"])
        clone = self.filter(*args, **kwargs)
        num = len(clone)
        if num == 1:
            return clone.query_cache[0]
        if not num:
            raise ObjectDoesNotExist("get() returned zero objects")
        raise ValueError("get() more than one object; use filter")

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
            kwargs = {
                "url": "{}{}".format(self.endpoint, "?{}".format(query_string) if query_string else ""),
            }
            if self.namespace is not None:
                kwargs["namespace"] = self.namespace
            r = self.api.get(**kwargs)
            r.raise_for_status()
            cache = []
            for obj in r.json()["items"]:
                cache.append(self.api_obj_class(self.api, obj))
            self._query_cache = cache
        return self._query_cache

    def __len__(self):
        return len(self.query_cache)

    def __iter__(self):
        return iter(self.query_cache)


class ObjectManager(object):

    def __init__(self, namespace=None):
        self.namespace = namespace

    def __call__(self, api):
        return Query(api, self.endpoint, self.api_obj_class, namespace=self.namespace)

    def __get__(self, obj, api_obj_class):
        assert obj is None, "cannot invoke objects on resource object."
        self.api_obj_class = api_obj_class
        self.endpoint = api_obj_class.endpoint
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
