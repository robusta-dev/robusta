Here are demo scenarios you can use to evaluate Robusta.dev. Each demo can be run with a single bash command.

# Crashing Pod Demo

## Running it

1. Run the script `./crash_pod_demo/crashpod_demo.sh`
2. Press enter to deliberately break the `crashpod` deployment and make it crash
3. Check your Slack channel for a notication about the crashing pod. The message includes the pod's logs!
4. Click the "Investigate button" to open Robusta's UI
5. Click on the last change event and see exactly what broke the pod

## Value Demonstrated

This demo shows:

1. You can get Slack notifications about issues in your cluster 
2. Notifications contain the exact data you need to debug
3. You see more troubleshooting data in the Robusta UI, including recent changes to Kubernetes objects

# OOM Kill Demo

## Running it

1. Run `kubectl apply -f ./oomkill_demo/oomkill_demo.yaml`
2. Check your Slack channel for a notification about the crashing pod. The message includes details you need to debug the OOM

## Value Demonstrated

This demo shows that Robusta has built-in knowledge about very specific errors in your cluster, including OOM Kills. 

Robusta automatically gathers the right data you need to debug each issue.

This lets you fix issues faster with more confidence.

# Namespace Comparison

## Running it

1. Run `kubectl apply -f namespace_comparison_demo` 
2. Open the Robusta UI and click on the "Comparison" page
3. Perform a comparison between the `compare1` and `compare2` namespaces

## Value Demonstrated

You can identify drift between multiple clusters or namespaces.

This is useful for two scenarios:

1. When you are running multiple copies of an application and need to instantly know what version is running where
2. When a bug occurs in one environment but not another. You can see exactly how those environments differ.

# Other
More examples coming soon. Please open a GitHub issue if you have ideas!

