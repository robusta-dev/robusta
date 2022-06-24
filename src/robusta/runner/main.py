import os
import os.path
from inspect import getmembers
import manhole

from .telemetry_service import TelemetryService, TelemetryLevel
from .log_init import logging, init_logging
from .web import Web
from ..core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from .. import api as robusta_api
from .config_loader import ConfigLoader
from ..model.config import Registry
from ..core.model.env_vars import ROBUSTA_TELEMETRY_ENDPOINT, SEND_ADDITIONAL_TELEMETRY, \
 ENABLE_TELEMETRY, TELEMETRY_PERIODIC_SEC

def main():
    init_logging()
    registry = Registry()
    event_handler = PlaybooksEventHandlerImpl(registry)
    loader = ConfigLoader(registry, event_handler)

    if ENABLE_TELEMETRY:    
        telemetry_service = TelemetryService(
            telemetry_level= TelemetryLevel.ERROR if SEND_ADDITIONAL_TELEMETRY else TelemetryLevel.USAGE,
            endpoint=ROBUSTA_TELEMETRY_ENDPOINT,
            periodic_time_sec= TELEMETRY_PERIODIC_SEC,
            registry= registry,
            )
    else:
        logging.info(f"Telemetry is disabled.")

    if os.environ.get("ENABLE_MANHOLE", "false").lower() == "true":
        manhole.install(locals=dict(getmembers(robusta_api)))

    
    Web.init(event_handler, loader)
    Web.run()  # blocking
    loader.close()



if __name__ == "__main__":
    main()
