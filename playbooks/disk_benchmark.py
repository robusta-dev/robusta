from robusta.api import *


class DiskBenchmarkParams(BaseModel):
    pvc_name: str = "robusta-disk-benchmark"
    test_seconds: int = 20
    namespace: str = INSTALLATION_NAMESPACE
    disk_size: str = "10Gi"
    storage_class_name: str


def format_float_per2(f_param):
    return "{:.2f}".format(f_param)


@on_manual_trigger
def disk_benchmark(event: ManualTriggerEvent):

    action_params = DiskBenchmarkParams(**event.data)
    pvc = PersistentVolumeClaim(
        metadata=ObjectMeta(
            name=action_params.pvc_name, namespace=action_params.namespace
        ),
        spec=PersistentVolumeClaimSpec(
            accessModes=["ReadWriteOnce"],
            storageClassName=action_params.storage_class_name,
            resources=ResourceRequirements(
                requests={"storage": action_params.disk_size}
            ),
        ),
    )
    try:
        pvc.createNamespacedPersistentVolumeClaim(action_params.namespace)
        pv_name = "robusta-benchmark-pv"
        image = "us-central1-docker.pkg.dev/genuine-flight-317411/devel/robusta-fio-benchmark"
        name = "robusta-fio-disk-benchmark"
        mount_path = "/robusta/data"
        spec = PodSpec(
            volumes=[
                Volume(
                    name=pv_name,
                    persistentVolumeClaim=PersistentVolumeClaimVolumeSource(
                        claimName=action_params.pvc_name
                    ),
                )
            ],
            containers=[
                Container(
                    name=name,
                    image=image,
                    imagePullPolicy="Always",
                    volumeMounts=[VolumeMount(mountPath=mount_path, name=pv_name)],
                    args=[
                        "--directory",
                        mount_path,
                        "--output-format",
                        "json",
                        "--group_reporting",
                        "--runtime",
                        f"{action_params.test_seconds}",
                        "/jobs/rand-rw.fio",
                    ],
                )
            ],
            restartPolicy="Never",
        )

        json_output = json.loads(
            RobustaJob.run_simple_job_spec(
                spec, name, 120 + action_params.test_seconds
            ).replace("'", '"')
        )
        job = json_output["jobs"][0]

        logging.info(
            f"\nfio benchmark:\n"
            f"Total Time: {action_params.test_seconds} Sec\n"
            f"Read Band Width: {format_float_per2(job['read']['bw'])} KB \n"
            f"Read IO Ops/Sec: {format_float_per2(job['read']['iops'])}\n"
            f"Write Band Width: {format_float_per2(job['write']['bw'])} KB \n"
            f"Write Ops/Sec: {format_float_per2(job['write']['iops'])}\n "
        )

    finally:
        pvc.deleteNamespacedPersistentVolumeClaim(
            name=action_params.pvc_name, namespace=action_params.namespace
        )
