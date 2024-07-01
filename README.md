<div id="top"></div>

<div align="center">
  <h1 align="center">Robusta - Better Prometheus Alerts (and more) for Kubernetes</h1>
  <h2 align="center">Enrich, Group, and Remediate your Alerts</h2>
  <p align="center">
    <a href="#%EF%B8%8F-how-it-works"><strong>How it Works</strong></a> |
    <a href="#-installing-robusta"><strong>Installation</strong></a> | 
    <a href="[https://docs.robusta.dev/master/configuration/index.html"><strong>Integrations ↗</strong></a> |
    <a href="https://docs.robusta.dev/master/index.html"><strong>Docs ↗</strong></a> |
    <a href="https://bit.ly/robusta-slack"><strong>Slack Community ↗</strong></a>
  </p>
</div>

## What Can Robusta Do?

Robusta integrates with Prometheus (e.g. `kube-prometheus-stack` or Coralogix) by webhook and adds features like: 

* [**Smart Grouping**](https://docs.robusta.dev/master/configuration/notification-grouping.html) - reduce notification spam with Slack threads 🧵
* *[*AI Investigation**](https://docs.robusta.dev/master/configuration/ai-analysis.html#ai-analysis) -  Kickstart alert investigation with AI (optional)
* [**Alert Enrichment**](https://docs.robusta.dev/master/how-it-works/index.html#automatically-investigate-a-prometheus-alert) - see pod logs and other data alongside your alerts
* [**Self-Healing**](https://docs.robusta.dev/master/tutorials/alert-remediation.html#remediate-prometheus-alerts) - define auto-remediation rules for faster fixes
* [**Advanced Routing**](https://docs.robusta.dev/master/tutorials/index.html#notification-routing) based on team, namespace, and more
* [**Problem-Detection without PromQL**](https://docs.robusta.dev/master/playbook-reference/triggers/index.html#triggers-reference) - generate Kubernetes-native alerts for OOMKills, failing Jobs, and more
* [**Change-Tracking**](https://docs.robusta.dev/master/tutorials/playbook-track-changes.html#track-kubernetes-changes) for Kubernetes Resources to correlate alerts and rollouts
* [**Auto-Resolve**](https://docs.robusta.dev/master/configuration/sinks/jira.html#jira) - update external systems when alerts are resolved (e.g. Jira)
* [**Dozens of Integrations**](https://docs.robusta.dev/master/configuration/index.html#integrations-overview) - Slack, Teams, Jira, and more

Don't have Prometheus? You can use Robusta without Prometheus, or install our all-in-one Kubernetes observability stack with Robusta and Prometheus included.

## 🛠️ How it works

Robusta is powered by a rule engine that takes incoming events (e.g. Prometheus alerts) and runs actions on them to gather more information or remediate problems. 

Here is an example rule that adds Pod logs to the `KubePodCrashLooping` alert from Prometheus:

```yaml
triggers:
  - on_prometheus_alert:
      alert_name: KubePodCrashLooping
actions:
  - logs_enricher: {}
```

The resulting alert looks like this in Slack:

![](./docs/images/crash-report.png)

When performing auto-remediation, you can configure 100% automation, or semi-automatic mode that requires user confirmation:

![](./docs/images/alert_on_hpa_reached_limit1.png)

[Learn more »](https://docs.robusta.dev/master/how-it-works/index.html)

<p align="right">(<a href="#top">back to top</a>)</p>

## 📒 Installing Robusta

Robusta is installed with Helm. For convenience, we provide a CLI wizard to generate Helm values.

You can install Robusta alongside your existing Prometheus, or as an all-in-one bundle with Robusta and a preconfigured `kube-prometheus-stack`.

[Installation instructions »](https://docs.robusta.dev/master/setup-robusta/installation/index.html)

<!-- <p align="right">(<a href="#top">back to top</a>)</p> -->

## 📝 Documentation
Interested? Learn more about Robusta.

[Full documentation »](https://docs.robusta.dev/master/index.html)
<p align="right">(<a href="#top">back to top</a>)</p>

## ✉️ Contact

* Slack - [robustacommunity.slack.com](https://bit.ly/robusta-slack)
* Twitter - [@RobustaDev](https://twitter.com/RobustaDev)
* LinkedIn - [robusta-dev](https://www.linkedin.com/company/robusta-dev/)
* Email Support - [support@robusta.dev ](mailto:support@robusta.dev )

<p align="right">(<a href="#top">back to top</a>)</p>

## 📑 License
Robusta is distributed under the MIT License. See [LICENSE.md](https://github.com/robusta-dev/robusta/blob/master/LICENSE) for more information.

## 🕐 Stay up to date
We add new features regularly. Stay up to date by watching us on GitHub.

![](./docs/images/star-repo.gif)
