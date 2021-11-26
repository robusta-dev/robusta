Findings API
###############

Motivation
--------------
Playbooks should use the Findings API to send messages to Slack, MSTeams, and other sinks.

By using the Findings API you can write a playbook once that works with all supported sinks.

Basic usage
------------------

Lets start with a simple example:

.. code-block:: python

    @action
    def test_playbook(event: ExecutionBaseEvent):
        event.add_enrichment([
            MarkdownBlock("This is a *markdown* message. Here are some movie characters:"),
            TableBlock([
                        ("Han Solo", "Star Wars"),
                        ("Paul Atreides", "Dune")
                       ], ["name", "movie"])
        )

Here is the playbook's output in Slack:


Here is the same playbook's output in the Robusta UI:

Concepts
--------------

TODO: link the add_enrichment

There are three important concepts in the Findings API: Findings, Enrichments, and Blocks. In the above example,
we implicitly created both a Finding and an Enrichment by calling ``add_enrichment`` and that Enrichment had two
blocks.

Findings
    A Finding describes an event that occurred at a specific time, like a Prometheus alert or a configuration change.
    For the Slack integration, a single Finding is sent as a single message. Every Finding contains metadata about the
    underlying event and one or more Enrichments.

Enrichments
    An Enrichment describes details about the Finding. For example, in a Prometheus alert Finding for the HighCPU alert,
    there will be one Enrichment containing alert labels, an additional Enrichment with a graph of CPU usage, and
    possibly a third Enrichment containing actionable recommendations. Every Enrichment has a type and a list of Blocks.

Blocks
    A Block is a visual element displayed to users. For example, a MarkdownBlock contains one or more paragraph of text.
    A TableBlock contains a table (converted behind the scenes to markdown or html). A FileBlock contains an attachment
    like an image or a log file. A DiffBlocks represents the diff between two objects and will be converted to either
    a Github-style HTML diff or a textual diff depending on the sink. And so on. The reason that Robusta uses Blocks
    is so that playbooks can easily output content that looks good for all sinks.


.. autoclass:: robusta.api.Finding
   :members:
   :undoc-members:
