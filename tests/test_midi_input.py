import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from event_bus import EventBus
from midi_message import NOTE_ON, NOTE_OFF, CC, PC, CLOCK, START, STOP
from midi_input import MidiInput


class MockUart:
    def __init__(self):
        self._data = b''

    def send(self, data):
        """Feed bytes into the mock UART."""
        self._data += bytes(data)

    def read(self):
        if self._data:
            result = self._data
            self._data = b''
            return result
        return None


def make_input():
    bus = EventBus()
    uart = MockUart()
    midi_in = MidiInput("IN", uart, bus)
    received = []
    bus.on("midi_in", lambda msg: received.append(msg))
    return midi_in, uart, received


def test_parse_note_on():
    midi_in, uart, received = make_input()
    uart.send([0x90, 60, 100])
    midi_in.poll()
    assert len(received) == 1
    assert received[0].type == NOTE_ON
    assert received[0].channel == 0
    assert received[0].data1 == 60
    assert received[0].data2 == 100


def test_parse_note_off():
    midi_in, uart, received = make_input()
    uart.send([0x80, 60, 0])
    midi_in.poll()
    assert len(received) == 1
    assert received[0].type == NOTE_OFF


def test_parse_cc():
    midi_in, uart, received = make_input()
    uart.send([0xB0, 7, 100])
    midi_in.poll()
    assert len(received) == 1
    assert received[0].type == CC
    assert received[0].data1 == 7
    assert received[0].data2 == 100


def test_parse_pc():
    midi_in, uart, received = make_input()
    uart.send([0xC0, 42])
    midi_in.poll()
    assert len(received) == 1
    assert received[0].type == PC
    assert received[0].data1 == 42
    assert received[0].data2 is None


def test_parse_clock():
    midi_in, uart, received = make_input()
    uart.send([0xF8])
    midi_in.poll()
    assert len(received) == 1
    assert received[0].type == CLOCK


def test_parse_transport():
    midi_in, uart, received = make_input()
    uart.send([0xFA, 0xFC])
    midi_in.poll()
    assert len(received) == 2
    assert received[0].type == START
    assert received[1].type == STOP


def test_multiple_messages_in_one_read():
    midi_in, uart, received = make_input()
    uart.send([0x90, 60, 100, 0x80, 60, 0])
    midi_in.poll()
    assert len(received) == 2
    assert received[0].type == NOTE_ON
    assert received[1].type == NOTE_OFF


def test_bytes_split_across_polls():
    midi_in, uart, received = make_input()

    uart.send([0x90])
    midi_in.poll()
    assert len(received) == 0

    uart.send([60])
    midi_in.poll()
    assert len(received) == 0

    uart.send([100])
    midi_in.poll()
    assert len(received) == 1
    assert received[0].type == NOTE_ON
    assert received[0].data1 == 60


def test_clock_interleaved_with_channel_message():
    """System real-time messages can arrive mid-message without disrupting it."""
    midi_in, uart, received = make_input()

    uart.send([0x90, 0xF8, 60, 100])
    midi_in.poll()
    assert len(received) == 2
    assert received[0].type == CLOCK
    assert received[1].type == NOTE_ON
    assert received[1].data1 == 60


def test_data_bytes_without_status_ignored():
    midi_in, uart, received = make_input()
    uart.send([60, 100])  # No status byte
    midi_in.poll()
    assert len(received) == 0


def test_no_data_available():
    midi_in, uart, received = make_input()
    midi_in.poll()
    assert len(received) == 0
