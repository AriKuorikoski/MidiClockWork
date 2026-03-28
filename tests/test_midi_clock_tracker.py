import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock MicroPython's time module before importing tracker
import time

class MockTime:
    def __init__(self):
        self._us = 0

    def ticks_us(self):
        return self._us

    def ticks_diff(self, a, b):
        return a - b

    def advance_us(self, us):
        self._us += us

mock_time = MockTime()
time.ticks_us = mock_time.ticks_us
time.ticks_diff = mock_time.ticks_diff

from event_bus import EventBus
from midi_message import MidiMessage, CLOCK, START, STOP, CONTINUE
from midi_clock_tracker import MidiClockTracker


def make_tracker():
    mock_time._us = 0
    bus = EventBus()
    tracker = MidiClockTracker(bus)
    return bus, tracker


def clock_msg():
    return MidiMessage(CLOCK)


def test_beat_every_24_ticks():
    bus, tracker = make_tracker()
    beats = []
    bus.on("beat", lambda: beats.append(True))

    tick_us = 20833
    for i in range(48):  # 2 beats
        mock_time.advance_us(tick_us)
        tracker.process(clock_msg())

    assert len(beats) == 2


def test_tempo_changed_event():
    bus, tracker = make_tracker()
    tempos = []
    bus.on("tempo_changed", lambda bpm: tempos.append(bpm))

    tick_us = 20833  # ~120 BPM
    for i in range(25):
        mock_time.advance_us(tick_us)
        tracker.process(clock_msg())

    assert len(tempos) == 1
    assert abs(tempos[0] - 120.0) < 1.0


def test_tempo_change_detection():
    bus, tracker = make_tracker()
    tempos = []
    bus.on("tempo_changed", lambda bpm: tempos.append(bpm))

    tick_us_120 = 20833
    for i in range(25):
        mock_time.advance_us(tick_us_120)
        tracker.process(clock_msg())

    tick_us_90 = 27778
    for i in range(25):
        mock_time.advance_us(tick_us_90)
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

    tick_us = 20833
    for i in range(12):
        mock_time.advance_us(tick_us)
        tracker.process(clock_msg())

    tracker.process(MidiMessage(START))

    for i in range(24):
        mock_time.advance_us(tick_us)
        tracker.process(clock_msg())

    assert len(beats) == 1
