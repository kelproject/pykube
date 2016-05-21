# ChangeLog

## 0.11.0

### Features

* `Job` object uses `batch/v1` kind

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
