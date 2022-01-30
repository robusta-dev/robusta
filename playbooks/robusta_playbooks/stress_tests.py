from robusta.api import *


class StressTestParams(ActionParams):
    """
    :var n: Number of requests to run.
    :var url: In cluster target url.
    """

    n: int = 1000
    url: str


@action
def http_stress_test(event: ExecutionBaseEvent, action_params: StressTestParams):
    """
    Run an http stress test and send the results
    """
    # TODO: remove timeout?
    output = RobustaJob.run_simple_job(
        "williamyeh/hey", f"/hey -n {action_params.n} {action_params.url}", 120
    )
    finding = Finding(
        title=f"Done running stress test with {action_params.n} http requests for url {action_params.url}",
        source=FindingSource.MANUAL,
        aggregation_key="http_stress_test",
    )
    if output:
        finding.add_enrichment([FileBlock("result.txt", output)])
    event.add_finding(finding)
