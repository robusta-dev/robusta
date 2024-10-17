import os.path

from pydantic_settings import SettingsConfigDict, BaseSettings


# these settings are loaded from three sources:
# 1. defaults in the source code (lowest precedence)
# 2. the config.env file
# 3. environment variables (highest precedence)
class TestConfig(BaseSettings):
    PYTEST_SLACK_CHANNEL: str = "robusta-pytest"
    PYTEST_SLACK_DELETE_CHANNEL_AFTER_TEST: bool = False

    # this is used for unit tests and has high permissions
    PYTEST_SLACK_TOKEN: str

    # this is used by robusta-runner and should be a regular slack token with the same permissions as real
    # robusta slack tokens
    PYTEST_IN_CLUSTER_SLACK_TOKEN: str
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), "config.env"))


CONFIG = TestConfig()
