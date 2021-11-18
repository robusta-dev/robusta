# Robusta's docs
These docs are Sphinx docs

Currently it's all manual docs, but at a later phase can crawl the python code, and auto generate additional docs

## Github actions build & deploy
The docs are deployed into a public gcp bucket
Any push to docs/* will trigger a github workflow, that will build the docs to 'master' (https://docs.robusta.dev/master)
Creating a code release will build and deploy docs release too. (for example: https://docs.robusta.dev/0.4.26)
If you need to override an existing doc release, you can manually trigger the workflow, with the release version as a parameter

## Local Build

The docs definitions are .rst files.

First install the build requirements:
`poetry install`

To build the html, form the docs root, run:

`make html`

This command will create a directory named `_build` containing the build artifacts

In order to deploy it to the `relay` service, copy the artifacts into the relay:

`cp -r _build/html RELAY_ROOT/relay/static/docs`

Redeploy the relay using skaffold