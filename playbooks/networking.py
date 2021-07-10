from robusta.api import *


class PingParams(BaseModel):
    hostname: str


@on_manual_trigger
def incluster_ping(event: ManualTriggerEvent):
    action_params = PingParams(**event.data)
    output = RobustaJob.run_simple_job(
        "nicolaka/netshoot", f"ping -c 1 {action_params.hostname}", 60
    )
    print("got output", output)
