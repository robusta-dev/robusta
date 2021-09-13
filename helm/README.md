# Robusta helm chart
Robusta's helm chart is served from our gcp bucket

# Upload a new chart version
If you want to upload a new chart version, follow these steps:
1. Update `Chart.yaml` file, with the updated `version` (Chart version) and `appVersion` (Robusta version)
2. Make sure the image tags in the `values.yaml` file are correct
3. Make sure `helm` and `gsutil` is installed on your machine.
4. From the directory, `helm`, run: `./upload_chart.sh`

# Installing robusta with the helm chart
1. Download the Robusta cli:
`pip3 install -U robusta-cli --no-cache`
2. Add Robusta's chart repo:
`helm repo add robusta https://robusta-charts.storage.googleapis.com`
3. Create the initial configuration for Robusta:
`robusta gen-config`
Follow the instructions, and a file named `active_playbooks_generated.yaml` is created
4. Lastly, install Robusta:
`helm install robusta robusta/robusta --set-file playbooks_file=./active_playbooks_generated.yaml` 