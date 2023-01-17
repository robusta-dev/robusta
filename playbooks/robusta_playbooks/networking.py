from robusta.api import ActionParams, ExecutionBaseEvent, FileBlock, RobustaJob, action


class PingParams(ActionParams):
    """
    :var hostname: Ping target host name.
    """

    hostname: str


@action
def incluster_ping(event: ExecutionBaseEvent, action_params: PingParams):
    """
    Check network connectivity in your cluster using ping.
    Pings a hostname from within the cluster
    """
    output = RobustaJob.run_simple_job("nicolaka/netshoot", f"ping -c 1 {action_params.hostname}", 60)
    event.add_enrichment([FileBlock(f"ping-{action_params.hostname}.txt", output.encode())])
