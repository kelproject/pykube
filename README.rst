======
pykube
======

*Python client library for Kubernetes*

.. image:: https://img.shields.io/pypi/dm/pykube.svg
    :target:  https://pypi.python.org/pypi/pykube/

.. image:: https://img.shields.io/pypi/v/pykube.svg
    :target:  https://pypi.python.org/pypi/pykube/

.. image:: https://img.shields.io/badge/license-apache-blue.svg
    :target:  https://pypi.python.org/pypi/pykube/

Features
========

* HTTP interface using requests using kubeconfig for authentication
* Python native querying of Kubernetes API objects

Installation
============

To install pykube, use pip::

    pip install pykube

Usage
=====

A simple query for all ready pods in a custom namespace::

    import operator

    from pykube.config import KubeConfig
    from pykube.http import HTTPClient
    from pykube.objects import Pod


    api = HTTPClient(KubeConfig.from_file("/Users/<username>/.kube/config"))
    pods = Pod.objects(api).filter(namespace="gondor-system")
    ready_pods = filter(operator.attrgetter("ready"), pods)

Selector query::

    pods = Pod.objects(api).filter(
        namespace="gondor-system",
        selector={"gondor.io/name__in": {"api-web", "api-worker"}},
    )

Requirements
============

* Python 2.7 or 3.4+
* requests (included in ``install_requires``)
* PyYAML (included in ``install_requires``)
