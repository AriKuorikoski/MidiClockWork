import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from event_bus import EventBus
from midi_message import MidiMessage, NOTE_ON, CC, PC, CLOCK
from midi_output import MidiOutput
from uart_writer import MessageFilter, UartWriter
from tempo_to_cc import TempoHandler, ValetonTempoHandler


class MockUart:
    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(data)


def make_output(msg_filter=None, tempo_handler=None):
    bus = EventBus()
    uart = MockUart()
    writer = UartWriter(uart, msg_filter or MessageFilter())
    output = MidiOutput("out1", bus, writer, tempo_handler)
    return bus, output, uart


def test_matching_message_is_written():
    bus, output, uart = make_output(MessageFilter(types={NOTE_ON}))
    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    assert len(uart.written) == 1
    assert uart.written[0] == bytes([0x90, 60, 100])


def test_non_matching_message_is_blocked():
    bus, output, uart = make_output(MessageFilter(types={NOTE_ON}))
    bus.emit("midi_out", MidiMessage(CLOCK))
    assert uart.written == []


def test_filter_by_channel():
    bus, output, uart = make_output(MessageFilter(channels={0}))
    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=1, data1=60, data2=100))
    assert len(uart.written) == 1


def test_filter_by_cc_number():
    bus, output, uart = make_output(MessageFilter(types={CC}, cc_numbers={7}))
    bus.emit("midi_out", MidiMessage(CC, channel=0, data1=7, data2=100))
    bus.emit("midi_out", MidiMessage(CC, channel=0, data1=11, data2=64))
    assert len(uart.written) == 1
    assert uart.written[0] == bytes([0xB0, 7, 100])


def test_no_filter_passes_all():
    bus, output, uart = make_output(MessageFilter())
    bus.emit("midi_out", MidiMessage(CLOCK))
    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    assert len(uart.written) == 2


def test_writer_with_generate_transforms_message():
    bus = EventBus()
    uart = MockUart()
    replacement = MidiMessage(CC, channel=0, data1=85, data2=64)
    writer = UartWriter(uart, MessageFilter(types={CLOCK}), generate=lambda msg: [replacement])
    output = MidiOutput("out1", bus, writer)
    bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uart.written) == 1
    assert uart.written[0] == bytes([0xB0, 85, 64])


def test_no_tempo_handler_ignores_tempo_change():
    bus, output, uart = make_output()
    bus.emit("tempo_changed", 120.0)
    assert uart.written == []


def test_base_tempo_handler_ignores_tempo_change():
    bus, output, uart = make_output(tempo_handler=TempoHandler())
    bus.emit("tempo_changed", 120.0)
    assert uart.written == []


def test_valeton_handler_writes_cc_on_tempo_change():
    bus, output, uart = make_output(tempo_handler=ValetonTempoHandler(channels=[0]))
    bus.emit("tempo_changed", 120.0)
    assert len(uart.written) == 2
    assert uart.written[0] == bytes([0xB0, 73, 0])
    assert uart.written[1] == bytes([0xB0, 74, 120])


def test_valeton_handler_uses_channel():
    bus, output, uart = make_output(tempo_handler=ValetonTempoHandler(channels=[3]))
    bus.emit("tempo_changed", 120.0)
    assert uart.written[0] == bytes([0xB3, 73, 0])
    assert uart.written[1] == bytes([0xB3, 74, 120])


def test_valeton_multi_channel_writes_pair_per_channel():
    bus, output, uart = make_output(tempo_handler=ValetonTempoHandler(channels=[0, 1]))
    bus.emit("tempo_changed", 120.0)
    assert len(uart.written) == 4
    assert uart.written[0] == bytes([0xB0, 73, 0])
    assert uart.written[1] == bytes([0xB0, 74, 120])
    assert uart.written[2] == bytes([0xB1, 73, 0])
    assert uart.written[3] == bytes([0xB1, 74, 120])


def test_two_outputs_are_independent():
    bus = EventBus()
    uart1 = MockUart()
    uart2 = MockUart()
    out1 = MidiOutput("out1", bus, UartWriter(uart1, MessageFilter(types={CLOCK})))
    out2 = MidiOutput("out2", bus, UartWriter(uart2, MessageFilter()))

    bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uart1.written) == 1
    assert len(uart2.written) == 1

    bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    assert len(uart1.written) == 1
    assert len(uart2.written) == 2


def test_valeton_cc_blocked_by_output_cc_number_filter():
    # If the output filter excludes CC73/74, tempo CCs are silently dropped.
    # This test documents that behaviour so it's visible if the design changes.
    bus, output, uart = make_output(
        MessageFilter(types={CC}, cc_numbers={7, 11}),  # excludes CC73 and CC74
        tempo_handler=ValetonTempoHandler(channels=[0])
    )
    bus.emit("tempo_changed", 120.0)
    assert uart.written == []  # silently dropped by the output filter


def test_tempo_only_affects_output_with_valeton_handler():
    bus = EventBus()
    uart1 = MockUart()
    uart2 = MockUart()
    out1 = MidiOutput("out1", bus, UartWriter(uart1, MessageFilter()))
    out2 = MidiOutput("out2", bus, UartWriter(uart2, MessageFilter()), ValetonTempoHandler(channels=[0]))

    bus.emit("tempo_changed", 120.0)

    assert uart1.written == []
    assert len(uart2.written) == 2
