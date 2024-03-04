import abc


class EventEmitter:
    @abc.abstractmethod
    def emit_event(self, event_name: str, **kwargs):
        pass
