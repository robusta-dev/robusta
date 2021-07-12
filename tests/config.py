import os.path
from pydantic import BaseSettings


# these settings are loaded from three sources:
# 1. defaults in the source code (lowest precedence)
# 2. the config.env file
# 3. environment variables (highest precedence)
class TestConfig(BaseSettings):
    PYTEST_SLACK_TOKEN: str
    PYTEST_SLACK_CHANNEL: str = "robusta-pytest"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "config.env")


CONFIG = TestConfig()
