:hide-toc:

Custom Alert Enrichment
==============================

Ever feel overwhelmed by Prometheus alerts that lack context? In this section, you will learn to enrich alerts with deterministic rules using Robusta.

.. note::

   **Looking for automatic AI enrichment?** Check out :doc:`HolmesGPT </configuration/holmesgpt/main-features>` for zero-configuration AI-powered alert enrichment that automatically investigates alerts and provides root cause analysis.

By creating custom enrichment rules, you can:

* Reduce mean time to resolution (MTTR) by automatically gathering system state and logs when alerts fire
* Make faster decisions on which team needs to investigate the alert
* Link alerts to runbooks and documentation, to improve knowledge sharing

Get started:

.. toctree::
   :maxdepth: 1

   bash-alert-enrichment
   link-alert-enrichment
