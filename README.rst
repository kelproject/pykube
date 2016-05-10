pykube
======

.. image:: http://slack.kelproject.com/badge.svg
   :target: http://slack.kelproject.com/

.. image:: https://img.shields.io/travis/kelproject/pykube.svg
   :target: https://travis-ci.org/kelproject/pykube

.. image:: https://img.shields.io/pypi/dm/pykube.svg
   :target:  https://pypi.python.org/pypi/pykube/

.. image:: https://img.shields.io/pypi/v/pykube.svg
   :target:  https://pypi.python.org/pypi/pykube/

.. image:: https://img.shields.io/badge/license-apache-blue.svg
   :target:  https://pypi.python.org/pypi/pykube/

Python client library for Kubernetes

.. image:: https://storage.googleapis.com/kel-assets/kel_full-02_200.jpg
   :target: http://kelproject.com/

Kel is an open source Platform as a Service (PaaS) from Eldarion, Inc. that
makes it easy to manage web application deployment and hosting through the
entire lifecycle from development through testing to production. It adds
components and tools on top of Kubernetes that help developers manage their
application infrastructure. Kel builds on Eldarion's 7+ years experience running
one of the leading Python and Django PaaSes.

For more information about Kel, see `kelproject.com`_, follow us on Twitter
`@projectkel`_, and join our `Slack team`_.

.. _kelproject.com: http://kelproject.com/
.. _@projectkel: https://twitter.com/projectkel
.. _Slack team: http://slack.kelproject.com/

Features
--------

* HTTP interface using requests using kubeconfig for authentication
* Python native querying of Kubernetes API objects

Installation
------------

To install pykube, use pip::

    pip install pykube

Usage
-----

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

.. code:: python

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
------------

* Python 2.7 or 3.3+
* requests (included in ``install_requires``)
* PyYAML (included in ``install_requires``)

License
-------

The code in this project is licensed under the Apache License, version 2.0
(included in this repository under LICENSE).


Contributing
------------

By making a contribution to this project, you are agreeing to the `Developer
Certificate of Origin v1.1`_ (also included in this repository under DCO.txt).

.. _Developer Certificate of Origin v1.1: http://developercertificate.org


Code of Conduct
----------------

In order to foster a kind, inclusive, and harassment-free community, the Kel
Project follows the `Contributor Covenant Code of Conduct`_.

.. _Contributor Covenant Code of Conduct: http://contributor-covenant.org/version/1/4/


Commercial Support
------------------

Commercial support for Kel is available through Eldarion, please contact
info@eldarion.com.
