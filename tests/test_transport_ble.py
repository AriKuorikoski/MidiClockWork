import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# ---------------------------------------------------------------------------
# Mock the 'bluetooth' module so tests run on desktop Python
# ---------------------------------------------------------------------------

import types

_bt = types.ModuleType("bluetooth")
_bt.FLAG_READ = 0x0002
_bt.FLAG_WRITE_NO_RESPONSE = 0x0004
_bt.FLAG_NOTIFY = 0x0010

class _UUID:
    def __init__(self, s): self._s = s
    def __repr__(self): return f"UUID({self._s!r})"

_bt.UUID = _UUID
sys.modules["bluetooth"] = _bt

from transport_ble import ble_wrap, ble_unwrap


# ---------------------------------------------------------------------------
# ble_wrap — raw MIDI → BLE MIDI packet
# ---------------------------------------------------------------------------

def test_wrap_adds_two_header_bytes():
    packet = ble_wrap(bytes([0xF8]))
    assert len(packet) == 3
    assert packet[0] == 0x80  # header
    assert packet[1] == 0x80  # timestamp LSB

def test_wrap_preserves_midi_bytes():
    midi = bytes([0x90, 60, 100])
    packet = ble_wrap(midi)
    assert packet[2:] == midi

def test_wrap_single_byte_message():
    packet = ble_wrap(bytes([0xF8]))  # CLOCK
    assert packet == bytes([0x80, 0x80, 0xF8])

def test_wrap_three_byte_message():
    packet = ble_wrap(bytes([0xB0, 73, 0]))  # CC ch0 CC73=0
    assert packet == bytes([0x80, 0x80, 0xB0, 73, 0])


# ---------------------------------------------------------------------------
# ble_unwrap — BLE MIDI packet → raw MIDI bytes
# ---------------------------------------------------------------------------

def test_unwrap_single_clock():
    packet = bytes([0x80, 0x80, 0xF8])
    assert ble_unwrap(packet) == bytes([0xF8])

def test_unwrap_three_byte_message():
    packet = bytes([0x80, 0x80, 0x90, 60, 100])
    assert ble_unwrap(packet) == bytes([0x90, 60, 100])

def test_unwrap_cc_message():
    packet = bytes([0x80, 0x80, 0xB0, 73, 0])
    assert ble_unwrap(packet) == bytes([0xB0, 73, 0])

def test_unwrap_two_messages_in_one_packet():
    # Two messages: NOTE_ON and NOTE_OFF, each with their own timestamp
    packet = bytes([
        0x80,              # packet header
        0x80, 0x90, 60, 100,  # ts + NOTE_ON
        0x81, 0x80, 60, 0,    # ts + NOTE_OFF (different timestamp)
    ])
    result = ble_unwrap(packet)
    assert result == bytes([0x90, 60, 100, 0x80, 60, 0])

def test_unwrap_too_short_returns_empty():
    assert ble_unwrap(bytes([0x80, 0x80])) == b''
    assert ble_unwrap(bytes([0x80])) == b''
    assert ble_unwrap(b'') == b''

def test_unwrap_malformed_missing_status_returns_empty():
    # Timestamp followed by a data byte (bit 7 = 0) — malformed
    packet = bytes([0x80, 0x80, 0x3C])  # header, ts, data-byte-only
    assert ble_unwrap(packet) == b''


# ---------------------------------------------------------------------------
# Round-trip: wrap then unwrap
# ---------------------------------------------------------------------------

def test_roundtrip_clock():
    midi = bytes([0xF8])
    assert ble_unwrap(ble_wrap(midi)) == midi

def test_roundtrip_note_on():
    midi = bytes([0x90, 60, 100])
    assert ble_unwrap(ble_wrap(midi)) == midi

def test_roundtrip_cc():
    midi = bytes([0xB0, 73, 0])
    assert ble_unwrap(ble_wrap(midi)) == midi

def test_roundtrip_start():
    midi = bytes([0xFA])
    assert ble_unwrap(ble_wrap(midi)) == midi
