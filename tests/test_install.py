import time
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel
from tests.utils.kubernetes_utils import create_crashing_deployment


def test_robusta_install(robusta: RobustaController, slack_channel: SlackChannel):
    crashing_deployment = create_crashing_deployment()
    try:
        expected = f"Crashing pod {crashing_deployment.metadata.name}"
        for _ in range(50):
            time.sleep(10)
            if slack_channel.was_message_sent_recently(expected):
                return
        assert False, f"cannot find expected='{expected} msg in slack"
    finally:
        crashing_deployment.delete()
