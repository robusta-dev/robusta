AWS
=====

Security
--------

Set of tools to audit AWS cloudtrail events and audit logs.


Configuration
***************


.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

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

  .. md-tab-item:: Holmes CLI


    First, add the following environment vairables:

    .. code-block:: yaml

      export AWS_ACCESS_KEY_ID="<your AWS access key ID>"
      export AWS_SECRET_ACCESS_KEY="<your AWS secret access key>"
      export AWS_DEFAULT_REGION="us-west-2"


    Then, add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
          aws/security:
              enabled: true


    To test, run: 

    .. code-block:: yaml
      
        holmes ask "Are there any security misconfigurations my signup application, particularly in the database?"

Capabilities
**************
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
----

Read access to Amazon RDS instances, events and logs

Configuration
****************

.. md-tab-set::

  .. md-tab-item:: Robusta Helm Chart

    .. code-block:: yaml

        holmes:
            additionalEnvVars:
                - name: AWS_ACCESS_KEY_ID
                  value: AKIXDDDSDSdSA
                - name: AWS_SECRET_ACCESS_KEY
                  value: =wJalrXUtnFEMI/KNG/bPxRfiCYEXAMPLEKEY
                - name: AWS_DEFAULT_REGION
                  value: us-west-2
            toolsets:
                aws/rds:
                    enabled: true

    .. include:: ./_toolset_configuration.inc.rst

  .. md-tab-item:: Holmes CLI

    First, add the following environment vairables:

    .. code-block:: yaml

      export AWS_ACCESS_KEY_ID="<your AWS access key ID>"
      export AWS_SECRET_ACCESS_KEY="<your AWS secret access key>"
      export AWS_DEFAULT_REGION="us-west-2"

    Then, add the following to **~/.holmes/config.yaml**, creating the file if it doesn't exist:

    .. code-block:: yaml

      toolsets:
          aws/rds:
              enabled: true

    To test, run: 

    .. code-block:: yaml
      
        holmes ask "Why is my signup application slow, also look into the database"


Capabilities
*************

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
