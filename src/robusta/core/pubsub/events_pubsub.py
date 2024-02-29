from collections import defaultdict
from weakref import WeakSet

from robusta.core.pubsub.event_emitter import EventEmitter
from robusta.core.pubsub.event_subscriber import EventHandler, EventSubscriber


class EventsPubSub(EventEmitter, EventSubscriber):
    def __init__(self) -> None:
        self.event_handlers: defaultdict[str, WeakSet[EventHandler]] = defaultdict(WeakSet)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self.event_handlers[event_name].add(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        self.event_handlers[event_name].remove(handler)

    def emit_event(self, event_name: str, **kwargs) -> None:
        for handler in self.event_handlers[event_name]:
            handler.handle_event(event_name, **kwargs)
