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

<!-- <p align="right">(<a href="#top">back to top</a>)</p> -->

## 🖥 Free Robusta UI
Take your Kubernetes monitoring to the next level with the [Robusta SaaS platform](https://platform.robusta.dev/signup?utm_source=github&utm_medium=robusta-readme&utm_content=free_robusta_ui_section). Creating an account is free, and includes:

- **AI Assistant**: Solve alerts faster with an AI assistant that highlights relevant observability data
- **Alert Timeline**: View Prometheus alerts across multiple clusters and spot correlations with a powerful timeline view
- **Change Tracking**: Correlate alerts with changes to your infrastructure or applications, with Robusta’s automatic change tracking for Kubernetes

  <a href="https://www.loom.com/share/89c7e098d9494d79895738e0b06091f0">
      <img src="https://cdn.loom.com/sessions/thumbnails/89c7e098d9494d79895738e0b06091f0-f508768968f50b46-full-play.gif">
  </a>

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


## 🔗 Integrations

Robusta integrates with a variety of tools and platforms. Click on any logo to learn more about the integration.

### 📤 Sinks (Destinations)

<table>
  <tr>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/slack.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg" alt="Slack" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Slack</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/teams.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg" alt="MS Teams" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>MS Teams</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/pagerduty.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6e/PagerDuty_logo.svg" alt="PagerDuty" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>PagerDuty</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/jira.html">
        <img src="https://upload.wikimedia.org/wikipedia/en/8/8e/Jira_%28Software%29_logo.svg" alt="Jira" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Jira</strong>
    </td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/zulip.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6f/Zulip_logo.svg" alt="Zulip" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Zulip</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/email.html">
        ✉️
      </a>
      <br><strong>Email</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/sinks/robusta-ui.html">
        <img src="https://docs.robusta.dev/master/_static/faviconNew.svg" alt="Robusta UI" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Robusta UI</strong>
    </td>
  </tr>
</table>

### 📥 Data Sources

<table>
  <tr>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/data-sources/prometheus.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/3/38/Prometheus_Logo.svg" alt="Prometheus" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Prometheus</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/data-sources/grafana.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e9/Grafana_icon.svg" alt="Grafana" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Grafana</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/data-sources/victoria-metrics.html">
        <img src="https://victoriametrics.com/assets/img/logo.svg" alt="Victoria Metrics" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Victoria Metrics</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/data-sources/google-managed-prometheus.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Google_Cloud_logo.svg" alt="Google Managed Prometheus" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Google Managed Prometheus</strong>
    </td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/data-sources/aws-managed-prometheus.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" alt="AWS Managed Prometheus" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>AWS Managed Prometheus</strong>
    </td>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/data-sources/coralogix.html">
        <img src="https://coralogix.com/wp-content/uploads/2020/01/coralogix-logo.svg" alt="Coralogix" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>Coralogix</strong>
    </td>
  </tr>
</table>

### 🧠 AI Analysis

<table>
  <tr>
    <td align="center">
      <a href="https://docs.robusta.dev/master/configuration/holmesgpt/index.html">
        <img src="https://upload.wikimedia.org/wikipedia/commons/4/4f/Robot_icon.svg" alt="HolmesGPT" style="background:white; padding:10px; border-radius:10px;" width="80">
      </a>
      <br><strong>HolmesGPT</strong>
    </td>
  </tr>
</table>

<p align="right">(<a href="#top">back to top</a>)</p>