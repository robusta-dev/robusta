Here are demo scenarios you can use to evaluate Robusta.dev. Each demo can be run with a single bash command.

# Crashing Pod Demo

## Running it

1. Run `cd ./crash_pod_demo && ./crashpod_demo.sh && cd ..`
2. Press enter to deliberately break the `crashpod` deployment and make it crash
3. Check your Slack channel for a notication about the crashing pod. The message includes the pod's logs!
4. Click the "Investigate button" to open Robusta's UI
5. Click on the last change event and see exactly what broke the pod

## Value Demonstrated

1. You can get Slack notifications about issues in your cluster 
2. Notifications contain the exact data you need to diagnose the issue
3. You see more troubleshooting data in the Robusta UI, including recent changes to Kubernetes objects

# OOM Kill (Out of Memory Kill) Demo

## Running it

1. Run `kubectl apply -f ./oomkill_demo/oomkill_job.yaml`
2. Check your Slack channel for a notification about the Kubernetes pod which got OOMKilled. The message includes details you need to debug the out of memory error.
3. Clean up the demo with `kubectl delete -f ./oomkill_demo/oomkill_demo.yaml`

## Value Demonstrated

Robusta shows relevant data for each alert. In this specific case, Robusta shows relevant memory graphs for OOM Kills.

This lets you fix issues faster with more confidence.

# CPU Throttling Demo (CPUThrottlingHigh alert)

## Running it

1. Run `kubectl apply -f ./cpu_throttling/`
2. Wait 15 minutes and then check your Slack channel for a notification about CPU throttling. The message includes a **dynamic** explanation about why it occurred and how to fix it.
3. Clean up the demo with `kubectl delete -f ./cpu_throttling`

**Note: To avoid noisy alerts about temporary and minor throttling, Robusta only alerts after CPU throttling occurs for at least 15 minutes.**

## Value Demonstrated

Robusta automatically investigates common Kubernetes issues and tells you why they occur.

Note: Robusta's explanations are **dynamic** and depend on the real reason an issue is occurring! If you had CPU throttling on a pod without CPU limits then you would have received **different** advice as the situation is different.

# Debugging Pending Pods

## Running it

1. Run `kubectl apply -f pending_pods` 
2. Wait 15 minutes and then check your Slack channel for a notification about the pending pod. The message includes Kubernetes events which tell you *why* the pod can't be scheduled to any of the existing nodes
3. Clean up the demo by running `kubectl delete -f pending_pods`

**Note: By default, Robusta only alerts after a pod is pending for 15 minutes.** In a busy Kubernetes cluster with autoscaling, it's normal and OK if pods are pending for short periods of time while clusters scale up!

## Value Demonstrated

Robusta tells you *why* pods are pending. E.g. if a pod is pending because there isn't enough CPU in the cluster, Robusta will tell you so! If the issue is not enough memory thenRobusta will tell you that instead. This works by pulling in the relevant Kubernetes events automatically, just like you would see in `kubectl get events` if you filtered for the relevant pods.

# ImagePullBackOff

## Running it

1. Run `kubectl apply -f image_pull_backoff`
2. Look at your Slack channel or the Robusta UI for a message about the ImagePullBackoff
3. Clean up the demo by running `kubectl delete -f image_pull_backoff`

## Value Demonstrated

Robusta identifies ImagePullBackoffs and also helps you differentiate between the different reasons (e.g. wrong image vs nonexistent tag)

# Namespace Comparison

## Running it

1. Run `kubectl apply -f namespace_comparison_demo` 
2. Open the Robusta UI and wait about 60 seconds for the new services to appear
2. In the Robusta UI click on the "Comparison" page
3. Perform a comparison between the `compare1` and `compare2` namespaces
4. Clean up the demo by running `kubectl delete -f namespace_comparison_demo`

## Value Demonstrated

You can identify drift between multiple clusters or namespaces.

This is useful for two scenarios:

1. When you are running multiple copies of an application. You can map out which versions are running and where.
2. When a bug occurs in one environment but not another. You can see exactly how those environments differ.

# Other
More examples coming soon. Please open a GitHub issue if you have ideas!

