import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock MicroPython's time module before importing tracker
import time

class MockTime:
    def __init__(self):
        self._ns = 0

    def monotonic_ns(self):
        return self._ns

    def advance_ns(self, ns):
        self._ns += ns

mock_time = MockTime()
time.monotonic_ns = mock_time.monotonic_ns

from event_bus import EventBus
from midi_message import MidiMessage, CLOCK, START, STOP, CONTINUE
from midi_clock_tracker import MidiClockTracker


def make_tracker():
    mock_time._ns = 0
    time.monotonic_ns = mock_time.monotonic_ns
    bus = EventBus()
    tracker = MidiClockTracker(bus)
    return bus, tracker


def clock_msg():
    return MidiMessage(CLOCK)


def test_beat_every_24_ticks():
    bus, tracker = make_tracker()
    beats = []
    bus.on("beat", lambda: beats.append(True))

    tick_ns = 20_833_000
    for i in range(48):  # 2 beats
        mock_time.advance_ns(tick_ns)
        tracker.process(clock_msg())

    assert len(beats) == 2


def test_tempo_changed_event():
    bus, tracker = make_tracker()
    tempos = []
    bus.on("tempo_changed", lambda bpm: tempos.append(bpm))

    tick_ns = 20_833_000  # ~120 BPM
    for i in range(25):
        mock_time.advance_ns(tick_ns)
        tracker.process(clock_msg())

    assert len(tempos) == 1
    assert abs(tempos[0] - 120.0) < 1.0


def test_tempo_change_detection():
    bus, tracker = make_tracker()
    tempos = []
    bus.on("tempo_changed", lambda bpm: tempos.append(bpm))

    tick_ns_120 = 20_833_000
    for i in range(25):
        mock_time.advance_ns(tick_ns_120)
        tracker.process(clock_msg())

    tick_ns_90 = 27_778_000
    for i in range(50):  # extra ticks for smoothing buffer to settle
        mock_time.advance_ns(tick_ns_90)
        tracker.process(clock_msg())

    assert len(tempos) >= 2
    assert abs(tempos[0] - 120.0) < 1.0
    assert abs(tempos[-1] - 90.0) < 1.0


def test_start_stop_transport():
    bus, tracker = make_tracker()
    events = []
    bus.on("transport", lambda state: events.append(state))

    tracker.process(MidiMessage(START))
    assert tracker.running == True
    assert events == ["start"]

    tracker.process(MidiMessage(STOP))
    assert tracker.running == False
    assert events == ["start", "stop"]


def test_continue_transport():
    bus, tracker = make_tracker()
    events = []
    bus.on("transport", lambda state: events.append(state))

    tracker.process(MidiMessage(START))
    tracker.process(MidiMessage(STOP))
    tracker.process(MidiMessage(CONTINUE))
    assert tracker.running == True
    assert events == ["start", "stop", "continue"]


def test_start_resets_tick_count():
    bus, tracker = make_tracker()
    beats = []
    bus.on("beat", lambda: beats.append(True))

    tick_ns = 20_833_000
    for i in range(12):
        mock_time.advance_ns(tick_ns)
        tracker.process(clock_msg())

    tracker.process(MidiMessage(START))

    for i in range(24):
        mock_time.advance_ns(tick_ns)
        tracker.process(clock_msg())

    assert len(beats) == 1
