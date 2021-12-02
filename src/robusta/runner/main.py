import os
import os.path
from inspect import getmembers
import manhole

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
    Web.init(event_handler)
    Web.run()  # blocking
    loader.close()


if __name__ == "__main__":
    main()
