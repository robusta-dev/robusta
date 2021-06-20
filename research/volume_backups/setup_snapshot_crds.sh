mkdir crds
wget https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/53469c21962339229dd150cbba50c34359acec73/config/crd/snapshot.storage.k8s.io_volumesnapshotclasses.yaml -O crds/a.yaml
wget https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/53469c21962339229dd150cbba50c34359acec73/config/crd/snapshot.storage.k8s.io_volumesnapshotcontents.yaml -O crds/b.yaml
wget https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/53469c21962339229dd150cbba50c34359acec73/config/crd/snapshot.storage.k8s.io_volumesnapshots.yaml -O crds/c.yaml
kubectl apply -f crds

mkdir controller
wget https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/master/deploy/kubernetes/snapshot-controller/rbac-snapshot-controller.yaml -O controller/a.yaml
wget https://raw.githubusercontent.com/kubernetes-csi/external-snapshotter/master/deploy/kubernetes/snapshot-controller/setup-snapshot-controller.yaml -O controller/b.yaml
kubectl apply -f controller
