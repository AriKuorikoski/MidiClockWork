import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transport_usb import usb_wrap, usb_unwrap


# ---------------------------------------------------------------------------
# usb_wrap — raw MIDI → 4-byte USB MIDI event packet
# ---------------------------------------------------------------------------

def test_wrap_note_on():
    packet = usb_wrap(bytes([0x90, 60, 100]))
    assert packet == bytes([0x09, 0x90, 60, 100])

def test_wrap_note_off():
    packet = usb_wrap(bytes([0x80, 60, 0]))
    assert packet == bytes([0x08, 0x80, 60, 0])

def test_wrap_cc():
    packet = usb_wrap(bytes([0xB0, 73, 0]))
    assert packet == bytes([0x0B, 0xB0, 73, 0])

def test_wrap_program_change():
    # PC is 2-byte message — padded to 4
    packet = usb_wrap(bytes([0xC0, 5]))
    assert packet == bytes([0x0C, 0xC0, 5, 0x00])

def test_wrap_channel_pressure():
    packet = usb_wrap(bytes([0xD0, 64]))
    assert packet == bytes([0x0D, 0xD0, 64, 0x00])

def test_wrap_pitch_bend():
    packet = usb_wrap(bytes([0xE0, 0, 64]))
    assert packet == bytes([0x0E, 0xE0, 0, 64])

def test_wrap_clock():
    packet = usb_wrap(bytes([0xF8]))
    assert packet == bytes([0x0F, 0xF8, 0x00, 0x00])

def test_wrap_start():
    packet = usb_wrap(bytes([0xFA]))
    assert packet == bytes([0x0F, 0xFA, 0x00, 0x00])

def test_wrap_stop():
    packet = usb_wrap(bytes([0xFC]))
    assert packet == bytes([0x0F, 0xFC, 0x00, 0x00])

def test_wrap_continue():
    packet = usb_wrap(bytes([0xFB]))
    assert packet == bytes([0x0F, 0xFB, 0x00, 0x00])

def test_wrap_channel_1_note_on():
    packet = usb_wrap(bytes([0x91, 60, 100]))
    assert packet == bytes([0x09, 0x91, 60, 100])

def test_wrap_empty_returns_empty():
    assert usb_wrap(b'') == b''

def test_wrap_unknown_status_returns_empty():
    assert usb_wrap(bytes([0xF0, 0x41])) == b''  # SysEx not supported


# ---------------------------------------------------------------------------
# usb_unwrap — 4-byte USB MIDI event packet → raw MIDI bytes
# ---------------------------------------------------------------------------

def test_unwrap_note_on():
    assert usb_unwrap(bytes([0x09, 0x90, 60, 100])) == bytes([0x90, 60, 100])

def test_unwrap_note_off():
    assert usb_unwrap(bytes([0x08, 0x80, 60, 0])) == bytes([0x80, 60, 0])

def test_unwrap_cc():
    assert usb_unwrap(bytes([0x0B, 0xB0, 73, 0])) == bytes([0xB0, 73, 0])

def test_unwrap_program_change():
    assert usb_unwrap(bytes([0x0C, 0xC0, 5, 0x00])) == bytes([0xC0, 5])

def test_unwrap_channel_pressure():
    assert usb_unwrap(bytes([0x0D, 0xD0, 64, 0x00])) == bytes([0xD0, 64])

def test_unwrap_pitch_bend():
    assert usb_unwrap(bytes([0x0E, 0xE0, 0, 64])) == bytes([0xE0, 0, 64])

def test_unwrap_clock():
    assert usb_unwrap(bytes([0x0F, 0xF8, 0x00, 0x00])) == bytes([0xF8])

def test_unwrap_start():
    assert usb_unwrap(bytes([0x0F, 0xFA, 0x00, 0x00])) == bytes([0xFA])

def test_unwrap_stop():
    assert usb_unwrap(bytes([0x0F, 0xFC, 0x00, 0x00])) == bytes([0xFC])

def test_unwrap_too_short_returns_empty():
    assert usb_unwrap(bytes([0x09, 0x90, 60])) == b''

def test_unwrap_unknown_cin_returns_empty():
    assert usb_unwrap(bytes([0x00, 0x00, 0x00, 0x00])) == b''


# ---------------------------------------------------------------------------
# Round-trip: wrap then unwrap
# ---------------------------------------------------------------------------

def test_roundtrip_note_on():
    midi = bytes([0x90, 60, 100])
    assert usb_unwrap(usb_wrap(midi)) == midi

def test_roundtrip_cc():
    midi = bytes([0xB0, 73, 0])
    assert usb_unwrap(usb_wrap(midi)) == midi

def test_roundtrip_clock():
    midi = bytes([0xF8])
    assert usb_unwrap(usb_wrap(midi)) == midi

def test_roundtrip_program_change():
    midi = bytes([0xC0, 5])
    assert usb_unwrap(usb_wrap(midi)) == midi

def test_roundtrip_start():
    midi = bytes([0xFA])
    assert usb_unwrap(usb_wrap(midi)) == midi
