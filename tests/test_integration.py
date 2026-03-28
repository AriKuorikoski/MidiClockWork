"""
Integration tests — full pipeline: raw MIDI bytes in, bytes out.

Each test builds a complete MidiSystem from a config dict and exercises
the real component stack with mock UARTs.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from midi_system import MidiSystem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def simple_config(input_filter=None, output_filter=None, tempo_handler=None):
    return Config({
        "inputs": [{
            "name": "IN",
            "uart": 0,
            "rx_pin": 1,
            "filter": input_filter or {},
        }],
        "outputs": [{
            "name": "OUT1",
            "uart": 1,
            "tx_pin": 4,
            "filter": output_filter or {},
            "tempo_handler": tempo_handler,
        }]
    })


def two_output_config(out1_filter=None, out2_filter=None):
    return Config({
        "inputs": [{"name": "IN", "uart": 0, "rx_pin": 1}],
        "outputs": [
            {"name": "OUT1", "uart": 1, "tx_pin": 4,
             "filter": out1_filter or {}, "tempo_handler": None},
            {"name": "OUT2", "uart": 2, "tx_pin": 8,
             "filter": out2_filter or {}, "tempo_handler": None},
        ]
    })


# ---------------------------------------------------------------------------
# Scenario 1 — Full pipeline passthrough
# ---------------------------------------------------------------------------

def test_note_on_passes_through():
    sys = MidiSystem().build_from_config(simple_config())
    sys.send_bytes(0, [0x90, 60, 100])
    assert sys.output_uart(1).written == [bytes([0x90, 60, 100])]


def test_clock_passes_through():
    sys = MidiSystem().build_from_config(simple_config())
    sys.send_bytes(0, [0xF8])
    assert sys.output_uart(1).written == [bytes([0xF8])]


def test_multiple_messages_in_one_poll():
    sys = MidiSystem().build_from_config(simple_config())
    sys.send_bytes(0, [0x90, 60, 100, 0xF8])
    assert len(sys.output_uart(1).written) == 2


# ---------------------------------------------------------------------------
# Scenario 2 — Clock tracker: 24 clocks produce a beat
# ---------------------------------------------------------------------------

def test_24_clocks_emit_beat():
    sys = MidiSystem().build_from_config(simple_config())
    beats = []
    sys.bus.on("beat", lambda: beats.append(True))
    sys.send_clocks(0, 24, bpm=120)
    assert len(beats) == 1


def test_48_clocks_emit_two_beats():
    sys = MidiSystem().build_from_config(simple_config())
    beats = []
    sys.bus.on("beat", lambda: beats.append(True))
    sys.send_clocks(0, 48, bpm=120)
    assert len(beats) == 2


# ---------------------------------------------------------------------------
# Scenario 3 — Valeton handler: 48 clocks at 120 BPM → CC73 + CC74
# ---------------------------------------------------------------------------

def test_valeton_cc_emitted_after_clocks():
    sys = MidiSystem().build_from_config(simple_config(
        tempo_handler={"type": "valeton", "channels": [0]}
    ))
    sys.send_clocks(0, 48, bpm=120)
    flat = sys.output_uart(1).written_flat()
    assert bytes([0xB0, 73, 0]) in [bytes(sys.output_uart(1).written[i])
                                    for i in range(len(sys.output_uart(1).written))]
    assert bytes([0xB0, 74, 120]) in [bytes(sys.output_uart(1).written[i])
                                      for i in range(len(sys.output_uart(1).written))]


# ---------------------------------------------------------------------------
# Scenario 4 — Output filter blocks non-matching message types
# ---------------------------------------------------------------------------

def test_clock_only_filter_blocks_note_on():
    sys = MidiSystem().build_from_config(simple_config(
        output_filter={"types": ["clock"]}
    ))
    sys.send_bytes(0, [0x90, 60, 100])  # NOTE_ON
    sys.send_bytes(0, [0xF8])           # CLOCK
    assert len(sys.output_uart(1).written) == 1
    assert sys.output_uart(1).written[0] == bytes([0xF8])


# ---------------------------------------------------------------------------
# Scenario 5 — Two outputs filter independently
# ---------------------------------------------------------------------------

def test_two_outputs_independent_filtering():
    sys = MidiSystem().build_from_config(two_output_config(
        out1_filter={},
        out2_filter={"types": ["cc"]},
    ))
    sys.send_bytes(0, [0x90, 60, 100])       # NOTE_ON
    sys.send_bytes(0, [0xB0, 7, 100])        # CC

    assert len(sys.output_uart(1).written) == 2   # OUT1 pass-all: both
    assert len(sys.output_uart(2).written) == 1   # OUT2 CC-only: one
    assert sys.output_uart(2).written[0] == bytes([0xB0, 7, 100])


# ---------------------------------------------------------------------------
# Scenario 6 — START resets clock; beat count restarts
# ---------------------------------------------------------------------------

def test_start_resets_clock_beat_count():
    sys = MidiSystem().build_from_config(simple_config())
    beats = []
    sys.bus.on("beat", lambda: beats.append(True))

    # First sequence: 12 clocks (half a beat)
    sys.send_clocks(0, 12, bpm=120)
    # START resets tick count
    sys.send_bytes(0, [0xFA])
    # Second sequence: 24 clocks → exactly 1 beat
    sys.send_clocks(0, 24, bpm=120)

    assert len(beats) == 1


# ---------------------------------------------------------------------------
# Scenario 7 — No tempo handler: clocks produce no CC output
# ---------------------------------------------------------------------------

def test_no_tempo_handler_no_cc_output():
    sys = MidiSystem().build_from_config(simple_config(tempo_handler=None))
    sys.send_clocks(0, 48, bpm=120)
    # Only raw CLOCK bytes should be written, no CC73/74
    for chunk in sys.output_uart(1).written:
        assert chunk == bytes([0xF8]), "unexpected non-clock byte written"


# ---------------------------------------------------------------------------
# Scenario 8 — Valeton with channel=3: CCs have status 0xB3
# ---------------------------------------------------------------------------

def test_valeton_channel_3():
    sys = MidiSystem().build_from_config(simple_config(
        tempo_handler={"type": "valeton", "channels": [3]}
    ))
    sys.send_clocks(0, 48, bpm=120)
    cc_written = [c for c in sys.output_uart(1).written if c[0] in (0xB3,)]
    assert len(cc_written) >= 2
    assert bytes([0xB3, 73]) == cc_written[0][:2]
    assert bytes([0xB3, 74]) == cc_written[1][:2]


# ---------------------------------------------------------------------------
# Scenario 9 — Valeton channels=[0,1]: CCs emitted for both channels
# ---------------------------------------------------------------------------

def test_valeton_multi_channel_tempo():
    sys = MidiSystem().build_from_config(simple_config(
        tempo_handler={"type": "valeton", "channels": [0, 1]}
    ))
    sys.send_clocks(0, 48, bpm=120)
    written = sys.output_uart(1).written
    cc_chunks = [c for c in written if len(c) == 3 and c[0] in (0xB0, 0xB1)]
    # At least one pair per channel
    ch0 = [c for c in cc_chunks if c[0] == 0xB0]
    ch1 = [c for c in cc_chunks if c[0] == 0xB1]
    assert len(ch0) >= 2
    assert len(ch1) >= 2


# ---------------------------------------------------------------------------
# Scenario 10 — Input filter: channel 1 messages dropped, channel 0 pass
# ---------------------------------------------------------------------------

def test_input_filter_drops_wrong_channel():
    sys = MidiSystem().build_from_config(simple_config(
        input_filter={"channels": [0], "include_global": True}
    ))
    sys.send_bytes(0, [0x90, 60, 100])  # NOTE_ON ch0 — pass
    sys.send_bytes(0, [0x91, 60, 100])  # NOTE_ON ch1 — blocked
    assert len(sys.output_uart(1).written) == 1
    assert sys.output_uart(1).written[0] == bytes([0x90, 60, 100])


# ---------------------------------------------------------------------------
# Scenario 11 — Input filter include_global: CLOCK passes despite channel filter
# ---------------------------------------------------------------------------

def test_input_filter_global_messages_pass():
    sys = MidiSystem().build_from_config(simple_config(
        input_filter={"channels": [0], "include_global": True}
    ))
    sys.send_bytes(0, [0xF8])           # CLOCK — no channel, should pass
    sys.send_bytes(0, [0x91, 60, 100])  # NOTE_ON ch1 — blocked
    assert len(sys.output_uart(1).written) == 1
    assert sys.output_uart(1).written[0] == bytes([0xF8])
