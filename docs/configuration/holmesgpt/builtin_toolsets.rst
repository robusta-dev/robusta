


Builtin Toolsets
===============

.. toctree::
   :hidden:
   :maxdepth: 1

   toolsets/argocd
   toolsets/aws
   toolsets/confluence
   toolsets/docker
   toolsets/grafana
   toolsets/helm
   toolsets/internet
   toolsets/kubernetes
   toolsets/opensearch
   toolsets/robusta
   toolsets/slab

Holmes allows you to define and configure integrations (toolsets) that fetch data from external sources. This data will be automatically used in investigations when relevant.

You can :doc:`write your own toolset <custom_toolsets>` or use the default Holmes toolsets listed below.


Builtin toolsets
^^^^^^^^^^^^^^^^^^^^^
Holmes comes with a set of builtin toolsets. Most of these toolsets are enabled by default, such as toolsets to read Kubernetes resources and fetch logs. Some builtin toolsets are disabled by default and can be enabled by the user by providing credentials or API keys to external systems.

.. grid:: 1 1 2 3
    :gutter: 3

    .. grid-item-card:: :octicon:`cpu;1em;` ArgoCD
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/argocd
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` AWS
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/aws
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Confluence
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/confluence
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Docker
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/docker
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Grafana
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/grafana
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Helm
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/helm
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Kubernetes
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/kubernetes
        :link-type: doc
    .. grid-item-card:: :octicon:`cpu;1em;` OpenSearch
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/opensearch
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Robusta
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/robusta
        :link-type: doc

    .. grid-item-card:: :octicon:`cpu;1em;` Slab
        :class-card: sd-bg-light sd-bg-text-light
        :link: toolsets/slab
        :link-type: doc




Enabling / Disabling Toolsets
-----------------------------

You can enable or disable toolsets with the ``holmes.toolsets`` Helm value:

.. code-block:: yaml
    enableHolmesGPT: true
    holmes:
      toolsets:
        kubernetes/logs:
          enabled: false # disable the builtin kubernetes/logs toolset - e.g. if you want Holmes to only read logs from Loki instead (requires enabling a loki toolset)

After making changes, apply them using Helm:

.. code-block:: bash

    helm upgrade robusta robusta/robusta --values=generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>


You can override fields from the default toolsets to customize them for your needs.
For example:

.. code-block:: yaml
    enableHolmesGPT: true
    holmes:
      toolsets:
      confluence:
      description: "Enhanced Confluence toolset for fetching and searching pages."
      prerequisites:
        - command: "curl --version"
        - env:
          - CONFLUENCE_USER
          - CONFLUENCE_API_KEY
          - CONFLUENCE_BASE_URL
      tools:
      - name: "search_confluence_pages"
        description: "Search for pages in Confluence using a query string."
        user_description: "search confluence for pages containing {{ query_string }}"
        command: "curl -u ${CONFLUENCE_USER}:${CONFLUENCE_API_KEY} -X GET -H 'Content-Type: application/json' ${CONFLUENCE_BASE_URL}/wiki/rest/api/content/search?cql=text~{{ query_string }}"

      - name: "fetch_pages_with_label"
        description: "Fetch all pages in Confluence with a specific label."
        user_description: "fetch all confluence pages with label {{ label }}"
        command: "curl -u ${CONFLUENCE_USER}:${CONFLUENCE_API_KEY} -X GET -H 'Content-Type: application/json' ${CONFLUENCE_BASE_URL}/wiki/rest/api/content/?expand=body.storage&label={{ label }}"
