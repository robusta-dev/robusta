import pytest
import yaml
import os
from pydantic import ValidationError
from robusta.core.model.runner_config import RunnerConfig

FIXTURES = os.path.join(os.path.dirname(__file__), "file_fixtures", "config_validation")
FIXTURE_VALID_CONFIG_FILE_PATH = os.path.join(FIXTURES, "valid_config.yaml")
FIXTURE_DUPL_SINKS_NAME_FILE_PATH = os.path.join(FIXTURES, "invalid_dupl_sink_names.yaml")

class TestSinkValidation:

    def test_valid_sink_config(self):
        with open(FIXTURE_VALID_CONFIG_FILE_PATH) as file:
            yaml_content = yaml.safe_load(file)
            config = RunnerConfig(**yaml_content)

    def test_duplicate_sink_names(self):
        with open(FIXTURE_DUPL_SINKS_NAME_FILE_PATH) as file:
            yaml_content = yaml.safe_load(file)
            with pytest.raises(ValidationError) as validation_error:
                config = RunnerConfig(**yaml_content)
            assert "sink name".casefold() in str(validation_error).casefold()
            assert "unique".casefold() in str(validation_error).casefold()
