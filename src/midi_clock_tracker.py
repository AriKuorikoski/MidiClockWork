import time
from midi_message import CLOCK, START, CONTINUE, STOP

TICKS_PER_BEAT = 24


class MidiClockTracker:
    def __init__(self, event_bus):
        self.bus = event_bus
        self._tick_count = 0
        self._last_ns = 0
        self._bpm = 0.0
        self._running = False
        # Average over 24 ticks (1 beat) for stable BPM
        self._tick_intervals = []
        self._max_intervals = TICKS_PER_BEAT
        # Smooth BPM over last 10 readings to filter jitter
        self._bpm_history = []
        self._max_bpm_history = 10

    @property
    def bpm(self):
        return self._bpm

    @property
    def running(self):
        return self._running

    def process(self, msg):
        if msg.type == CLOCK:
            self._on_tick()
        elif msg.type == START:
            self._running = True
            self._tick_count = 0
            self._tick_intervals = []
            self._bpm_history = []
            self.bus.emit("transport", "start")
        elif msg.type == CONTINUE:
            self._running = True
            self.bus.emit("transport", "continue")
        elif msg.type == STOP:
            self._running = False
            self.bus.emit("transport", "stop")

    def _on_tick(self):
        now_ns = time.monotonic_ns()

        # Calculate interval
        if self._last_ns > 0:
            interval = now_ns - self._last_ns
            self._tick_intervals.append(interval)
            if len(self._tick_intervals) > self._max_intervals:
                self._tick_intervals.pop(0)

            # Recalculate BPM when we have enough samples
            if len(self._tick_intervals) >= TICKS_PER_BEAT:
                avg_ns = sum(self._tick_intervals) / len(self._tick_intervals)
                new_bpm = 60_000_000_000 / (avg_ns * TICKS_PER_BEAT)
                self._bpm_history.append(new_bpm)
                if len(self._bpm_history) > self._max_bpm_history:
                    self._bpm_history.pop(0)
                smoothed = sum(self._bpm_history) / len(self._bpm_history)
                if round(smoothed) != round(self._bpm):
                    self._bpm = smoothed
                    self.bus.emit("tempo_changed", self._bpm)

        self._last_ns = now_ns

        # Beat tracking
        self._tick_count += 1
        if self._tick_count >= TICKS_PER_BEAT:
            self._tick_count = 0
            self.bus.emit("beat")
