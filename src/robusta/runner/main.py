import os

from robusta.runner.ssl_utils import add_custom_certificate

ADDITIONAL_CERTIFICATE: str = os.environ.get("CERTIFICATE", "")

if add_custom_certificate(ADDITIONAL_CERTIFICATE):
    print("added custom certificate")

# DO NOT ADD ANY CODE ABOVE THIS
# ADDING IMPORTS BEFORE ADDING THE CUSTOM CERTS MIGHT INIT HTTP CLIENTS THAT DOESN'T RESPECT THE CUSTOM CERT

import signal

from robusta.core.model.env_vars import ENABLE_TELEMETRY, ROBUSTA_TELEMETRY_ENDPOINT, TELEMETRY_PERIODIC_SEC
from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from robusta.model.config import Registry
from robusta.patch.patch import create_monkey_patches
from robusta.runner.config_loader import ConfigLoader
from robusta.runner.log_init import init_logging, logging
from robusta.runner.process_setup import process_setup
from robusta.runner.telemetry_service import TelemetryService
from robusta.runner.web import Web
from robusta.utils.server_start import ServerStart


def main():
    process_setup()
    init_logging()
    ServerStart.set()

    create_monkey_patches()
    registry = Registry()
    event_handler = PlaybooksEventHandlerImpl(registry)
    loader = ConfigLoader(registry, event_handler)
    sink_registry = registry.get_sinks()
    ui_sink_enabled = "robusta_ui_sink" in sink_registry.get_all()
    if ui_sink_enabled or ENABLE_TELEMETRY:
        if not ENABLE_TELEMETRY:
            logging.warning("Telemetry could not be disabled when Robusta UI is used.")
        TelemetryService(
            endpoint=ROBUSTA_TELEMETRY_ENDPOINT,
            periodic_time_sec=TELEMETRY_PERIODIC_SEC,
            registry=registry,
        )
    else:
        logging.info("Telemetry is disabled.")

    Web.init(event_handler, loader)

    signal.signal(signal.SIGINT, event_handler.handle_sigint)
    event_handler.set_cluster_active(True)
    Web.run()  # blocking
    loader.close()


if __name__ == "__main__":
    main()
