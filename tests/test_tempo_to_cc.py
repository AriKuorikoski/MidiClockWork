import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from midi_message import MidiMessage, CC
from tempo_to_cc import TempoHandler, ValetonTempoHandler


# --- _bpm_to_cc (tested via ValetonTempoHandler instance) ---

def bpm_to_cc(bpm):
    return ValetonTempoHandler()._bpm_to_cc(bpm)


def test_bpm_40_is_range0():
    msb, lsb = bpm_to_cc(40)
    assert msb == 0
    assert lsb == 40

def test_bpm_127_is_range0():
    msb, lsb = bpm_to_cc(127)
    assert msb == 0
    assert lsb == 127

def test_bpm_128_is_range1():
    msb, lsb = bpm_to_cc(128)
    assert msb == 1
    assert lsb == 0

def test_bpm_255_is_range1():
    msb, lsb = bpm_to_cc(255)
    assert msb == 1
    assert lsb == 127

def test_bpm_256_is_range2():
    msb, lsb = bpm_to_cc(256)
    assert msb == 2
    assert lsb == 0

def test_bpm_260_is_range2():
    msb, lsb = bpm_to_cc(260)
    assert msb == 2
    assert lsb == 4

def test_bpm_rounds_to_nearest_int():
    msb, lsb = bpm_to_cc(120.6)
    assert msb == 0
    assert lsb == 121

def test_bpm_below_min_returns_none():
    assert bpm_to_cc(1) is None
    assert bpm_to_cc(39) is None

def test_bpm_above_max_returns_none():
    assert bpm_to_cc(261) is None
    assert bpm_to_cc(999) is None

def test_bpm_midrange():
    msb, lsb = bpm_to_cc(180)
    assert msb == 1
    assert lsb == 52  # 180 - 128


# --- TempoHandler (base / null object) ---

class MockWriter:
    def __init__(self):
        self.processed = []

    def process(self, msg):
        self.processed.append(msg)


def test_base_handler_does_nothing():
    writer = MockWriter()
    handler = TempoHandler()
    handler.handle(120.0, writer)
    assert writer.processed == []


# --- ValetonTempoHandler ---

def test_valeton_ignores_bpm_out_of_range():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(30.0, writer)   # below min
    handler.handle(300.0, writer)  # above max
    assert writer.processed == []


def test_valeton_calls_process_twice():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(120.0, writer)
    assert len(writer.processed) == 2

def test_valeton_cc_numbers():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(120.0, writer)
    assert writer.processed[0].data1 == 73
    assert writer.processed[1].data1 == 74

def test_valeton_message_type_is_cc():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(120.0, writer)
    assert writer.processed[0].type == CC
    assert writer.processed[1].type == CC

def test_valeton_120_bpm_values():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(120.0, writer)
    assert writer.processed[0].data2 == 0    # CC73 = 0 (range 0)
    assert writer.processed[1].data2 == 120  # CC74 = 120

def test_valeton_200_bpm_values():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(200.0, writer)
    assert writer.processed[0].data2 == 1   # CC73 = 1 (range 1)
    assert writer.processed[1].data2 == 72  # CC74 = 200 - 128

def test_valeton_260_bpm_values():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=0)
    handler.handle(260.0, writer)
    assert writer.processed[0].data2 == 2  # CC73 = 2 (range 2)
    assert writer.processed[1].data2 == 4  # CC74 = 260 - 256

def test_valeton_uses_configured_channel():
    writer = MockWriter()
    handler = ValetonTempoHandler(channel=3)
    handler.handle(100.0, writer)
    assert writer.processed[0].channel == 3
    assert writer.processed[1].channel == 3
