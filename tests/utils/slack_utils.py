import logging

from slack_sdk import WebClient


class SlackChannel:
    def __init__(self, token: str, channel_name: str):
        self.client = WebClient(token=token)
        self.channel_name = channel_name
        self.channel_id = self._create_or_join_channel(self.client, channel_name)

    def was_message_sent_recently(self, expected) -> bool:
        results = self.client.conversations_history(channel=self.channel_id, limit=4)
        messages = results["messages"]
        for msg in messages:
            if expected in msg["text"]:
                return True
        return False

    def get_latest_message(self):
        # Note: Prefer get_message_by_ts() to avoid race conditions when tests share a channel
        results = self.client.conversations_history(channel=self.channel_id)
        messages = results["messages"]
        return messages[0]["text"]

    def get_message_by_ts(self, ts: str) -> str | None:
        """Get message by timestamp - avoids race conditions unlike get_latest_message()."""
        results = self.client.conversations_history(
            channel=self.channel_id,
            latest=ts,
            oldest=ts,
            inclusive=True,
            limit=1
        )
        messages = results["messages"]
        return messages[0]["text"] if messages else None

    def get_complete_latest_message(self):
        results = self.client.conversations_history(channel=self.channel_id)
        messages = results["messages"]
        return messages[0]

    @staticmethod
    def _create_or_join_channel(client: WebClient, channel_name: str) -> str:
        """Creates or joins the specified slack channel and returns its channel_id"""
        for channel in client.conversations_list()["channels"]:
            if channel["name"] == channel_name:
                try:
                    # Attempt to join the channel if not already joined
                    client.conversations_join(channel=channel["id"])
                except Exception as e:
                    # It's ok if already in channel or can't join (e.g., private and no permission)
                    logging.warning(f"Could not join channel {channel_name}: {e}")
                return channel["id"]

        # TODO: make this a private channel not a public channel. it shouldn't be visible to anyone who joins the public
        # robusta workspace
        result = client.conversations_create(name=channel_name)
        return result["channel"]["id"]
