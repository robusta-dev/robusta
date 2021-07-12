from robusta.api import get_slack_client


# TODO: make this a private channel not a public channel. it shouldn't be visible to anyone who joins the public
# robusta workspace
def create_or_join_channel(name: str) -> str:
    """Creates or joins the specified slack channel and returns its channel_id"""
    client = get_slack_client()
    for channel in client.conversations_list()["channels"]:
        if channel["name"] == name:
            # TODO: join the channel if necessary
            return channel["id"]

    result = client.conversations_create(name=name)
    return result["channel"]["id"]


def get_latest_message(channel_id: str) -> str:
    client = get_slack_client()
    results = client.conversations_history(channel=channel_id)
    messages = results["messages"]
    return messages[0]["text"]
