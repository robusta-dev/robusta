# Installing Robusta as a user
If you want to use Robusta, see our [installation guide](https://robusta.dev/docs/getting-started/installing.html).

# Installing Robusta runner in cluster as a developer
If you want to develop features for Robusta itself you'll need to install Robusta from source:

1. `git clone` the source code. 
2. Install skaffold and kustomize.
3. Run `skaffold run --tail`

If you want to use the Slack integration, get a slack token from https://robusta.dev/integrations/slack/?id=xyz 
and add it to `deployment/dev/set_slack_api_key.yaml` before running skaffold.

# Running Robusta runner locally as a developer
If you want to run the Robusta runner on your own computer (e.g. with telepresence):

1. `git clone` the source code
2. `cd src`
3. `poetry install`
4. `poetry run python3 -m robusta.runner.main`

# Running Robusta cli locally as a developer
This is only necessary if you are developing features for the cli itself.
If you just want to develop robusta-runner and install it from your local version,
use the skaffold instructions above. 

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