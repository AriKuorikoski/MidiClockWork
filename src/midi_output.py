class MidiOutput:
    def __init__(self, name, bus, writer, tempo_handler=None):
        self.name = name
        self.bus = bus
        self._writer = writer
        self._tempo_handler = tempo_handler

        bus.on("midi_out", self._on_message)
        bus.on("tempo_changed", self._on_tempo_changed)

    def _on_message(self, msg):
        if self._writer.filter.matches(msg):
            self._writer.process(msg)

    def _on_tempo_changed(self, bpm):
        if self._tempo_handler is None:
            return
        for msg in self._tempo_handler.handle(bpm):
            if self._writer.filter.matches(msg):
                self._writer.process(msg)
