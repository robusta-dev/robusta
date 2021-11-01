Elasticsearch Integration
#########################

Robusta playbooks can run in response to `Elasticsearch/Kibana watchers <https://www.elastic.co/guide/en/elasticsearch/reference/current/how-watcher-works.html>`_
by using `webhook actions <https://www.elastic.co/guide/en/elasticsearch/reference/current/actions-webhook.html>`_.

A common use case is gathering troubleshooting data with Robusta when pods in your Kubernetes cluster write specific error logs.

Robusta Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. The Robusta-relay must be enabled so that it can route Elasticsearch webhooks to the appropriate Robusta runner
2. The following variables must be defined in your Helm values file:

.. code-block:: yaml

    globalConfig:
      account_id: ""       # your official Robusta account_id
      signing_key: ""      # a secret key used to verify the identity of Elasticsearch

Example Elasticsearch Watcher
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Elasticsearch Watcher configuration will trigger a Robusta playbook.
Make sure you update ``<account_id>``, ``<cluster_name>``, and ``<secret_key>`` in the emphasized line.
These should match the same values you define in the Robusta Helm chart.

.. code-block:: json
   :emphasize-lines: 24

    {
      "trigger": {
        "schedule": {
          "interval": "30m"
        }
      },
      "input": {
        "simple": {
          "str": "val1",
          "obj": {
            "str": "val2"
          },
          "num": 23
        }
      },
      "condition": {
        "always": {}
      },
      "actions": {
        "robusta_webhook": {
          "throttle_period_in_millis": 0,
          "transform": {
            "script": {
              "source": "return ['body' : ['account_id' : '<account_id>', 'cluster_name' : '<cluster_name>', 'action_name' : 'echo', 'action_params' : ['message' : 'Hello Robusta!'], 'sinks' : ['slack sink'], 'origin' : 'elasticsearch'], 'key' : '<secret_key>']",
              "lang": "painless"
            }
          },
          "webhook": {
            "scheme": "https",
            "host": "robusta.dev",
            "port": 443,
            "method": "post",
            "path": "/integrations/generic/actions_with_key",
            "params": {},
            "headers": {},
            "body": "{{#toJson}}ctx.payload{{/toJson}}"
          }
        }
      }
    }