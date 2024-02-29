import abc


class EventHandler:
    @abc.abstractmethod
    def handle_event(self, event_name: str, **kwargs):
        pass


class EventSubscriber:
    @abc.abstractmethod
    def subscribe(self, event_name: str, handler: EventHandler):
        pass

    @abc.abstractmethod
    def unsubscribe(self, event_name: str, handler: EventHandler):
        pass
