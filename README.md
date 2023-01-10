<div align="center">
  <p>
    <a href="https://home.robusta.dev/" target="_blank">
        <img src="./logos/Robusta_readme.png" alt="Robusta.dev">
    </a>
</p>
  <h2>Monitor Kubernetes the Right Way</h2>
    <h3>Connect your existing Prometheus and gain 360° observability*</h3>
    *Prometheus recommended, but not required.
  <p>

  [![twitter robusta](https://img.shields.io/twitter/follow/RobustaDev?logo=twitter&color=blue&label=@RobustaDev&style=flat-square)](https://twitter.com/RobustaDev)
  [![slack robusta](https://img.shields.io/badge/Slack-Join-4A154B?style=flat-square&logo=slack&logoColor=white)](https://bit.ly/robusta-slack)
 <a href="https://www.linkedin.com/company/robusta-dev/"><img alt="LinkedIn" title="LinkedIn" src="https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white"/></a>
  <a href="https://www.youtube.com/channel/UCeLrAOI3anJAfO3BrYVB62Q"><img alt="Youtube" title="Youtube" src="https://img.shields.io/youtube/channel/subscribers/UCeLrAOI3anJAfO3BrYVB62Q?color=%23ff0000&label=Robusta%20Dev&logo=youtube&logoColor=%23ff0000&style=flat-square"/></a>
</div>

<div id="top"></div>
<!-- TABLE OF CONTENTS -->
<details>
  <summary><h3 style="display:inline;">Table of Contents</h3></summary>
  <ol>
    <li>
      <a href="#about-the-project">About the project</a>
    </li>
    <li>
      <a href="#use-cases">Use cases</a>
    </li>
    <li><a href="#examples">Examples</a></li>
    <li><a href="#installing-robusta">Installing Robusta</a></li>
    <li><a href="#documentation">Documentation</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#stay-up-to-date">Stay up to date</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## 💻 About the project
Robusta is both an automations engine for Kubernetes, and a [full observability platform](https://home.robusta.dev/) built with that engine.

Robusta is commonly used alongside Prometheus, but other tools are supported too.

By listening to all the events in your cluster, Robusta can tell you *why* alerts fired, what happened at the same time, and what you can do about it.

Robusta can either improve your existing alerts, or be used to define new alerts triggered by APIServer changes.

## 🛠️ How it works

Robusta's behaviour is defined by rules like this:

```yaml
triggers:
  - on_prometheus_alert:
      alert_name: KubePodCrashLooping
actions:
  - logs_enricher: {}
sinks:
  - slack
```

In the above example, whenever the `KubePodCrashLooping` alert fires, Robusta will fetch logs from the right pod and attach them to the alert. The result looks like this:

![](./docs/images/crash-report.png)

Robusta also supports alert-remediations:

![](./docs/images/alert_on_hpa_reached_limit1.png)

[Over 50 types of automations and enrichments are built-in »](https://docs.robusta.dev/master/catalog/actions/index.html)

<p align="right">(<a href="#top">back to top</a>)</p>

## 📒 Installing Robusta

1. Install our python cli:

```commandline
python3 -m pip install -U robusta-cli --no-cache
```

2. Generate a values file for Helm:
```commandline
robusta gen-config
```

3. Install Robusta with Helm:
```commandline
helm repo add robusta https://robusta-charts.storage.googleapis.com && helm repo update
helm install robusta robusta/robusta -f ./generated_values.yaml
```

[Detailed instructions »](https://docs.robusta.dev/master/installation.html)

<!-- <p align="right">(<a href="#top">back to top</a>)</p> -->

## 📝 Documentation
Interested? Learn more about Robusta

* [Architecture](https://docs.robusta.dev/master/architecture.html)
* [Upgrade and Uninstall](https://docs.robusta.dev/master/upgrade.html)
* [Configuration Guide](https://docs.robusta.dev/master/user-guide/configuration.html)
* [Triggers](https://docs.robusta.dev/master/catalog/triggers/index.html)

[Full documentation »](https://docs.robusta.dev/master/index.html)
<p align="right">(<a href="#top">back to top</a>)</p>


## ✉️ Contact

* Slack - [robustacommunity.slack.com](https://bit.ly/robusta-slack)
* Twitter - [@RobustaDev](https://twitter.com/RobustaDev)
* LinkedIn - [robusta-dev](https://www.linkedin.com/company/robusta-dev/)
* Jobs - [jobs@robusta.dev ](mailto:jobs@robusta.dev)
* Email Support - [support@robusta.dev ](mailto:support@robusta.dev )

<p align="right">(<a href="#top">back to top</a>)</p>

## 📑 License
Robusta is distributed under the MIT License. See [LICENSE.md](https://github.com/robusta-dev/robusta/blob/master/LICENSE) for more information.

## 🕐 Stay up to date
We add new features regularly. Stay up to date by watching us on GitHub.

![](./docs/images/star-repo.gif)
