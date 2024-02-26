import os
import sys

from robusta.core.model.env_vars import RUN_AS_SUBPROCESS


def process_setup():
    if RUN_AS_SUBPROCESS:
        if os.fork():
            # Parent process, pid 1 in our deployment scenario. Wait (blocking - doesn't
            # utilitze any CPU) for the forked "main" process to exit (if it ever does)
            os.wait()
            # At this point we are sure no subprocesses are running, so we can safely
            # exit the pid 1 process, effectively causing the Docker image (and thus
            # the k8s pod) to terminate.
            sys.exit(1)

        # Child process; create a process group to conveniently terminate the process
        # along with subprocesses if need be via killpg. Currently the only use is in
        # robusta.runner.config_loader.ConfigLoader.__reload_playbook_packages.
        os.setpgrp()
