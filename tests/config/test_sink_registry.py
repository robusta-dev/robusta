import yaml

from robusta.core.model.runner_config import RunnerConfig
from robusta.model.config import Registry, SinksRegistry


CONFIG = """
playbook_repos:
  chatgpt_robusta_actions:
    url: "file:///path/to/kubernetes-chatgpt-bot"
sinks_config:
  - mail_sink:
      name: my_sink1
      mailto: "mailtos://user:password@example.com?from=a@x&to=b@y"

  - mail_sink:
      name: my_sink2
      mailto: "mailtos://user:password@example.com?from=a@x&to=b@y"
"""

class TestSinkFactory:

  def setup_method(self, method):
      self.config_data = yaml.safe_load(CONFIG)
      self.runner_config = RunnerConfig(**self.config_data)
      self.registry = Registry()
      new_sinks, _ = SinksRegistry.construct_new_sinks(self.runner_config.sinks_config, {}, self.registry)
      self.sinks_registry = SinksRegistry(new_sinks)


  def test_create_sinks(self):
      assert list(self.sinks_registry.sinks.keys()) == ["my_sink1", "my_sink2"]


  def test_delete_sinks(self):
      del self.runner_config.sinks_config[0]
      new_sinks, _ = SinksRegistry.construct_new_sinks(self.runner_config.sinks_config, self.sinks_registry.sinks, self.registry)
      assert list(new_sinks.keys()) == ["my_sink2"]

      
  def test_add_new_sinks(self):
      self.config_data["sinks_config"].insert(1, {'mail_sink': {'name': 'my_sink3', 'mailto': 'mailtos://user:password@example.com?from=a@x&to=b@y'}})
      self.runner_config = RunnerConfig(**self.config_data)
      new_sinks, _ = SinksRegistry.construct_new_sinks(self.runner_config.sinks_config, self.sinks_registry.sinks, self.registry)
      assert list(new_sinks.keys()) == ["my_sink1", "my_sink3", "my_sink2"]


  def test_sink_config_changed(self):
      new_email = "dev@robusta.dev"
      self.runner_config.sinks_config[0].mail_sink.mailto = new_email
      new_sinks, _ = SinksRegistry.construct_new_sinks(self.runner_config.sinks_config, self.sinks_registry.sinks, self.registry)
      assert new_sinks["my_sink1"].params.mailto == new_email
      assert list(new_sinks.keys()) == ["my_sink1", "my_sink2"]
