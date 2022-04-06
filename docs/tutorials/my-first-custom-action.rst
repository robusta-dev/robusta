Customizing Robusta
######################################################

Learn how to automate Kubernetes error handling with Robusta., in *15 minutes* or less :)

Goals
---------------------------------------
We’re going to create a custom playbook using a short and made-up (but realistic) scenario.

First, we’ll describe the the scenario, and then we’ll implement a Robusta automation (playbook) that detects this issue immediately and recommends a fix!

You’re more than welcome to follow along the scenario on your own machine 💻

.. note::

    It is recommended to read :ref:`Track Kubernetes Changes` before starting this guide.

The scenario
---------------------------------------
You want to create a new pod with the image “ngnix”!

Being the smart person that you are, you decide save some time by copying and pasting an existing YAML file you have in your computer, and changing the pod name and image to ngnix.

.. code-block:: yaml

    apiVersion: v1
    kind: Pod
    metadata:
      name: nginx
      labels:
        env: test
    spec:
      containers:
      - name: nginx
        image: nginx
        imagePullPolicy: IfNotPresent
      nodeSelector:
        spoiler: alert

Now you start the pod by running the following command:

.. code-block:: bash

    $ kubectl apply -f nginx-pod.yaml
    pod/nginx created

For some reason the pod doesn't start (note it’s “Pending” Status):

.. code-block:: bash

    $ kubectl get pods

    NAME                                                     READY   STATUS    RESTARTS   AGE

    nginx                                                    0/1     Pending   0          5h19m

You wait a few minutes, but is remains the same.

Then you say, ok, let’s look at the event log:

.. code-block:: bash

    kubectl get event --field-selector involvedObject.name=nginx
    LAST SEEN   TYPE      REASON             OBJECT      MESSAGE
    64s         Warning   FailedScheduling   pod/nginx   0/1 nodes are available: 1 node(s) didn't match Pod's node affinity/selector.

Aha! “1 node(s) didn't match Pod's node affinity/selector.”! ALRIGHT!!!



Wait, what does it mean? 😖  (Hint: Check the YAML config for the spoiler)



After searching online for some time, you find out that the YAML file you copied had a “nodeSelector” with the key-value “spoiler: alert”, which means that it can only be scheduled on nodes (machines) that have this configuration 🤦‍♂️.

From the docs:

.. pull-quote::
    nodeSelector is the simplest recommended form of node selection constraint. nodeSelector is a field of PodSpec. It specifies a map of key-value pairs. For the pod to be eligible to run on a node, **the node must have each of the indicated key-value pairs as labels** (it can have additional labels as well). The most common usage is one key-value pair.

So you comment out those lines, run kubectl apply again, and all is well.

.. code-block:: yaml

    apiVersion: v1
    kind: Pod
    metadata:
      name: nginx
      labels:
        env: test
    spec:
      containers:
      - name: nginx
        image: nginx
        imagePullPolicy: IfNotPresent
    #  nodeSelector:
    #    spoiler: alert


Automating the detection with a Robusta Playbook
----
What we need to do?
----

.. note::
    Make sure to clean up the pod from the last section by running ``kubectl delete pod nginx``

A playbook consists of two things:

- Trigger - We’re going to use a built in trigger
- Action - We’re going to write our own action!


Finding the correct trigger
----
What is the correct trigger for the job?
We can think of two triggers that may fit:

- Creation of a new pod (because we create a new pod, ‘ngnix’)
- A Kubernetes Event is fired (because we ran kubectl get event to find out the scheduling error)

Let’s look at the Trigger section about :ref:`Kubernetes (API Server)`, and try to find out triggers for both.
Go ahead and try to find them!

Okay! We find ``on_pod_create`` and ``on_event_create``

We'll use ``on_event_create`` in this tutorial because it will be easier to identify scheduling issues by looking at the event.

Writing the action
----

Now we need to write code that checks this event and reports it. To find the correct event class that matches our trigger ``on_event_create``. please take a look at :ref:`Event Hierarchy`.

