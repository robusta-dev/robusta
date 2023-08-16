Rocket.Chat
#################

Robusta can report issues and events in your Kubernetes cluster to Rocket.Chat.

.. image:: /images/rocketchat1.png
  :width: 600

Connecting Rocket.Chat
------------------------------------------------

To set up the Rocket.Chat sink, you'll need the following information:

* Personal Access Token

* User ID

* Channel name

* Server URL


Follow these steps to generate the `Personal Access Token` and `User ID`:

* Log in to your Rocket.Chat server using a valid username and password.

*  Click on your avatar and select `My Account`.

*  Navigate to Profile > Preferences > Personal Access Tokens.

*  Check the `Ignore Two Factor Authentication` option.

*  Fill in the `Add new Personal Access Token` text field and click the `Add` button.

*  Copy the provided `Personal Access Token` and `User ID`.


.. image:: /images/rocketchat2.png
  :width: 1000

Configuring the Rocket.Chat sink
------------------------------------------------

.. admonition:: Add this to your generated_values.yaml

    .. code-block:: yaml

         sinks_config:
         # Rocket.Chat integration params
        - rocketchat_sink:
              name: main_rocketchat_sink
              user_id: <User ID>
              channel: <Rocket.Chat channel>
              token: <Personal Access Token>
              server_url: <Server URL>

Save the file and run

.. code-block:: bash
   :name: cb-add-rocketchat-sink

    helm upgrade robusta robusta/robusta --values=generated_values.yaml

