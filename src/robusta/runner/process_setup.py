import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor

from robusta.core.model.env_vars import RUN_AS_SUBPROCESS

# TASK_PROCESSPOOL_SIZE = int(os.environ.get("TASK_PROCESSPOOL_SIZE", 10))

master_pid = None
# master_process_pool = None


def process_setup():
    global master_pid, master_process_pool

    print("process_setup...")
    if RUN_AS_SUBPROCESS:
        if os.fork():
            print("parent, sleeping...")
            # Parent process, pid 1 in our deployment scenario. Wait (blocking - doesn't
            # utilize any CPU) for the forked "main" process to exit (if it ever does)
            os.wait()
            # At this point we are sure no subprocesses are running, so we can safely
            # exit the pid 1 process, effectively causing the Docker image (and thus
            # the k8s pod) to terminate.
            print("parent terminating?!")
            sys.exit(1)

        print("child, running...")
        # Child process; create a process group to conveniently terminate the process
        # along with subprocesses if need be via killpg. Currently, the only use is in
        # robusta.runner.config_loader.ConfigLoader.__reload_playbook_packages.
        os.setpgrp()

    print(f"setting up master_* for pid {os.getpid()}")
    master_pid = os.getpid()
    # master_process_pool = ProcessPoolExecutor(max_workers=TASK_PROCESSPOOL_SIZE)
