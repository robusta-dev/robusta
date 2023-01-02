import os
import os.path

from robusta.core.model.env_vars import (
    ENABLE_TELEMETRY,
    ROBUSTA_TELEMETRY_ENDPOINT,
    SEND_ADDITIONAL_TELEMETRY,
    TELEMETRY_PERIODIC_SEC,
)
from robusta.core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from robusta.model.config import Registry
from robusta.patch.patch import create_monkey_patches
from robusta.runner.config_loader import ConfigLoader
from robusta.runner.log_init import init_logging, logging
from robusta.runner.ssl_utils import add_custom_certificate
from robusta.runner.telemetry_service import TelemetryLevel, TelemetryService
from robusta.runner.web import Web


def main():
    init_logging()
    if add_custom_certificate(os.environ.get("CERTIFICATE", "")):
        logging.info("added custom certificate")

    create_monkey_patches()
    registry = Registry()
    event_handler = PlaybooksEventHandlerImpl(registry)
    loader = ConfigLoader(registry, event_handler)

    if ENABLE_TELEMETRY:
        TelemetryService(
            telemetry_level=TelemetryLevel.ERROR if SEND_ADDITIONAL_TELEMETRY else TelemetryLevel.USAGE,
            endpoint=ROBUSTA_TELEMETRY_ENDPOINT,
            periodic_time_sec=TELEMETRY_PERIODIC_SEC,
            registry=registry,
        )
    else:
        logging.info("Telemetry is disabled.")

    Web.init(event_handler, loader)
    Web.run()  # blocking
    loader.close()


if __name__ == "__main__":
    main()
