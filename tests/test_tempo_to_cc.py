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

def test_base_handler_does_nothing():
    assert TempoHandler().handle(120.0) == []


# --- ValetonTempoHandler ---

def test_valeton_default_channel():
    handler = ValetonTempoHandler()
    assert handler.channels == [0]

def test_valeton_ignores_bpm_out_of_range():
    handler = ValetonTempoHandler()
    assert handler.handle(30.0) == []
    assert handler.handle(300.0) == []

def test_valeton_single_channel_two_messages():
    msgs = ValetonTempoHandler(channels=[0]).handle(120.0)
    assert len(msgs) == 2

def test_valeton_cc_numbers():
    msgs = ValetonTempoHandler(channels=[0]).handle(120.0)
    assert msgs[0].data1 == 73
    assert msgs[1].data1 == 74

def test_valeton_message_type_is_cc():
    msgs = ValetonTempoHandler(channels=[0]).handle(120.0)
    assert msgs[0].type == CC
    assert msgs[1].type == CC

def test_valeton_120_bpm_values():
    msgs = ValetonTempoHandler(channels=[0]).handle(120.0)
    assert msgs[0].data2 == 0
    assert msgs[1].data2 == 120

def test_valeton_200_bpm_values():
    msgs = ValetonTempoHandler(channels=[0]).handle(200.0)
    assert msgs[0].data2 == 1
    assert msgs[1].data2 == 72

def test_valeton_260_bpm_values():
    msgs = ValetonTempoHandler(channels=[0]).handle(260.0)
    assert msgs[0].data2 == 2
    assert msgs[1].data2 == 4

def test_valeton_uses_configured_channel():
    msgs = ValetonTempoHandler(channels=[3]).handle(100.0)
    assert msgs[0].channel == 3
    assert msgs[1].channel == 3

def test_valeton_multi_channel_emits_pair_per_channel():
    msgs = ValetonTempoHandler(channels=[0, 1, 2]).handle(120.0)
    assert len(msgs) == 6  # 2 CC messages × 3 channels

def test_valeton_multi_channel_correct_channels():
    msgs = ValetonTempoHandler(channels=[0, 1]).handle(120.0)
    assert msgs[0].channel == 0
    assert msgs[1].channel == 0
    assert msgs[2].channel == 1
    assert msgs[3].channel == 1
