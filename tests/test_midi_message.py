import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from midi_message import (
    MidiMessage, parse,
    NOTE_ON, NOTE_OFF, CC, PC, PITCH_BEND,
    CHANNEL_PRESSURE, AFTERTOUCH,
    CLOCK, START, STOP, CONTINUE,
)


# --- Parsing ---

def test_parse_note_on():
    msg = parse(bytes([0x90, 60, 100]))
    assert msg.type == NOTE_ON
    assert msg.channel == 0
    assert msg.data1 == 60
    assert msg.data2 == 100


def test_parse_note_on_channel_10():
    msg = parse(bytes([0x99, 36, 127]))
    assert msg.type == NOTE_ON
    assert msg.channel == 9
    assert msg.data1 == 36
    assert msg.data2 == 127


def test_parse_note_off():
    msg = parse(bytes([0x85, 60, 0]))
    assert msg.type == NOTE_OFF
    assert msg.channel == 5
    assert msg.data1 == 60
    assert msg.data2 == 0


def test_parse_cc():
    msg = parse(bytes([0xB0, 7, 100]))
    assert msg.type == CC
    assert msg.channel == 0
    assert msg.data1 == 7
    assert msg.data2 == 100


def test_parse_pc():
    msg = parse(bytes([0xC3, 42]))
    assert msg.type == PC
    assert msg.channel == 3
    assert msg.data1 == 42
    assert msg.data2 is None


def test_parse_pitch_bend():
    msg = parse(bytes([0xE0, 0, 64]))
    assert msg.type == PITCH_BEND
    assert msg.channel == 0
    assert msg.data1 == 0
    assert msg.data2 == 64


def test_parse_aftertouch():
    msg = parse(bytes([0xA0, 60, 80]))
    assert msg.type == AFTERTOUCH
    assert msg.channel == 0
    assert msg.data1 == 60
    assert msg.data2 == 80


def test_parse_channel_pressure():
    msg = parse(bytes([0xD2, 100]))
    assert msg.type == CHANNEL_PRESSURE
    assert msg.channel == 2
    assert msg.data1 == 100
    assert msg.data2 is None


def test_parse_clock():
    msg = parse(bytes([0xF8]))
    assert msg.type == CLOCK
    assert msg.channel is None


def test_parse_start():
    msg = parse(bytes([0xFA]))
    assert msg.type == START


def test_parse_stop():
    msg = parse(bytes([0xFC]))
    assert msg.type == STOP


def test_parse_continue():
    msg = parse(bytes([0xFB]))
    assert msg.type == CONTINUE


def test_parse_empty():
    assert parse(bytes([])) is None


def test_parse_invalid_status():
    assert parse(bytes([0xF1])) is None


def test_parse_truncated_message():
    assert parse(bytes([0x90, 60])) is None  # Note On needs 3 bytes


# --- Serialization ---

def test_serialize_note_on():
    msg = MidiMessage(NOTE_ON, channel=0, data1=60, data2=100)
    assert msg.serialize() == bytes([0x90, 60, 100])


def test_serialize_note_on_channel_5():
    msg = MidiMessage(NOTE_ON, channel=5, data1=72, data2=80)
    assert msg.serialize() == bytes([0x95, 72, 80])


def test_serialize_cc():
    msg = MidiMessage(CC, channel=0, data1=7, data2=100)
    assert msg.serialize() == bytes([0xB0, 7, 100])


def test_serialize_pc():
    msg = MidiMessage(PC, channel=3, data1=42)
    assert msg.serialize() == bytes([0xC3, 42])


def test_serialize_clock():
    msg = MidiMessage(CLOCK)
    assert msg.serialize() == bytes([0xF8])


def test_serialize_start():
    msg = MidiMessage(START)
    assert msg.serialize() == bytes([0xFA])


# --- Round-trip ---

def test_roundtrip_note_on():
    raw = bytes([0x92, 48, 110])
    msg = parse(raw)
    assert msg.serialize() == raw


def test_roundtrip_cc():
    raw = bytes([0xBF, 64, 127])
    msg = parse(raw)
    assert msg.serialize() == raw


def test_roundtrip_pc():
    raw = bytes([0xC0, 0])
    msg = parse(raw)
    assert msg.serialize() == raw


def test_roundtrip_clock():
    raw = bytes([0xF8])
    msg = parse(raw)
    assert msg.serialize() == raw
