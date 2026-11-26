import logging

from robusta.api import ActionParams, ExecutionBaseEvent, action


class EchoParams(ActionParams):
    message: str


@action
def echo(event: ExecutionBaseEvent, params: EchoParams):
    logging.warning(f"echo: {params.message}")
