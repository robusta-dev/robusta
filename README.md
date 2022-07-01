<div align="center">
  <p>
    <a href="https://home.robusta.dev/" target="_blank">
        <img src="./logos/Robusta_readme.png" alt="Robusta Logo">
    </a>
</p>
  <h2>Robusta</h2>
    <h3>A troubleshooting and automations platform for Kubernetes</h3>
   <a href="https://docs.robusta.dev/master/"><strong>Explore the docs »</strong></a>
  <p>

  ![GitHub Workflow Status (event)](https://img.shields.io/github/workflow/status/robusta-dev/robusta/Test%20robusta%20with%20pytest?event=push&label=Build&style=flat-square)
  ![GitHub](https://img.shields.io/github/license/robusta-dev/robusta?color=orange&label=License&logoColor=Greed&style=flat-square)

  [![twitter robusta](https://img.shields.io/twitter/follow/RobustaDev?logo=twitter&color=blue&label=@RobustaDev&style=flat-square)](https://twitter.com/RobustaDev)
  [![slack robusta](https://img.shields.io/badge/Slack-Join-4A154B?style=flat-square&logo=slack&logoColor=white)](https://join.slack.com/t/robustacommunity/shared_invite/zt-10rkepc5s-FnXKvGjrBmiTkKdrgDr~wg)
 <a href="https://www.linkedin.com/company/robusta-dev/"><img alt="LinkedIn" title="LinkedIn" src="https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white"/></a>
  <a href="https://www.youtube.com/channel/UCeLrAOI3anJAfO3BrYVB62Q"><img alt="Youtube" title="Youtube" src="https://img.shields.io/youtube/channel/subscribers/UCeLrAOI3anJAfO3BrYVB62Q?color=%23ff0000&label=Robusta%20Dev&logo=youtube&logoColor=%23ff0000&style=flat-square"/></a>
</div>

<div id="top"></div>
<!-- TABLE OF CONTENTS -->
<details>
  <summary><h3 style="display:inline;">Table of Contents</h3></summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#use-cases">Use cases</a>
    </li>
    <li><a href="#examples">Examples</a></li>
    <li><a href="#installing-robusta">Installing</a></li>
    <li><a href="#documentation">Documentation</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#stay-up-to-date">Stay up to date</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## 💻 About the project
Robusta streamlines everything that happens **after** you deploy your application. It is somewhat like Zapier/IFTTT for DevOps, with an emphasis on prebuilt useful automations and not just "build your own".

## 🛠️ Use cases

- [X] [Kubernetes monitoring - prebuilt Prometheus integration that enriches alerts with extra context and graphs](https://home.robusta.dev/prometheus-based-monitoring/?from=github)
- [X] Event-triggered automations for Kubernetes (like Argo Events) with an emphasis on simplicity
- [X] Auto-remediations - out of the box fixes for common alerts. Write your own in Python.
- [X] [Change tracking - track and audit every change to your Kubernetes cluster](http://home.robusta.dev/ui?from=github)

[Screenshots and demos »](http://robusta.dev/?from=github)


## ⚡ Examples

**Monitor crashing pods and send their logs to Slack:**

```yaml
triggers:
  - on_prometheus_alert:
      alert_name: KubePodCrashLooping
actions:
  - logs_enricher: {}
sinks:
  - slack
```

![](./docs/images/crash-report.png)

**Remediate alerts with the click of a button:**

![](./docs/images/alert_on_hpa_reached_limit1.png)

**Take manual troubleshooting actions, like [attaching a debugger to a python pod](https://docs.robusta.dev/master/catalog/actions/python-troubleshooting.html#python-debugger):**

```commandline
robusta playbooks trigger python_debugger name=mypod namespace=default
```

[Over 50 built-in automations »](https://docs.robusta.dev/master/catalog/actions/index.html)

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

* Slack - [robustacommunity.slack.com](https://join.slack.com/t/robustacommunity/shared_invite/zt-10rkepc5s-FnXKvGjrBmiTkKdrgDr~wg)
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


## 🙏 Acknowledgments
Thank you to all of our contributors!

An additional thanks to all the open source projects we use. Especially:

1. [Hikaru](https://hikaru.readthedocs.io/)
2. [Pydantic](https://pydantic-docs.helpmanual.io/)
3. [Typer](https://typer.tiangolo.com/tutorial/options/)
4. [Kubernetes Python library](https://github.com/kubernetes-client/python/)
5. [CairoSVG](https://github.com/Kozea/CairoSVG)
6. [...and all the other libraries we use](https://github.com/robusta-dev/robusta/network/dependencies)

Each open source project is used in accordance with the relevant licenses.
Details can be found on the website for each project.
<p align="right">(<a href="#top">back to top</a>)</p>
