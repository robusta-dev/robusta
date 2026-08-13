import logging

from hikaru.model.rel_1_26 import (
    Container,
    ObjectMeta,
    PersistentVolumeClaim,
    PersistentVolumeClaimVolumeSource,
    PodList,
    PodSpec,
    Volume,
    VolumeMount,
)
from robusta.api import (
    FileBlock,
    Finding,
    FindingSource,
    FindingType,
    MarkdownBlock,
    PersistentVolumeEvent,
    RobustaPod,
    action,
)


@action
def volume_analysis(event: PersistentVolumeEvent):
    """
    This action shows you the files present on your persistent volume
    """
    function_name = "VolumeAnalysis"
    # https://docs.robusta.dev/master/extending/actions/findings-api.html
    finding = Finding(
        title="Persistent Volume content",
        source=FindingSource.MANUAL,
        aggregation_key=function_name,
        finding_type=FindingType.REPORT,
        failure=False,
    )

    if not event.get_persistentvolume():
        logging.error(f"VolumeAnalysis was called on event without Persistent Volume: {event}")
        return

    # Get persistent volume data the object contains data related to PV like metadata etc
    pv = event.get_persistentvolume()
    pv_claimref = pv.spec.claimRef
    reader_pod = None

    try:

        if pv_claimref is not None:
            # Do this if there is a PVC attached to PV
            pvc_obj = PersistentVolumeClaim.readNamespacedPersistentVolumeClaim(
                name=pv_claimref.name, namespace=pv_claimref.namespace
            ).obj
            pod = get_pod_related_to_pvc(pvc_obj, pv)

            if pod is not None:
                # Do this if a Pod is using PVC

                volume_mount_name = None

                # Find name of the mounted volume on pod
                for volume in pod.spec.volumes:
                    if volume.persistentVolumeClaim.claimName == pv_claimref.name:
                        volume_mount_name = volume.name
                        break

                # Use name of the mounted volume to find the correct volume mount
                container_found_flag = False
                container_volume_mount = None
                for container in pod.spec.containers:
                    if container_found_flag:
                        break
                    for volume_mount in container.volumeMounts:
                        if volume_mount_name == volume_mount.name:
                            container_volume_mount = volume_mount
                            container_found_flag = True
                            break

                result = pod.exec(f"ls -R {container_volume_mount.mountPath}/")  # type: ignore
                finding.title = f"Files present on persistent volume {pv.metadata.name} are: "
                finding.add_enrichment(
                    [
                        FileBlock("Data.txt: ", result.encode()),
                    ]
                )

            else:
                # Do this if no Pod is attached to PVC
                reader_pod = persistent_volume_reader(persistent_volume=pv)
                result = reader_pod.exec(f"ls -R {reader_pod.spec.containers[0].volumeMounts[0].mountPath}")
                finding.title = f"Files present on persistent volume {pv.metadata.name} are: "
                finding.add_enrichment(
                    [
                        FileBlock("Data.txt: ", result.encode()),
                    ]
                )
        else:
            finding.add_enrichment(
                [
                    MarkdownBlock(f"Persistent volume named {pv.metadata.name} have no persistent volume claim."),
                ]
            )

    finally:
        # delete the reader pod
        if reader_pod is not None:
            reader_pod.delete()

    event.add_finding(finding)


# returns a pod that mounts the given persistent volume


def persistent_volume_reader(persistent_volume):
    reader_pod_spec = RobustaPod(
        apiVersion="v1",
        kind="Pod",
        metadata=ObjectMeta(
            name="volume-inspector",
            namespace=persistent_volume.spec.claimRef.namespace,
        ),
        spec=PodSpec(
            volumes=[
                Volume(
                    name="pvc-mount",
                    persistentVolumeClaim=PersistentVolumeClaimVolumeSource(
                        claimName=persistent_volume.spec.claimRef.name
                    ),
                )
            ],
            containers=[
                Container(
                    name="pvc-inspector",
                    image="busybox",
                    command=["tail"],
                    args=["-f", "/dev/null"],
                    volumeMounts=[
                        VolumeMount(
                            mountPath="/pvc",
                            name="pvc-mount",
                        )
                    ],
                )
            ],
        ),
    )
    reader_pod = reader_pod_spec.create()
    return reader_pod


# function to get pod data related to a pvc


def get_pod_related_to_pvc(pvc_obj, pv_obj):
    pod_list = PodList.listNamespacedPod(pvc_obj.metadata.namespace).obj
    pod = None
    for pod in pod_list.items:
        for volume in pod.spec.volumes:
            if volume.persistentVolumeClaim:
                if volume.persistentVolumeClaim.claimName == pv_obj.spec.claimRef.name:
                    return pod
