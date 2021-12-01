# Overview
We use `pytest`. We have two categories of tests:

1. Module tests: e.g. Slack tests.
   These run locally on your own machine, although they might contact services
   like Slack to test functionality.
   
2. End-to-end tests: These install Robusta on a Kubernetes cluster and 
    test it on that cluster. You need either a real cluster or KIND for these tests.
   
Right now both kinds of tests are bundled together. We should probably make it easier
to run each kind of test separately.

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