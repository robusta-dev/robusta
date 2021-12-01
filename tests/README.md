# Overview
We use `pytest`. We have two categories of tests which are currently
bundled together but should probably be split in some way:

1. Tests for specific modules: For example, tests for the Slack integration.
   These run locally on your own machine, although they might contact other servers
   like Slack to test functionality.
   
2. End-to-end tests: These install Robusta on a Kubernetes cluster and then 
    run tests by connecting to that cluster and checking Robusta's end to end
    functionality. These tests cannot run without a Kubernetes server. However,
    they can run on KIND so you don't need a "real" cluster.

# Requirements:
1. You need to have a Kubernetes cluster 
2. The Kubernetes cluster should be your current kube-config.
   Check with `kubectl config get-contexts`

# Setup:
1. Set a Slack token in `tests/config.env`
2. Optional: reduce the chance you'll accidentally commit your Slack key to git by running `git update-index --skip-worktree tests/config.env`

# Running the tests:
Run `./build_and_test.sh`
   
**Warning:** The first run takes a long time because it builds a
docker image from scratch. Don't panic if it hangs for a while.
Subsequent runs are faster.