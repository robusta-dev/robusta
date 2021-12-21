# Installing Robusta as a user
If you want to use Robusta, see our [installation guide](https://robusta.dev/docs/getting-started/installing.html).

# Installing Robusta runner in cluster as a developer
If you want to develop features for Robusta itself you'll need to install Robusta from source:

1. `git clone` the source code. 
2. Install [skaffold](https://skaffold.dev/) and [helm](https://helm.sh/). 
3. Run `robusta gen-config` and copy the result to `deployment/generated_values.yaml`
4. Run `skaffold run --tail`

If you encounter an error like: `"https://prometheus-community.github.io/helm-chart" is not a valid chart repository or cannot be reached` then run:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
```

# Running Robusta runner locally as a developer
This is never necessary, but you might find it more convenient to run Robusta locally and not in cluster.

1. `git clone` the source code
2. `cd src`
3. `poetry install`
4. `poetry run python3 -m robusta.runner.main`
5. Consider using [telepresence](https://www.telepresence.io/) to connect your local Robusta process with in-cluster services like Prometheus.

If you're on Mac OS and receive errors about `Pillow` or `libjpeg` when running `poetry install` then run `brew install libjpeg` first.

If you encounter `NotADirectoryError: [Errno 20] Not a directory` while trying to debug, you may need to disable the `Attach to subprocess` option on your debugger.

# Running Robusta cli locally as a developer
This is only necessary if you are developing features for the cli itself.

### Using poetry
1. `git clone` the source code
2. `cd src`
3. `poetry install`
4. `poetry run robusta`

### Alternative method using pip
This method installs robusta into your global python environment

1. `git clone` the source code
2. `cd src`
3. `pip3 install .`

# Running Tests
See [tests/README.md](./tests/README.md)
