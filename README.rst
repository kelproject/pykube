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

Query for all ready pods in a custom namespace:

.. code:: python

    import operator
    import pykube

    api = pykube.HTTPClient(pykube.KubeConfig.from_file("/Users/<username>/.kube/config"))
    pods = pykube.Pod.objects(api).filter(namespace="gondor-system")
    ready_pods = filter(operator.attrgetter("ready"), pods)

Selector query:

.. code:: python

    pods = pykube.Pod.objects(api).filter(
        namespace="gondor-system",
        selector={"gondor.io/name__in": {"api-web", "api-worker"}},
    )

Create a ReplicationController:

.. code:: python

    obj = {
        "apiVersion": "v1",
        "kind": "ReplicationController",
        "metadata": {
            "name": "my-rc",
            "namespace": "gondor-system"
        },
        "spec": {
            "replicas": 3,
            "selector": {
                "app": "nginx"
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "nginx"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx",
                            "ports": [
                                {"containerPort": 80}
                            ]
                        }
                    ]
                }
            }
        }
    }
    pykube.ReplicationController(obj).create()

Delete a ReplicationController:

    obj = {
        "apiVersion": "v1",
        "kind": "ReplicationController",
        "metadata": {
            "name": "my-rc",
            "namespace": "gondor-system"
        }
    }
    pykube.ReplicationController(obj).delete()

Requirements
============

* Python 2.7 or 3.4+
* requests (included in ``install_requires``)
* PyYAML (included in ``install_requires``)
