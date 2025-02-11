AWS
===

Security
--------

Set of tools to audit AWS cloudtrail events and audit logs.


Configuration
*************

.. code-block:: yaml

    holmes:
        additionalEnvVars:
            - name: AWS_ACCESS_KEY_ID
              value: AKIAIOSFODNN7EXAMPLE
            - name: AWS_SECRET_ACCESS_KEY
              value: =wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
            - name: AWS_DEFAULT_REGION
              value: us-west-2
        toolsets:
            aws/security:
                enabled: true

.. include:: ./_toolset_configuration.inc.rst

Capabilities
************
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - aws_cloudtrail_event_lookup
     - Fetches events of a specified type from AWS CloudTrail along with the users that called them
   * - aws_cloudtrail_event_details
     - Fetches and returns full event details for an AWS cloudtrail event in JSON format given an event ID
   * - aws_user_audit_logs
     - Fetches audit logs for a specified user from AWS CloudTrail in past 24 hours. Provide username as was outputed by aws_event_lookup or aws_event_details


RDS
---

Read access to Amazon RDS instances, events and logs

Configuration
************

.. code-block:: yaml

    holmes:
        additionalEnvVars:
            - name: AWS_ACCESS_KEY_ID
              value: AKIAIOSFODNN7EXAMPLE
            - name: AWS_SECRET_ACCESS_KEY
              value: =wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
            - name: AWS_DEFAULT_REGION
              value: us-west-2
        toolsets:
            aws/rds:
                enabled: true

.. include:: ./_toolset_configuration.inc.rst

Capabilities
************
.. include:: ./_toolset_capabilities.inc.rst

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool Name
     - Description
   * - aws_rds_describe_events
     - Fetches rds events
   * - aws_rds_describe_instance
     - Get the configuration of a RDS instance
   * - aws_rds_describe_instances
     - Fetches rds instances
   * - aws_rds_describe_logs
     - List available RDS logs (e.g. slow query logs)
   * - aws_rds_fetch_log_by_name
     - Fetch a specific log for an AWS RDS instance by log file name.
