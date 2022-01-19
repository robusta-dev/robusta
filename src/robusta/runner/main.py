import os
import os.path
from inspect import getmembers
import manhole
import sentry_sdk

from .log_init import init_logging
from .web import Web
from ..core.playbooks.playbooks_event_handler_impl import PlaybooksEventHandlerImpl
from .. import api as robusta_api
from .config_loader import ConfigLoader
from ..model.config import Registry


def main():
    init_logging()
    registry = Registry()
    event_handler = PlaybooksEventHandlerImpl(registry)
    loader = ConfigLoader(registry, event_handler)
    if os.environ.get("ENABLE_MANHOLE", "false").lower() == "true":
        manhole.install(locals=dict(getmembers(robusta_api)))

    sentry_dsn = os.environ.get("SECRET_SENTRY_DSN", "")
    if sentry_dsn:
        sentry_sdk.init(sentry_dsn, traces_sample_rate=0.5)
  
    Web.init(event_handler)
    Web.run()  # blocking
    loader.close()


if __name__ == "__main__":
    main()
