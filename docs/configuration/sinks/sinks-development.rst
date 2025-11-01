Developing a New Sink
################################

If Robusta doesn't support the sink you need, consider implementing your own.

What Are Robusta Sinks?
--------------------------

:ref:`Sinks <sinks-reference>` are the destinations to which Robusta sends data. For example, when sending Robusta messages
to Slack, Robusta uses a Slack sink.

Internally, Robusta generates
:ref:`Findings <Creating Findings>`, or messages,
which are then formatted by each sink in an appropriate manner. For example,
a link might be formatted one way for Slack (e.g. markdown) and in another format
for another destination (e.g. HTML).

Before reading this tutorial, make sure you are familiar with the
:ref:`Findings API <Creating Findings>`
It contains explanations of the types of findings your sink will have to process.

How Sinks are Implemented
--------------------------

Sinks are located in `src/robusta/core/sinks <https://github.com/robusta-dev/robusta/tree/master/src/robusta/core/sinks>`_.
Each sink consists of a sink class and a config class. Optionally, helpers are used from `src/robusta/integrations <https://github.com/robusta-dev/robusta/tree/master/src/robusta/integrations>`_.

To implement a new sink you must:

1. :ref:`Build Robusta from source <Build from Source>`
2. Add a new Python module inside `src/robusta/core/sinks <https://github.com/robusta-dev/robusta/tree/master/src/robusta/core/sinks>`_ containing your sink’s source code
3. Implement a sink config class
4. Implement a sink class

Let's take a closer look at steps 3 and 4.

Implementing The Config Class
--------------------------------------------

There are two configuration classes we need to provide so our new sink can work properly.
Those are the “sink config” and “sink config wrapper” classes.

Let’s take a look at Robusta’s Mattermost sink as an example.

The relevant classes can be found at `src/robusta/core/sinks/mattermost/mattermost_sink_params.py <https://github.com/robusta-dev/robusta/tree/master/src/robusta/core/sinks/mattermost/mattermost_sink_params.py>`_

The class :code:`MattermostSinkParams` contains all the parameters our sink has.
In this example, we have *url*, *token*, *token_id*, and *channel* parameters.
Robusta uses Pydantic for validation This guarantees that all the required parameters will be
present to set up our sink. (You can also provide additional validation if needed, just like
the *url* parameter in the Mattermost sink).

.. code-block:: python

        class MattermostSinkParams(SinkBaseParams):
            url: str
            token: str
            token_id: str
            channel: str

            @validator("url")
            def set_http_schema(cls, url):
                parsed_url = urlparse(url)
                # if netloc is empty string, the url was provided without schema
                if not parsed_url.netloc:
                    raise AttributeError(f"{url} does not contain the schema!")
                return url

The :code:`MattermostSinkConfigWrapper` has nothing but the attribute to store
our sink configuration. It defines exactly how the sink’s configuration should look in your
Robusta YAML file. (E.g, if you renamed *mattermost_sink* in :code:`MattermostSinkConfigWrapper` to
*mattermost_cool_sink*, then Robusta’s YAML configuration would need to contain a
*mattermost_cool_sink* key to recognize the sink).

.. code-block:: python

    class MattermostSinkConfigWrapper(SinkConfigBase):
        mattermost_sink: MattermostSinkParams

        def get_params(self) -> SinkBaseParams:
            return self.mattermost_sink

Accordingly, you should create two configuration classes for your new sink.
These classes must inherit from :code:`SinkBaseParams` and :code:`SinkConfigBase` accordingly.

Implementing the Sink Class
------------------------------

Now we will implement the sink itself.

All sinks inherit from the :code:`SinkBase` class so they can be integrated with Robusta.
The main logic for the sink is located in the :code:`write_finding method`. It accepts two parameters:
*finding*, which is the
:ref:`Findings <Creating Findings>`
instance, and the *platform_enabled* boolean value.
The *platform_enabled* value indicates whether the Robusta platform sink is enabled in the
configuration, which allows us to add special buttons like  “Silence” and “Investigate”
to the message. These buttons send users to the Robusta UI, so only show them if the UI
(aka platform) is enabled.

To start, create a Sink class, inheriting from :code:`SinkBase`.

Inside your class, two methods need to be defined: the constructor method and the
:code:`write_finding` method that will do all the real work.

The easiest way to understand how sinks work is to find the **Webhook** sink class,
as it has a pretty simple structure.

:code:`Webhook.write_finding` takes as input a Finding instance containing several enrichments.
Those enrichments should be transformed into the state that our sink can consume.
The webhook sink simply transforms blocks to unformatted text that can be sent to any webhook.
We cannot process some blocks this way (e.g. *FileBlock* or *CallableBlock*) so they are skipped
in the :code:`__to_unformatted_text` method. It’s OK to send only a subset of blocks in the sink,
according to what the destination supports.

After the blocks are mapped and formatted into a message, they are sent to
the actual destination. Most of Robusta’s sinks use a POST call to a relevant API
provided by the destination. However, you are not limited to using only POST calls.
You can connect to destinations however you choose. For example, you could even open a
database connection if you wanted to.

Connecting the Sink to Robusta
---------------------------------

Once you have completed your sink’s implementation, you must add it to Robusta so it is recognized. To do so, you need to add your Sink definition to several places:

1. src/robusta/core/sinks/sink_factory.py
    Inside the create_sink method, add your newly created sink, as shown below:

    .. code-block:: python

        elif isinstance(sink_config, YourNewSinkConfigWrapper):
           return YourNewSink(sink_config, registry)

2. src/robusta/core/model/runner_config.py
    Inside the sinks_config attribute definition, add your new sink, as shown below:

    .. code-block:: python


           DiscordSinkConfigWrapper,
           MattermostSinkConfigWrapper,
           YourNewSinkConfigWrapper
        ]

Congrats! If you’ve made it here, you can now configure your new sink in Robusta’s
YAML configuration file and receive notifications at the destination of your choosing.
