Main Features
=============

Robusta integrates `HolmesGPT <https://github.com/robusta-dev/holmesgpt>`_ to provide AI-powered root cause analysis for Kubernetes alerts and issues.

See HolmesGPT in Action
-----------------------

.. tab-set::

   .. tab-item:: AWS Troubleshooting

      .. raw:: html

         <div style="position: relative; padding-bottom: 56.25%; height: 0;">
            <iframe src="https://www.loom.com/embed/2e5e3a259a5c41018914c9abd8429f00"
                    frameborder="0"
                    webkitallowfullscreen
                    mozallowfullscreen
                    allowfullscreen
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
            </iframe>
         </div>

   .. tab-item:: CPU Spike Investigation

      .. raw:: html

         <div style="position: relative; padding-bottom: 56.25%; height: 0;">
            <iframe src="https://www.loom.com/embed/b63f0eba0fd74750929f37c16b3fca3b"
                    frameborder="0"
                    webkitallowfullscreen
                    mozallowfullscreen
                    allowfullscreen
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
            </iframe>
         </div>

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

Next Steps
----------

* :doc:`getting-started` - Set up HolmesGPT in 5 minutes
* `Available Data Sources <https://holmesgpt.dev/data-sources/builtin-toolsets/>`_ - See all supported integrations (use Robusta Helm Chart configuration method)
* `Helm Configuration Reference <https://holmesgpt.dev/reference/helm-configuration/>`_ - Advanced HolmesGPT settings for Robusta deployments