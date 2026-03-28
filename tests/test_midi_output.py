import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from event_bus import EventBus
from midi_message import MidiMessage, NOTE_ON, CC, PC, CLOCK
from midi_output import MidiOutput


class MockUart:
    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(data)


def test_forwards_messages():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    msg = MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)
    bus.emit("midi_out", msg)
    assert len(uart.written) == 1
    assert uart.written[0] == bytes([0x90, 60, 100])


def test_filter_blocks_clock():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    output.add_filter(lambda msg: msg.type != CLOCK)

    bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uart.written) == 0

    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    assert len(uart.written) == 1


def test_filter_blocks_channel():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    # Block channel 10 (index 9)
    output.add_filter(lambda msg: msg.channel != 9)

    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=9, data1=36, data2=127))
    assert len(uart.written) == 0

    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    assert len(uart.written) == 1


def test_filter_blocks_specific_cc():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    # Block CC 7 (volume)
    output.add_filter(lambda msg: not (msg.type == CC and msg.data1 == 7))

    bus.emit("midi_out", MidiMessage(CC, channel=0, data1=7, data2=100))
    assert len(uart.written) == 0

    bus.emit("midi_out", MidiMessage(CC, channel=0, data1=11, data2=64))
    assert len(uart.written) == 1


def test_filter_blocks_pc():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    output.add_filter(lambda msg: msg.type != PC)

    bus.emit("midi_out", MidiMessage(PC, channel=0, data1=5))
    assert len(uart.written) == 0


def test_multiple_filters():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    output.add_filter(lambda msg: msg.type != CLOCK)
    output.add_filter(lambda msg: msg.channel != 9 if msg.channel is not None else True)

    bus.emit("midi_out", MidiMessage(CLOCK))                                    # blocked
    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=9, data1=36, data2=127))  # blocked
    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))  # passes
    assert len(uart.written) == 1


def test_remove_filter():
    bus = EventBus()
    uart = MockUart()
    output = MidiOutput("out1", uart, bus)

    block_clock = lambda msg: msg.type != CLOCK
    output.add_filter(block_clock)

    bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uart.written) == 0

    output.remove_filter(block_clock)

    bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uart.written) == 1


def test_multiple_outputs_independent():
    bus = EventBus()
    uart1 = MockUart()
    uart2 = MockUart()
    out1 = MidiOutput("out1", uart1, bus)
    out2 = MidiOutput("out2", uart2, bus)

    out1.add_filter(lambda msg: msg.type != CLOCK)

    bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uart1.written) == 0
    assert len(uart2.written) == 1
    assert uart2.written[0] == bytes([0xF8])