Okay! We find out it’s ``EventEvent``!

So we need to get the information, check for the scenario, and then report it (for more information about reporting it see :ref:`Findings API`)

Let’s name our action ``report_scheduling_failure``, and write everything in a python file:

.. code-block:: python

    from robusta.api import *

    @action
    def report_scheduling_failure(event: EventEvent):
        actual_event = event.get_event()

        print(f"This print will be shown in the robusta logs={actual_event}")

        if actual_event.type.casefold() == f'Warning'.casefold() and \
            actual_event.reason.casefold() == f'FailedScheduling'.casefold() and \
            actual_event.involvedObject.kind.casefold() == f'Pod'.casefold():
            _report_failed_scheduling(event, actual_event.involvedObject.name, actual_event.message)

    def _report_failed_scheduling(event: EventEvent, pod_name: str, message: str):
        # this is how you send data to slack or other destinations
        event.add_enrichment([
            MarkdownBlock(f"Failed to schedule a pod named '{pod_name}', error: {message}"),
        ])

Before we proceed, we need to enable local playbook repositories in Robusta.

Follow this quick guide to learn how to package your python file for Robusta: :ref:`Custom playbook repositories`

Use this useful debugging commands to make sure your action ( ``report_scheduling_failure``) is loaded:

.. code-block:: bash

    robusta logs # get robusta logs, see errors
    robusta playbooks list-dirs  # get see if you custom action package was loaded

Let’s push the new action to Robusta, and then test it by triggering the action manually immediately.

.. code-block:: bash

    robusta playbooks push <PATH_TO_LOCAL_PLAYBOOK_FOLDER>
    robusta playbooks trigger report_scheduling_failure name=robusta-runner-8cd69f7cb-g5bkb namespace=default seconds=5

Check our slack channel, and:

.. image:: /images/example_report_scheduling_failure.png

Connection the trigger to the action - a Playbook is born!
-------------------------------------

We need to add a custom playbook that this action it in the generated_values.yaml.

.. code-block:: yaml

    globalConfig:
      signing_key: XXXX
      account_id: XXXX
    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: '#my-slack-channel'
        api_key: XXXXX
    - robusta_sink:
        name: robusta_ui_sink
        token: XXXXXX  # generated with `robusta gen-config`
    clusterName: my-cluster
    enablePrometheusStack: true
    # Custom Playbooks from here
    customPlaybooks:
    - triggers:
      - on_event_create: {}
      actions:
      - report_scheduling_failure: {}
    # Enable loading playbooks to a persistent volume
    playbooksPersistentVolume: true

.. note::
    If you haven't already, make sure to clean up the pod from the last section by running ``kubectl delete pod nginx``

Time to update Robusta’s config with the new generated_config.yaml:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml
    robusta playbooks list # see all the playbooks. Run it after a few minutes

After a minute or two Robusta will be ready.

Let’s push the new action to Robusta:

.. code-block:: bash

    robusta playbooks push <PATH_TO_PLAYBOOK_FOLDER>

After a minute or two Robusta will be ready.

Great!

Run the scenario from the first section again (creating a bad bad configuration), and you should see this in your slack:

Check our slack channel, and:

.. image:: /images/example_report_scheduling_failure.png

Cleaning up
----

.. code-block:: bash

    kubectl delete pod nginx # delete the pod
    robusta playbooks delete <PLAYBOOK_FOLDER> # remove the playbook we just added from Robusta

    # Remove "customPlaybooks" and "playbooksPersistentVolume" from you config, and then run helm upgrade
    helm upgrade robusta robusta/robusta --values=generated_values.yaml


Summary
-------------------------------------

We learned how to solve a real problem (pod not scheduling) only once and have Robusta automate it in the future for all our happy co-workers (and future us) to enjoy.

This example of an unschedulable pod is actually covered by Robusta out of the box (if you enable the builtin Prometheus stack) but you can see how easy it is to track any error you like and send it to a notifications system with extra data.