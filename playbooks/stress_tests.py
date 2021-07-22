from robusta.api import *


class StressTestParams(BaseModel):
    n: int = 1000
    url: str


@on_manual_trigger
def http_stress_test(event: ManualTriggerEvent):
    action_params = StressTestParams(**event.data)
    # TODO: remove timeout?
    output = RobustaJob.run_simple_job(
        "williamyeh/hey", f"/hey -n {action_params.n} {action_params.url}", 120
    )
    event.processing_context.create_finding(
        title=f"Done running stress test with {action_params.n} http requests for url {action_params.url}",
        source=SOURCE_MANUAL,
        type=TYPE_CHAOS_STRESS,
    )
    event.processing_context.finding.add_enrichment([FileBlock("result.txt", output)])
