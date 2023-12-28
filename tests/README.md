# Cheat Sheet

Run tests faster by re-using resoures from the last run (this is less "clean" but typically fine):

```bash
./build_and_test.sh --fast-mode
```

Run a specific test: 

```bash
./build_and_test.sh -k test_foo
```

Run all tests in a specific file:

```bash
./build_and_test.sh tests/test_slack.py
```

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

# Slack Setup:
If you'd like to run the Slack tests, you will need two Slack tokens:

1. A regular Slack token generated with `robusta gen-config` that Robusta will send messages to Slack with.
2. A high-permission Slack token that you create and only you have access to. The tests use this to read and verify the messages that Robusta sends to Slack. 

The two tokens must be for the same Slack workspace.

If you work for Robusta, you can find the 2nd token in our password vault, under the title "tests/config.env".
If you don't have access to this, you can generate the 2nd token as follows:

1. Create a new Slack application at https://api.slack.com/apps/
2. Grant your application the following scopes:
    - app_mentions:read
    - channels:history
    - channels:read
    - chat:write
    - chat:write.public
    - conversations.connect:read
    - groups:history
    - groups:read
    - team:read
    - channels:join
    - channels:manage
3. Install the application into your Slack workspace
4. Copy your *Bot User OAuth Token* from the "OAuth & Permissions" screen at https://api.slack.com/apps/<app_id>/oauth,
5. Update `tests/config.env` with the token
6. Optional: reduce the chance you'll accidentally commit your Slack key to git by running `git update-index --skip-worktree tests/config.env`

# Running the tests:
Run `./build_and_test.sh`
   
**Warning:** The first run takes a long time because it builds a
docker image from scratch. Don't panic if it hangs for a while.
Subsequent runs are faster.