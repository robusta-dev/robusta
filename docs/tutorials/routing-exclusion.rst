Routing with Exclusion Rules
=============================

This guide defines a sink that receives all notifications *except* for something specific.

To drop a specific notification altogether, see :ref:`Silencing Alerts`.

Using Matchers to Exclude Alerts
------------------------------------------------

To excluding notifications from a sink, define a matcher with a "negative lookahead regex":

For example, we can exclude notifications related to pods and deployments:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: other_slack_sink
        slack_channel: no-pods-or-deployments
        api_key: secret-key
        match:
          # match all notifications EXCEPT for those related to pods and deployments
          # this uses negative-lookahead regexes as well as regex OR
          kind: ^(?!(pod)|(deployment))

.. include:: _routing-further-reading.rst

Further Reading
------------------

