from typing import Optional
from pydantic import BaseModel, Field
from robusta.core.model.base_params import ActionParams


class DelayedNotificationConfig(BaseModel):
    """
    Configuration for delayed notifications
    :var delay_seconds: Number of seconds to delay the notification
    :var condition: Optional condition that must be met for the delay to apply
    """
    delay_seconds: int = Field(ge=0, description="Number of seconds to delay the notification")
    condition: Optional[str] = Field(None, description="Optional condition for applying the delay")


class SinkBaseParams(ActionParams):
    """
    Base class for all sink configurations
    """
    name: str
    notification_delay_seconds: Optional[int] = Field(None, ge=0, description="Delay notification by specified seconds")
    delayed_notification_config: Optional[DelayedNotificationConfig] = Field(
        None, description="Advanced delayed notification configuration"
    )

    def get_delay_seconds(self) -> int:
        """Get the effective delay in seconds"""
        if self.delayed_notification_config:
            return self.delayed_notification_config.delay_seconds
        return self.notification_delay_seconds or 0