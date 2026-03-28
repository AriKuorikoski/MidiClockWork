import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
from midi_message import MidiMessage, NOTE_ON, CC, CLOCK, START
from midi_clock_tracker import MidiClockTracker
from midi_router import MidiRouter


def make_router():
    mock_time._us = 0
    bus = EventBus()
    clock = MidiClockTracker(bus)
    router = MidiRouter(bus, clock)
    return bus, clock, router




def test_forwards_midi_in_to_midi_out():
    bus, clock, router = make_router()
    received = []
    bus.on("midi_out", lambda msg: received.append(msg))

    msg = MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)
    bus.emit("midi_in", msg)

    assert len(received) == 1
    assert received[0].type == NOTE_ON


def test_clock_reaches_tracker():
    bus, clock, router = make_router()
    beats = []
    bus.on("beat", lambda: beats.append(True))

    tick_us = 20833
    for i in range(24):
        mock_time.advance_us(tick_us)
        bus.emit("midi_in", MidiMessage(CLOCK))

    assert len(beats) == 1


def test_transport_reaches_tracker():
    bus, clock, router = make_router()

    bus.emit("midi_in", MidiMessage(START))
    assert clock.running == True


def test_non_clock_messages_forwarded():
    bus, clock, router = make_router()
    received = []
    bus.on("midi_out", lambda msg: received.append(msg))

    bus.emit("midi_in", MidiMessage(CC, channel=0, data1=7, data2=100))
    bus.emit("midi_in", MidiMessage(CLOCK))

    assert len(received) == 2
    assert received[0].type == CC
    assert received[1].type == CLOCK
