Health Probes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta ships without Kubernetes health probes. If your platform requires them - for example a policy that
rejects containers with no ``livenessProbe`` - you can define them yourself on the runner and the forwarder.

Nothing is rendered unless you set it, so the default install is unaffected.

Available Endpoints
-------------------------------------

The runner serves HTTP on port ``5000``, named ``http``:

* ``/metrics`` - available as soon as the web server starts, independent of any external service.
* ``/healthz`` - ``200`` only when every configured sink reports healthy, ``500`` otherwise.

The forwarder serves ``/metrics`` on port ``2112``, named ``metrics``. It has no ``/healthz``; any other path
returns ``404``. The port is bound at process start, before the watch loop syncs.

Recommended Configuration
-------------------------------------

.. code-block:: yaml

    runner:
      startupProbe:
        httpGet:
          path: /metrics
          port: http
        failureThreshold: 30
        periodSeconds: 10
      livenessProbe:
        httpGet:
          path: /metrics
          port: http
        periodSeconds: 30
      readinessProbe:
        httpGet:
          path: /healthz
          port: http
        periodSeconds: 15

    kubewatch:
      livenessProbe:
        httpGet:
          path: /metrics
          port: metrics
        periodSeconds: 15

Any probe field Kubernetes accepts can be used, including ``tcpSocket`` and ``exec``.

Choosing an Endpoint
-------------------------------------

Use ``/metrics`` for liveness. It restarts the pod only when the process is genuinely wedged.

Avoid ``/healthz`` for liveness. Because it tracks sink health, a transient outage at Slack or another sink
would restart the runner repeatedly while nothing is wrong with the runner itself. Robusta shipped a liveness
probe on ``/healthz`` in early 2023 and removed it again for this reason.

``/healthz`` is a reasonable readiness endpoint if you want a sink-aware signal - it takes the pod out of the
Service and blocks a rollout from proceeding, without restarting anything.

Note that probes are not how you detect a misconfigured install. A runner that cannot reach the Kubernetes API,
or a forwarder without a usable kubeconfig, exits at startup and lands in ``CrashLoopBackOff``, which Kubernetes
already reports on its own.

Why Reference Ports By Name
-------------------------------------

Both containers declare their port with a name, and the examples above use the name rather than ``5000`` or
``2112``. Prefer the name in anything you write yourself:

* **The number stops being repeated.** A probe that says ``port: http`` keeps working if the listen port
  changes. A probe hardcoding ``5000`` has to be found and updated, and silently probes the wrong port until
  someone notices.
* **It says what the port is for.** ``port: http`` is readable in a review; ``port: 5000`` needs a lookup.
* **Other Kubernetes objects resolve names too.** NetworkPolicy rules and Prometheus Operator scrape configs
  accept a container port name and resolve it per pod, so one rename does not have to be chased across objects.
* **A typo says so.** A probe naming a port no container declares reports
  ``port "..." not found``. A probe with the wrong number reports a generic connection refused, which looks
  the same as an application that is genuinely down.

Port names are more constrained than Service port names: at most 15 characters, lowercase alphanumeric and
dashes, and unique within the pod.

One place to keep using the number is a Service ``targetPort``, which is why both Services still say
``targetPort: 5000`` and ``targetPort: 2112``. A numeric ``targetPort`` resolves whether or not the pod
declares the name, while a named one resolves per pod - so during an upgrade from a chart version whose pods
had no named port, pods stay ``Ready`` but their endpoints are published with no port at all, and the Service
black-holes traffic until the rollout finishes.
