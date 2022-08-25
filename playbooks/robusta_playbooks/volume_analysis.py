from robusta.api import action, PersistentVolumeEvent, RobustaPod, ObjectMeta, PodSpec, Volume, PersistentVolumeClaimVolumeSource, Container, VolumeMount, List, BaseBlock, MarkdownBlock,Finding,FindingSource,FindingType


@action
def volume_analysis(event: PersistentVolumeEvent):
    # This function creates a reader pod (using the builtin hikaru library) that mount and output contents present on your persistent volume.
    """
    This action shows you the files present on your persistent volume
    """

    # Get persistent volume data the object contains data related to PV like metadata etc
    volume = event.get_persistentvolume()

    # Define a reader (busybox) pod which mounts the volume

    reader_pod = RobustaPod(
        apiVersion="v1",
        kind="Pod",
        metadata=ObjectMeta(
            name="volume-inspector",
        ),
        spec=PodSpec(
            volumes=[
                Volume(
                    name="pvc-mount",
                    persistentVolumeClaim=PersistentVolumeClaimVolumeSource(
                        claimName=volume.spec.claimRef.name
                    )
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
            ]
        )
    )
    # create the pod defined
    reader_pod_create = reader_pod.createNamespacedPod(
        namespace=volume.spec.claimRef.namespace,
    ).obj

    
    try:
        #https://docs.robusta.dev/master/developer-guide/actions/findings-api.html
        finding = Finding(
        title=f"Persistent Volume content",
        source=FindingSource.MANUAL,
        aggregation_key="volume_analysis",
        finding_type=FindingType.REPORT,
        failure=False,
    )
        # exec a cmd on the reader pod to get file contents of PV
        cmd = f"ls -R /pvc"
        block_list: List[BaseBlock] = []
        output = reader_pod_create.exec(cmd)
        block_list.append(MarkdownBlock(
            f"Files currently present on your volume {volume.metadata.name} are:*"))
        block_list.append(MarkdownBlock(output))
        finding.add_enrichment(block_list)
        event.add_finding(finding)
        print(f"output is {output}")
    finally:
        # delete the reader pod
        reader_pod_create.deleteNamespacedPod(
            reader_pod_create.metadata.name, reader_pod_create.metadata.namespace
        )
