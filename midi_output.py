class MidiOutput:
    def __init__(self, name, uart, bus):
        self.name = name
        self.uart = uart
        self.bus = bus
        self._filters = []

        bus.on("midi_out", self._on_message)

    def add_filter(self, filter_fn):
        self._filters.append(filter_fn)

    def remove_filter(self, filter_fn):
        self._filters.remove(filter_fn)

    def _on_message(self, msg):
        for f in self._filters:
            if not f(msg):
                return
        self._write_data(msg)

    def _write_data(self, msg):
        self.uart.write(msg.serialize())
