Creating Findings
###################

Motivation
--------------
Playbooks should use the Findings API to display output. They should **not** send output directly to Slack or other destinations.

By using the Findings API, your playbook will support Slack, MSTeams, and other sinks.

Basic Usage
-----------------

Playbooks can call ``event.add_enrichment`` to add to the playbook's output. For example:

.. code-block:: python

    @action
    def test_playbook(event: ExecutionBaseEvent):
        event.add_enrichment(
            [
                MarkdownBlock(
                    "This is a *markdown* message. Here are some movie characters:"
                ),
                TableBlock(
                    [["Han Solo", "Star Wars"], ["Paul Atreides", "Dune"]],
                    ["name", "movie"],
                ),
            ]
        )


When playbooks finish running, their output is sent to the configured sinks.
Here is output for the above example:

.. tab-set::

    .. tab-item:: Slack

        .. image:: /images/basic-robusta-finding-slack.png
            :width: 700

Core Concepts
----------------------------

The Findings API has four important concepts:

Finding
    An event, like a Prometheus alert or a deployment update.

Enrichment
    Details about a Finding, like the labels for a Prometheus alert or a deployment's YAML before and after the update.

Block
    A visual element, like a paragraph, an image, or a table.

Sink
    A destination Findings are sent to, like Slack, MSTeams, Kafka topics

Here is an example showing the above concepts:

.. graphviz::

    digraph {
      compound=true;
      rankdir=TB
      fixedsize=true;

      node [ fontname="Handlee"
             fixedsize=true
             width=2
             height=1
      ];
      subgraph cluster_finding {

          label=<Finding<BR /><BR /><I><FONT POINT-SIZE="9">HighCPU Alert</FONT></I>>;

          subgraph cluster_enrichment1 {
              label=<Enrichment<BR /><BR /><I><FONT POINT-SIZE="9">Prometheus Labels</FONT></I>>;
              block1 [
                  label = <TableBlock<BR /><BR /><I><FONT POINT-SIZE="9">pod=my-pod<BR />namespace=default</FONT></I>>;
              ]
          }

          subgraph cluster_enrichment2 {
              label=<Enrichment<BR /><BR /><I><FONT POINT-SIZE="9">CPU Profile Result</FONT></I>>;
              rank=same;
              block2 [
                  label = <MarkdownBlock<BR /><BR /><I><FONT POINT-SIZE="9">Explanation</FONT></I>>;
              ]
              block3 [
                  label = <FileBlock<BR /><BR /><I><FONT POINT-SIZE="9">Profiler Result</FONT></I>>;
              ]
          }
      }

          slack_sink [
              label = <Slack Sink>;
          ]
          msteams_sink [
              label = <MSTeams Sink>;
          ]
          more_sinks [
              label = <...>;
          ]

      block2 -> slack_sink, more_sinks, msteams_sink [ltail=cluster_finding minlen=2];
    }

Advanced Usage
-----------------

It is possible to customize a findings name, override the default finding for events, and more.

But we haven't documented it yet. Please consult the source code.

.. autoclass:: robusta.api.Finding
   :members:
   :undoc-members:

Block Types
-----------------------------

Every Block represents a different type of visual data. Here are the possible Blocks:

.. module:: robusta.api

.. autosummary::

    MarkdownBlock
    FileBlock
    DividerBlock
    HeaderBlock
    ListBlock
    TableBlock
    KubernetesFieldsBlock
    KubernetesDiffBlock
    JsonBlock
    CallbackBlock

.. note::

    Not all block types are supported by all sinks. If an unsupported block arrives at a sink, it will be ignored

Reference
--------------

.. autoclass:: robusta.api.MarkdownBlock
    :no-members:

    A simple example:

    .. code-block:: python

        MarkdownBlock("Hi, *I'm bold* and _I'm italic_")

    Things can get hairy when using writing content across multiple lines:

    .. code-block:: python

        MarkdownBlock(
            "# This is a header \n\n"
            "And this is a paragraph. "
            "Same paragraph. A new string on each line prevents Python from adding newlines."
        ),

    For convenience, use ``strip_whitespace=True`` and multiline strings:

    .. code-block:: python

        MarkdownBlock("""
            Due to strip_whitespace=True this is all one
            paragraph despite indentation and newlines.
            """, strip_whitespace=True)


.. autoclass:: robusta.api.FileBlock
    :no-members:

    Examples:

    .. code-block:: python

        FileBlock("test.txt", "this is the file's contents")

.. autoclass:: robusta.api.DividerBlock
    :no-members:

.. autoclass:: robusta.api.HeaderBlock
    :no-members:

.. autoclass:: robusta.api.ListBlock
    :no-members:

.. autoclass:: robusta.api.TableBlock
    :no-members:

.. autoclass:: robusta.api.KubernetesFieldsBlock
    :no-members:

.. autoclass:: robusta.api.KubernetesDiffBlock
    :no-members:

.. autoclass:: robusta.api.JsonBlock
    :no-members:

.. autoclass:: robusta.api.CallbackBlock
    :no-members:
