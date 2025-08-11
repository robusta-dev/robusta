Sending Alerts to the Robusta UI
=================================

Why Send Your Alerts to Robusta?
---------------------------------

Benefits include:

* Persistent alert history on a filterable timeline
* Centralized view of alerts from all your monitoring systems (multiple Prometheus instances, cloud services, custom tools)
* AI investigation of alerts
* Correlations between alerts and Kubernetes deploys
* and more!

.. image:: /images/robusta-ui-timeline.png
   :alt: Prometheus Alert History

Setting Up Alert Integration
-----------------------------

To configure alert integration with your monitoring system, see :doc:`Alert Sources <index>`.

Common Troubleshooting Scenarios
---------------------------------

.. tab-set::

    .. tab-item:: General Issues

        **Not receiving alerts in Robusta UI?**

        1. **Just installed?** Wait 10 minutes after installation for all components to initialize
        2. **Check your specific integration:** Each alert source has its own troubleshooting guide on its documentation page
        3. **Verify authentication:** Ensure API keys and webhook URLs are correctly configured

        **Need to test your integration?**

        Refer to your specific alert source documentation for testing procedures.

    .. tab-item:: AlertManager

        **Not receiving alerts?**

        1. **Verify routing configuration:**
           
           - Ensure Robusta is the first receiver in your AlertManager configuration, or
           - All previous receivers have ``continue: true`` set
           - See configuration examples in your specific alert source documentation

        2. **Check logs for errors:**
           
           - Review AlertManager logs for webhook errors
           - Check Prometheus Operator logs (if using kube-prometheus-stack)
           - Look for errors in Robusta runner logs

        3. **Check pod health (embedded Prometheus stack):**
           
           - Verify all Prometheus and AlertManager pods are running
           - Look for OOMKills and increase memory limits if needed
           - See :doc:`Embedded Prometheus troubleshooting <embedded-prometheus>`

        4. **Verify network connectivity (external AlertManager):**
           
           - Test connectivity to Robusta webhook endpoint
           - Check firewall rules and network policies
           - Ensure AlertManager can resolve DNS names

        **Alerts arriving but missing Kubernetes context?**

        Check :doc:`Alert Label Mapping </setup-robusta/additional-settings>` to customize how Prometheus labels map to Kubernetes resources.


Testing Your Integration
------------------------

Each alert source has specific testing methods:

* **Standard AlertManager**: Use ``robusta demo-alert`` command
* **Cloud Services**: Check the specific service's documentation for test procedures
* **Custom Systems**: Use the test features built into your monitoring platform

Refer to your specific integration documentation for detailed testing steps.

Need More Help?
---------------

* Check your specific alert source documentation for detailed troubleshooting
* Review logs in AlertManager, Prometheus Operator (if applicable), and Robusta runner
* Join our `Slack community <https://bit.ly/robusta-slack>`_ for direct support