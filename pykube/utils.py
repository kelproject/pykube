from six.moves import zip_longest


empty = object()


def obj_merge(a, b):
    c = {}
    for k, v in a.items():
        if k not in b:
            c[k] = v
        else:
            c[k] = obj_check(v, b[k])
    for k, v in b.items():
        if k not in a:
            c[k] = v
    return c


def obj_check(a, b):
    c = None
    if not isinstance(a, type(b)):
        c = a
    else:
        if isinstance(a, dict):
            c = obj_merge(a, b)
        elif isinstance(a, list):
            z = []
            for x, y in zip_longest(a, b, fillvalue=empty):
                if x is empty:
                    z.append(y)
                elif y is empty:
                    z.append(x)
                else:
                    z.append(obj_check(x, y))
            c = z
        else:
            c = a
    return c
