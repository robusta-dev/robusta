Health Probes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Robusta ships without Kubernetes health probes. If your platform requires them - for example a policy that
rejects containers with no ``livenessProbe`` - you can define them yourself on the runner and the forwarder.

Nothing is rendered unless you set it, so the default install is unaffected.

Available Endpoints
-------------------------------------

The runner serves HTTP on port ``5000``:

* ``/metrics`` - available as soon as the web server starts, independent of any external service.
* ``/healthz`` - ``200`` only when every configured sink reports healthy, ``500`` otherwise.

The forwarder serves ``/metrics`` on port ``2112``. It has no ``/healthz``; any other path returns ``404``.
The port is bound at process start, before the watch loop syncs.

Neither container declares named ports, so probe ports must be numeric.

Recommended Configuration
-------------------------------------

.. code-block:: yaml

    runner:
      startupProbe:
        httpGet:
          path: /metrics
          port: 5000
        failureThreshold: 30
        periodSeconds: 10
      livenessProbe:
        httpGet:
          path: /metrics
          port: 5000
        periodSeconds: 30
      readinessProbe:
        httpGet:
          path: /healthz
          port: 5000
        periodSeconds: 15

    kubewatch:
      livenessProbe:
        httpGet:
          path: /metrics
          port: 2112
        periodSeconds: 30
      readinessProbe:
        httpGet:
          path: /metrics
          port: 2112
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
