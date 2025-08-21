Main Features
=============

Robusta integrates `HolmesGPT <https://github.com/robusta-dev/holmesgpt>`_ to provide AI-powered root cause analysis for Kubernetes alerts and issues.

What HolmesGPT Does
-------------------

**Automatic Investigation**
   When alerts fire, HolmesGPT automatically:
   
   * Analyzes pod logs and events
   * Examines resource metrics and limits
   * Checks recent deployments and changes
   * Investigates related resources and dependencies
   * Provides actionable recommendations

**Multi-Source Analysis**
   HolmesGPT pulls data from:
   
   * Kubernetes API (pods, nodes, events, logs)
   * Prometheus metrics
   * Cloud provider APIs (AWS, Azure, GCP)
   * Application monitoring (Datadog, New Relic)
   * Log aggregation systems (Loki, OpenSearch, Coralogix)
   * And more via `extensible toolsets <https://holmesgpt.dev/data-sources/builtin-toolsets/>`_

How to Use It
-------------

**In Robusta UI**
   Click the ``Root Cause`` tab on any alert to see the AI investigation.

   .. image:: /images/ai-root-causeanalysis.png
       :width: 600px

**Via @holmes in Slack**
   Ask natural language questions about your clusters:
   
   * ``@holmes what apps are crashing in prod-cluster?``
   * ``@holmes why is my alert firing on staging?``
   * ``@holmes investigate high memory usage in dev-cluster``

Example Investigation
---------------------

Here's what HolmesGPT found for a CrashLoopBackOff alert:

.. image:: /images/AI_Analysis_demo2.png
    :width: 1000px

The AI identified:
- The exact error from pod logs
- The root cause (missing environment variable)
- Recommended fix with example YAML
- Related configuration issues

Why Use HolmesGPT?
------------------

**Save Time**
   Stop manually checking logs, metrics, and events across multiple tools. HolmesGPT does it in seconds.

**Reduce MTTR**
   Get to root cause faster with AI that understands Kubernetes patterns and common issues.

**Learn as You Go**
   Each investigation explains what was checked and why, helping your team learn Kubernetes troubleshooting.

**24/7 Coverage**
   AI investigations run automatically on every alert, even at 3 AM.

Next Steps
----------

* :doc:`getting-started` - Set up HolmesGPT in 5 minutes
* `HolmesGPT Documentation <https://holmesgpt.dev>`_ - Advanced configuration and customization
* `Available Data Sources <https://holmesgpt.dev/data-sources/builtin-toolsets/>`_ - See all supported integrations