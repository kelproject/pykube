# ChangeLog

## Development

### Features

* `KubeConfig` learned to handle empty or missing user configuration
* `HTTPClient` learned to create an HTTP session with no authentication

## 0.12.0

### Features

* `APIObject` learned to use JSON Merge Patch instead of JSON Patch
* `Deployment` and `ReplicaSet` learned `scale` method

### Bug fixes

* `Job.scale` fixed to work as advertised
* `Pod.ready` learned to handle no conditions as empty conditions

## 0.11.3

### Bug fixes

* CRITICAL: `Query._clone` learned to copy the selector

## 0.11.2

### Bug fixes

* `Query.get` re-learned how to return a single object from the query cache
* `HTTPClient` learned how to handle no namespace to produce correct URLs

## 0.11.1

### Bug fixes

* `HTTPClient` learned to issue requests against the batch APIs

## 0.11.0

pykube is now hosted under the Kel Project.

### Features

* added Kubernetes API object: `ReplicaSet`
* `Job` object uses `batch/v1` kind
* `Job` object learned to scale to a new number of replicas

### Bug fixes

* `HTTPClient` learned to warn when an IP hostname is used on Python < 3.5

## 0.10.0

### Features

* added Kubernetes API objects: `ConfigMap` and `Ingress`
* `KubeConfig.from_file` learned to expand `~` shortcut in paths
* `KubeConfig.from_service_account` learned to take a custom path
* added `kind` attribute to all API objects

### Bug fixes

* `RollingUpdater` learned to validate selectors and labels (matching kubectl)

## 0.9.0

### Features

* added Kubernetes API objects: `Deployment`, `Job`, `PersistentVolume` and `PersistentVolumeClaim`
* improved exception message when Kubernetes API responds with an error

### Bug fixes

* added `DaemonSet` to public API
