import time
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel
from tests.utils.kubernetes_utils import get_crashing_deployment

# TODO: test multiple KIND versions
# TODO: verify that cli install command is backwards compatible by testing old robusta versions


def test_robusta_install(robusta: RobustaController, slack_channel: SlackChannel):
    crashing_deployment = get_crashing_deployment(robusta.namespace)
    crashing_deployment.client = robusta.get_client()
    crashing_deployment.create()
    msg = ""
    expected = f"Crashing pod {crashing_deployment.metadata.name}"
    for _ in range(10):
        time.sleep(10)
        msg = slack_channel.get_latest_messages()
        if expected in msg:
            break
    assert expected in msg, f"cannot find expected='{expected} in msg='{msg}'"
