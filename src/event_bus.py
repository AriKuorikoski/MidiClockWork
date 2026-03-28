class EventBus:
    def __init__(self):
        self._handlers = {}

    def on(self, event, handler):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def off(self, event, handler):
        if event in self._handlers and handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def emit(self, event, *args, **kwargs):
        if event in self._handlers:
            for handler in self._handlers[event]:
                handler(*args, **kwargs)
