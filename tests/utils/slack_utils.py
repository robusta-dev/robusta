from slack_sdk import WebClient


class SlackChannel:
    def __init__(self, token: str, channel_name: str):
        self.client = WebClient(token=token)
        self.channel_name = channel_name
        self.channel_id = self._create_or_join_channel(self.client, channel_name)

    def get_latest_messages(self):
        results = self.client.conversations_history(channel=self.channel_id)
        messages = results["messages"]
        return messages[0]["text"]

    @staticmethod
    def _create_or_join_channel(client: WebClient, channel_name: str) -> str:
        """Creates or joins the specified slack channel and returns its channel_id"""
        for channel in client.conversations_list()["channels"]:
            if channel["name"] == channel_name:
                # TODO: join the channel if necessary
                return channel["id"]

        # TODO: make this a private channel not a public channel. it shouldn't be visible to anyone who joins the public
        # robusta workspace
        result = client.conversations_create(name=channel_name)
        return result["channel"]["id"]
