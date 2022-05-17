Robusta UI Triggers
############################
| Robusta UI can pull data directly from your clusters.
| This lets you see extra data like running pods, which is fetched on demand.

Minimum Requirements
********************
Robusta & Robusta CLI versions must be at least :code:`0.9.11`.

- Robusta
    - To check your current cluster version, run: :code:`helm list --filter robusta`
    - To upgrade your cluster to the latest version, run: :code:`robusta upgrade`
    - Note! You need to do this per cluster.
- Robusta CLI
    - To check your current CLI version, run: :code:`robusta version`
    - To upgrade your CLI to latest version, run: :code:`pip install -U robusta-cli --no-cache`

Multi Cluster Support
*********************
To use this feature on multiple clusters, make sure you install Robusta with these same values across all your clusters:
    - :code:`globalConfig.account_id`
    - :code:`globalConfig.signing_key`
    - :code:`rsa`
| These values are inside the :code:`values.yaml` file you use when you run :code:`helm install robusta...`
| See `Installation Guide <https://docs.robusta.dev/master/installation.html>`_ for more details.