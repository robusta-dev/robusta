from robusta.api import *


class StressTestParams (BaseModel):
    slack_channel: str
    n: int = 1000
    url: str

@on_manual_trigger
def http_stress_test(event: ManualTriggerEvent):
    action_params = StressTestParams(**event.data)
    # TODO: remove timeout?
    output = RobustaJob.run_simple_job("williamyeh/hey", f"/hey -n {action_params.n} {action_params.url}", 120)
    event.slack_channel = action_params.slack_channel
    event.report_title = f"Done running stress test with {action_params.n} http requests for url {action_params.url}"
    event.report_blocks.append(FileBlock("result.txt", output))
    send_to_slack(event)
