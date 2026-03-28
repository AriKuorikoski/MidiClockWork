import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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


# --- Input filter ---

def make_filtered_input(input_filter):
    bus = EventBus()
    uart = MockUart()
    midi_in = MidiInput("IN", uart, bus, input_filter=input_filter)
    received = []
    bus.on("midi_in", lambda msg: received.append(msg))
    return midi_in, uart, received


def test_filter_allows_matching_channel():
    midi_in, uart, received = make_filtered_input({"channels": {0}, "include_global": True})
    uart.send([0x90, 60, 100])  # NOTE_ON ch0
    midi_in.poll()
    assert len(received) == 1


def test_filter_blocks_non_matching_channel():
    midi_in, uart, received = make_filtered_input({"channels": {0}, "include_global": True})
    uart.send([0x91, 60, 100])  # NOTE_ON ch1
    midi_in.poll()
    assert len(received) == 0


def test_filter_passes_global_when_include_global_true():
    midi_in, uart, received = make_filtered_input({"channels": {0}, "include_global": True})
    uart.send([0xF8])  # CLOCK — no channel
    midi_in.poll()
    assert len(received) == 1


def test_filter_blocks_global_when_include_global_false():
    midi_in, uart, received = make_filtered_input({"channels": {0}, "include_global": False})
    uart.send([0xF8])  # CLOCK
    midi_in.poll()
    assert len(received) == 0


def test_filter_none_passes_all():
    midi_in, uart, received = make_filtered_input(None)
    uart.send([0x95, 60, 100])  # NOTE_ON ch5
    uart.send([0xF8])
    midi_in.poll()
    assert len(received) == 2


def test_two_inputs_independent_filters():
    bus = EventBus()
    uart0 = MockUart()
    uart1 = MockUart()
    in0 = MidiInput("IN0", uart0, bus, input_filter={"channels": {0}, "include_global": False})
    in1 = MidiInput("IN1", uart1, bus, input_filter={"channels": {1}, "include_global": False})
    received = []
    bus.on("midi_in", lambda msg: received.append(msg))

    uart0.send([0x90, 60, 100])  # ch0 from in0 — passes in0 filter
    in0.poll()
    uart1.send([0x91, 60, 100])  # ch1 from in1 — passes in1 filter
    in1.poll()
    uart0.send([0x91, 60, 100])  # ch1 from in0 — blocked by in0 filter
    in0.poll()

    assert len(received) == 2
    assert received[0].channel == 0
    assert received[1].channel == 1
