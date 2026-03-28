class MidiRouter:
    def __init__(self, bus, clock_tracker):
        self.bus = bus
        self.clock_tracker = clock_tracker

        bus.on("midi_in", self._on_midi_in)

    def _on_midi_in(self, msg):
        self.clock_tracker.process(msg)
        self.bus.emit("midi_out", msg)
