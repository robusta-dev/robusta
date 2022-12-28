# Robusta helm chart
Robusta's helm chart is served from our gcp bucket.

NOTE: **Don't use the Helm values file directly**. Check the [Installation instructions](https://docs.robusta.dev/master/getting-started/installation.html) 

# Upload a new chart version
If you want to upload a new chart version, follow these steps:
1. Update `Chart.yaml` file, with the updated `version` (Chart version) and `appVersion` (Robusta version)
2. Make sure the image tags in the `values.yaml` file are correct
3. Make sure `helm` and `gsutil` is installed on your machine.
4. From the directory, `helm`, run: `./upload_chart.sh`

# Installing robusta with the helm chart
See https://docs.robusta.dev/master/getting-started/installation.html
