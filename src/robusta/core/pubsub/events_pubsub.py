from collections import defaultdict
from typing import Dict

from robusta.core.pubsub.event_emitter import EventEmitter
from robusta.core.pubsub.event_subscriber import EventHandler, EventSubscriber


class EventsPubSub(EventEmitter, EventSubscriber):
    event_handlers: defaultdict[str, Dict[str, EventHandler]]

    def __init__(self):
        self.event_handlers = defaultdict(dict)

    def subscribe(self, subscriber_name: str, event_name: str, handler: EventHandler):
        self.event_handlers[event_name][subscriber_name] = handler

    def unsubscribe(self, subscriber_name: str, event_name: str):
        if subscriber_name in self.event_handlers[event_name].keys():
            del self.event_handlers[event_name][subscriber_name]

    def emit_event(self, event_name: str, **kwargs):
        for handler in self.event_handlers[event_name].values():
            handler.handle_event(event_name, **kwargs)
