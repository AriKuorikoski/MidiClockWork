import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from midi_message import MidiMessage, NOTE_ON, CC, PC, CLOCK
from uart_writer import MessageFilter, UartWriter


class MockUart:
    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(data)


# --- MessageFilter ---

def test_filter_no_criteria_matches_all():
    f = MessageFilter()
    assert f.matches(MidiMessage(CLOCK)) is True
    assert f.matches(MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)) is True
    assert f.matches(MidiMessage(CC, channel=0, data1=7, data2=100)) is True


def test_filter_by_type_matches():
    f = MessageFilter(types={CLOCK})
    assert f.matches(MidiMessage(CLOCK)) is True
    assert f.matches(MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)) is False


def test_filter_by_multiple_types():
    f = MessageFilter(types={CC, PC})
    assert f.matches(MidiMessage(CC, channel=0, data1=7, data2=100)) is True
    assert f.matches(MidiMessage(PC, channel=0, data1=5)) is True
    assert f.matches(MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)) is False


def test_filter_by_channel_matches():
    f = MessageFilter(channels={0, 1})
    assert f.matches(MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)) is True
    assert f.matches(MidiMessage(NOTE_ON, channel=1, data1=60, data2=100)) is True
    assert f.matches(MidiMessage(NOTE_ON, channel=2, data1=60, data2=100)) is False


def test_filter_by_channel_excludes_system_messages():
    f = MessageFilter(channels={0})
    assert f.matches(MidiMessage(CLOCK)) is False  # CLOCK has no channel


def test_filter_by_cc_number():
    f = MessageFilter(types={CC}, cc_numbers={7, 11})
    assert f.matches(MidiMessage(CC, channel=0, data1=7, data2=100)) is True
    assert f.matches(MidiMessage(CC, channel=0, data1=11, data2=64)) is True
    assert f.matches(MidiMessage(CC, channel=0, data1=1, data2=50)) is False


def test_filter_combines_type_and_channel():
    f = MessageFilter(types={CC}, channels={0})
    assert f.matches(MidiMessage(CC, channel=0, data1=7, data2=100)) is True
    assert f.matches(MidiMessage(CC, channel=1, data1=7, data2=100)) is False
    assert f.matches(MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)) is False


def test_filter_combines_type_channel_and_cc():
    f = MessageFilter(types={CC}, channels={0}, cc_numbers={7})
    assert f.matches(MidiMessage(CC, channel=0, data1=7, data2=100)) is True
    assert f.matches(MidiMessage(CC, channel=0, data1=11, data2=100)) is False
    assert f.matches(MidiMessage(CC, channel=1, data1=7, data2=100)) is False


# --- UartWriter ---

def test_writer_no_generate_writes_original():
    uart = MockUart()
    writer = UartWriter(uart, MessageFilter())
    msg = MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)
    writer.process(msg)
    assert uart.written == [bytes([0x90, 60, 100])]


def test_writer_with_generate_writes_generated():
    uart = MockUart()
    replacement = MidiMessage(CC, channel=0, data1=85, data2=64)
    writer = UartWriter(uart, MessageFilter(), generate=lambda msg: [replacement])
    writer.process(MidiMessage(CLOCK))
    assert uart.written == [bytes([0xB0, 85, 64])]


def test_writer_generate_returning_none_writes_nothing():
    uart = MockUart()
    writer = UartWriter(uart, MessageFilter(), generate=lambda msg: None)
    writer.process(MidiMessage(CLOCK))
    assert uart.written == []


def test_writer_generate_returning_empty_writes_nothing():
    uart = MockUart()
    writer = UartWriter(uart, MessageFilter(), generate=lambda msg: [])
    writer.process(MidiMessage(CLOCK))
    assert uart.written == []


def test_writer_generate_multiple_messages():
    uart = MockUart()
    msgs = [
        MidiMessage(CC, channel=0, data1=7, data2=100),
        MidiMessage(CC, channel=0, data1=11, data2=64),
    ]
    writer = UartWriter(uart, MessageFilter(), generate=lambda msg: msgs)
    writer.process(MidiMessage(CLOCK))
    assert len(uart.written) == 2
    assert uart.written[0] == bytes([0xB0, 7, 100])
    assert uart.written[1] == bytes([0xB0, 11, 64])

