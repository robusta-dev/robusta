<div id="top"></div>

<div align="center">
  <h1 align="center">Robusta - Better Prometheus Notifications for Kubernetes</h1>
  <h2 align="center">Better grouping, enrichment, and remediation of your existing alerts</h2>
  <p align="center">
    <a href="#%EF%B8%8F-how-it-works"><strong>How it Works</strong></a> |
    <a href="#-installing-robusta"><strong>Installation</strong></a> |
    <a href="https://docs.robusta.dev/master/configuration/index.html"><strong>Integrations ↗</strong></a> |
    <a href="https://docs.robusta.dev/master/index.html"><strong>Docs ↗</strong></a> |
    <a href="https://bit.ly/robusta-slack"><strong>Slack Community ↗</strong></a>
  </p>
</div>

## What Can Robusta Do?

Compatible with kube-prometheus-stack, Prometheus Operator, and more.

Robusta integrates with Prometheus by webhook and adds features like:

* [**Smart Grouping**](https://docs.robusta.dev/master/configuration/notification-grouping.html) - reduce notification spam with Slack threads 🧵
* [**AI Investigation**](https://docs.robusta.dev/master/configuration/holmesgpt/index.html#ai-analysis) -  Kickstart alert investigation with AI (optional)
* [**Alert Enrichment**](https://docs.robusta.dev/master/how-it-works/index.html#automatically-investigate-a-prometheus-alert) - see pod logs and other data alongside your alerts
* [**Self-Healing**](https://docs.robusta.dev/master/tutorials/alert-remediation.html#remediate-prometheus-alerts) - define auto-remediation rules for faster fixes
* [**Advanced Routing**](https://docs.robusta.dev/master/notification-routing/configuring-sinks.html) based on team, namespace, and more
* [**Problem-Detection without PromQL**](https://docs.robusta.dev/master/playbook-reference/triggers/index.html#triggers-reference) - generate Kubernetes-native alerts for OOMKills, failing Jobs, and more
* [**Change-Tracking**](https://docs.robusta.dev/master/tutorials/playbook-track-changes.html#track-kubernetes-changes) for Kubernetes Resources to correlate alerts and rollouts
* [**Auto-Resolve**](https://docs.robusta.dev/master/configuration/sinks/jira.html#jira) - update external systems when alerts are resolved (e.g. Jira)
* [**Dozens of Integrations**](https://docs.robusta.dev/master/configuration/index.html#integrations-overview) - Slack, Teams, Jira, and more

Don't have Prometheus? You can use Robusta without Prometheus, or install our all-in-one Kubernetes observability stack with Robusta and Prometheus included.

## 🔗 Integrations

Robusta integrates with a variety of tools and platforms. Click on any logo to learn more about the integration.

### 📤 Notification Destinations

<table>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/slack.html">
        <img src="./docs/images/integration_logos/slack-icon.png" alt="Slack" width="40">
        <br><strong>Slack</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/ms-teams.html">
        <img src="./docs/images/integration_logos/teams-icon.png" alt="MS Teams" width="40">
        <br><strong>MS Teams</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/discord.html">
        <img src="./docs/images/integration_logos/discord-icon.png" alt="Discord" width="40">
        <br><strong>Discord</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/telegram.html">
        <img src="./docs/images/integration_logos/telegram-icon.png" alt="Telegram" width="40">
        <br><strong>Telegram</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/google_chat.html">
        <img src="./docs/images/integration_logos/google_chat-icon.png" alt="Google Chat" width="40">
        <br><strong>Google Chat</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/mattermost.html">
        <img src="./docs/images/integration_logos/mattermost-icon.png" alt="Mattermost" width="40">
        <br><strong>Mattermost</strong>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/PagerDuty.html">
        <img src="./docs/images/integration_logos/pagerduty-icon.png" alt="PagerDuty" width="40">
        <br><strong>PagerDuty</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/Opsgenie.html">
        <img src="./docs/images/integration_logos/opsgenie-icon.png" alt="Opsgenie" width="40">
        <br><strong>Opsgenie</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/jira.html">
        <img src="./docs/images/integration_logos/jira-icon.png" alt="Jira" width="40">
        <br><strong>Jira</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/ServiceNow.html">
        <img src="./docs/images/integration_logos/servicenow-icon.png" alt="ServiceNow" width="40">
        <br><strong>ServiceNow</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/mail.html">
        <img src="./docs/images/integration_logos/smtp-logo.png" alt="Email" width="40">
        <br><strong>Email</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/webhook.html">
        <img src="./docs/images/integration_logos/webhook-icon.png" alt="Webhook" width="40">
        <br><strong>Webhook</strong>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/DataDog.html">
        <img src="./docs/images/integration_logos/datadog-icon.png" alt="DataDog" width="40">
        <br><strong>DataDog</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/VictorOps.html">
        <img src="./docs/images/integration_logos/victorops-logo.svg" alt="VictorOps" width="40">
        <br><strong>VictorOps</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/rocketchat.html">
        <img src="./docs/images/integration_logos/rocketchat-logo.svg" alt="Rocket.Chat" width="40">
        <br><strong>Rocket.Chat</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/webex.html">
        <img src="./docs/images/integration_logos/webex-logo.png" alt="Webex" width="40">
        <br><strong>Webex</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/pushover.html">
        <img src="./docs/images/integration_logos/pushover-icon.png" alt="Pushover" width="40">
        <br><strong>Pushover</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/zulip.html">
        <img src="https://zulip.com/static/images/logo/zulip-icon-128x128.png" alt="Zulip" width="40">
        <br><strong>Zulip</strong>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/RobustaUI.html">
        <img src="./logos/logo-only.png" alt="Robusta UI" width="40">
        <br><strong>Robusta UI</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/kafka.html">
        <img src="./docs/images/integration_logos/kafka-logo.png" alt="Kafka" width="40">
        <br><strong>Kafka</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/file.html">
        <img src="./docs/images/integration_logos/file-icon.svg" alt="File" width="40">
        <br><strong>File</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/sinks/YandexMessenger.html">
        <img src="./docs/images/integration_logos/yandex-logo.svg" alt="Yandex Messenger" width="40">
        <br><strong>Yandex Messenger</strong>
      </a>
    </td>
  </tr>
</table>

### 📊 Metrics and Alerts

<table>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/alert-manager.html">
        <img src="./docs/images/integration_logos/prometheus-icon.png" alt="Prometheus" width="40">
        <br><strong>Prometheus</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/victoria-metrics.html">
        <img src="./docs/images/integration_logos/victoriametrics-logo.png" alt="Victoria Metrics" width="40">
        <br><strong>Victoria Metrics</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/grafana-alert-manager.html">
        <img src="./docs/images/integration_logos/grafana-icon.png" alt="Grafana" width="40">
        <br><strong>Grafana Alertmanager</strong>
      </a>
    </td>
    <!-- <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/embedded-prometheus.rst">
        <img src="./docs/images/integration_logos/prometheus-icon.png" alt="kube-prometheus-stack" width="40">
        <br><strong>kube-prometheus-stack</strong>
      </a>
    </td> -->
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/outofcluster-prometheus.rst">
        <img src="./docs/images/integration_logos/thanos-logo.svg" alt="Thanos" width="40">
        <br><strong>Thanos</strong>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/aws-managed-prometheus.html">
        <img src="./docs/images/integration_logos/aws-managed-prometheus-logo.svg" alt="AWS Managed Prometheus" width="40">
        <br><strong>AWS Managed Prometheus</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/google-managed-prometheus.html">
        <img src="./docs/images/integration_logos/gcpmonitoring-icon.png" alt="Google Managed Prometheus" width="40">
        <br><strong>Google Managed Prometheus</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/azure-managed-prometheus.html">
        <img src="./docs/images/integration_logos/azure-managed-prometheus.png" alt="Azure Managed Prometheus" width="40">
        <br><strong>Azure Managed Prometheus</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/coralogix_managed_prometheus.html">
        <img src="./docs/images/integration_logos/coralogix-icon.png" alt="Coralogix" width="40">
        <br><strong>Coralogix</strong>
      </a>
    </td>
  </tr>
</table>

### 🧠 AI-Powered Alert Enrichement

<table>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/holmesgpt/index.html">
        <img src="https://raw.githubusercontent.com/robusta-dev/holmesgpt/refs/heads/master/images/logo.png" alt="HolmesGPT" width="40">
        <br><strong>HolmesGPT</strong>
      </a>
    </td>
  </tr>
</table>

### 💰 Cost Management

<table>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/resource-recommender.html">
        <img src="./docs/images/integration_logos/kubernetes-icon.png" alt="KRR" width="40">
        <br><strong>KRR (Kubernetes Resource Recommender)</strong>
      </a>
    </td>
  </tr>
</table>

<p align="right">(<a href="#top">back to top</a>)</p>

## 🛠️ How it works

Robusta uses rules and AI to take Prometheus alerts and add extra information to them, such as pod logs, relevant graphs, possible remediations, and more.

Here is an example alert in Slack:

![](./docs/images/crash-report.png)

Here is an example remediation action:

![](./docs/images/alert_on_hpa_reached_limit1.png)

[Learn more »](https://docs.robusta.dev/master/how-it-works/index.html)

<p align="right">(<a href="#top">back to top</a>)</p>

## 📒 Installing Robusta

Robusta is installed with Helm. For convenience, we provide a CLI wizard to generate Helm values.

You can install Robusta alongside your existing Prometheus, or as an all-in-one bundle with Robusta and a preconfigured `kube-prometheus-stack`.

To get *even more* out of Robusta, we recommend creating [a free Robusta UI account](#-free-robusta-ui). Learn more below.

[Create a free Robusta UI account »](https://platform.robusta.dev/signup?utm_source=github&utm_medium=robusta-readme&utm_content=installing_robusta_section)

[Installation instructions »](https://docs.robusta.dev/master/setup-robusta/installation/index.html)


<!-- ### 🌩️ Installation Options -->

<!-- <table>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/eks-managed-prometheus.html">
        <img src="./docs/images/integration_logos/eks-icon.png" alt="AWS EKS" width="40">
        <br><strong>AWS EKS</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/google-managed-prometheus.html">
        <img src="./docs/images/integration_logos/gke-icon.png" alt="Google GKE" width="40">
        <br><strong>Google GKE</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/configuration/alertmanager-integration/azure-managed-prometheus.html">
        <img src="./docs/images/integration_logos/aks-icon.png" alt="Azure AKS" width="40">
        <br><strong>Azure AKS</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/setup-robusta/openshift.html">
        <img src="./docs/images/integration_logos/openshift-icon.png" alt="OpenShift" width="40">
        <br><strong>OpenShift</strong>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/setup-robusta/gitops/argocd.html">
        <img src="./docs/images/integration_logos/argocd-icon.png" alt="ArgoCD" width="40">
        <br><strong>ArgoCD</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/setup-robusta/gitops/flux.html">
        <img src="https://fluxcd.io/img/flux-icon-color.png" alt="Flux" width="40">
        <br><strong>Flux</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/setup-robusta/installation/all-in-one-installation.html">
        <img src="./docs/images/integration_logos/prometheus-icon.png" alt="All-in-One" width="40">
        <br><strong>All-in-One Package</strong>
      </a>
    </td>
    <td align="center" width="100">
      <a href="https://docs.robusta.dev/master/setup-robusta/installation/standalone-installation.html">
        <img src="./docs/images/integration_logos/kubernetes-icon.png" alt="Standalone" width="40">
        <br><strong>Standalone</strong>
      </a>
    </td>
  </tr>
</table> -->

<!-- <p align="right">(<a href="#top">back to top</a>)</p> -->

## 🖥 Free Robusta UI
Take your Kubernetes monitoring to the next level with the [Robusta SaaS platform](https://platform.robusta.dev/signup?utm_source=github&utm_medium=robusta-readme&utm_content=free_robusta_ui_section). Creating an account is free, and includes:

- **AI Assistant**: Solve alerts faster with an AI assistant that highlights relevant observability data
- **Alert Timeline**: View Prometheus alerts across multiple clusters and spot correlations with a powerful timeline view
- **Change Tracking**: Correlate alerts with changes to your infrastructure or applications, with Robusta's automatic change tracking for Kubernetes

  <a href="https://www.loom.com/share/89c7e098d9494d79895738e0b06091f0">
      <img src="https://cdn.loom.com/sessions/thumbnails/89c7e098d9494d79895738e0b06091f0-f508768968f50b46-full-play.gif">
  </a>

<p align="right">(<a href="#top">back to top</a>)</p>


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


