import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import time

class MockTime:
    def __init__(self):
        self._us = 0
    def ticks_us(self):
        return self._us
    def ticks_diff(self, a, b):
        return a - b

mock_time = MockTime()
time.ticks_us = mock_time.ticks_us
time.ticks_diff = mock_time.ticks_diff

from config import Config
from system_builder import SystemBuilder, BuiltSystem
from midi_input import MidiInput
from midi_output import MidiOutput
from tempo_to_cc import ValetonTempoHandler
from midi_message import MidiMessage, NOTE_ON, CC, CLOCK


class MockUart:
    def __init__(self):
        self._in_buffer = b''
        self.written = []

    def send(self, data):
        self._in_buffer += bytes(data)

    def read(self):
        if self._in_buffer:
            result = self._in_buffer
            self._in_buffer = b''
            return result
        return None

    def write(self, data):
        self.written.append(bytes(data))


def make_uart_factory():
    uarts = {}
    def factory(uart_id, baudrate, tx_pin=None, rx_pin=None):
        uart = MockUart()
        uarts[uart_id] = uart
        return uart
    return factory, uarts


def build(config_dict):
    cfg = Config(config_dict)
    factory, uarts = make_uart_factory()
    system = SystemBuilder(uart_factory=factory).build(cfg)
    return system, uarts


def simple_config(filter_cfg=None, tempo_handler=None):
    return {
        "inputs": [{"name": "IN", "uart": 0, "rx_pin": 1}],
        "outputs": [{
            "name": "OUT1",
            "uart": 1,
            "tx_pin": 4,
            "filter": filter_cfg or {},
            "tempo_handler": tempo_handler,
        }]
    }


# --- BuiltSystem structure ---

def test_returns_built_system():
    system, _ = build(simple_config())
    assert isinstance(system, BuiltSystem)

def test_correct_number_of_inputs():
    system, _ = build(simple_config())
    assert len(system.inputs) == 1

def test_correct_number_of_outputs():
    system, _ = build(simple_config())
    assert len(system.outputs) == 1

def test_two_outputs():
    cfg = {
        "inputs": [{"name": "IN", "uart": 0, "rx_pin": 1}],
        "outputs": [
            {"name": "OUT1", "uart": 1, "tx_pin": 4, "filter": {}, "tempo_handler": None},
            {"name": "OUT2", "uart": 2, "tx_pin": 8, "filter": {}, "tempo_handler": None},
        ]
    }
    system, uarts = build(cfg)
    assert len(system.outputs) == 2
    assert 1 in uarts
    assert 2 in uarts

def test_bus_is_shared():
    system, _ = build(simple_config())
    assert system.bus is not None


# --- Output filter propagated ---

def test_output_pass_all_filter():
    system, uarts = build(simple_config(filter_cfg={}))
    system.bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    system.bus.emit("midi_out", MidiMessage(CLOCK))
    assert len(uarts[1].written) == 2

def test_output_type_filter():
    system, uarts = build(simple_config(filter_cfg={"types": ["clock"]}))
    system.bus.emit("midi_out", MidiMessage(CLOCK))
    system.bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    assert len(uarts[1].written) == 1
    assert uarts[1].written[0] == bytes([0xF8])

def test_output_channel_filter():
    system, uarts = build(simple_config(filter_cfg={"channels": [0]}))
    system.bus.emit("midi_out", MidiMessage(NOTE_ON, channel=0, data1=60, data2=100))
    system.bus.emit("midi_out", MidiMessage(NOTE_ON, channel=1, data1=60, data2=100))
    assert len(uarts[1].written) == 1


# --- Tempo handler ---

def test_no_tempo_handler():
    system, uarts = build(simple_config(tempo_handler=None))
    system.bus.emit("tempo_changed", 120.0)
    assert uarts[1].written == []

def test_valeton_tempo_handler_created():
    system, uarts = build(simple_config(
        tempo_handler={"type": "valeton", "channels": [0]}
    ))
    system.bus.emit("tempo_changed", 120.0)
    assert len(uarts[1].written) == 2
    assert uarts[1].written[0] == bytes([0xB0, 73, 0])
    assert uarts[1].written[1] == bytes([0xB0, 74, 120])

def test_valeton_multi_channel():
    system, uarts = build(simple_config(
        tempo_handler={"type": "valeton", "channels": [0, 1]}
    ))
    system.bus.emit("tempo_changed", 120.0)
    assert len(uarts[1].written) == 4


# --- Input filter propagated to router ---

def test_input_channel_filter_blocks_other_channels():
    cfg = {
        "inputs": [{"name": "IN", "uart": 0, "rx_pin": 1,
                    "filter": {"channels": [0], "include_global": True}}],
        "outputs": [{"name": "OUT1", "uart": 1, "tx_pin": 4,
                     "filter": {}, "tempo_handler": None}],
    }
    system, uarts = build(cfg)
    # Inject via the input UART to exercise the real filter path
    uarts[0].send([0x90, 60, 100])  # ch0 — passes
    system.inputs[0].poll()
    uarts[0].send([0x91, 60, 100])  # ch1 — blocked
    system.inputs[0].poll()
    assert len(uarts[1].written) == 1

def test_input_filter_passes_global_messages():
    cfg = {
        "inputs": [{"name": "IN", "uart": 0, "rx_pin": 1,
                    "filter": {"channels": [0], "include_global": True}}],
        "outputs": [{"name": "OUT1", "uart": 1, "tx_pin": 4,
                     "filter": {}, "tempo_handler": None}],
    }
    system, uarts = build(cfg)
    uarts[0].send([0xF8])  # CLOCK — no channel, should pass
    system.inputs[0].poll()
    assert len(uarts[1].written) == 1

def test_two_inputs_with_independent_filters():
    cfg = {
        "inputs": [
            {"name": "IN0", "uart": 0, "rx_pin": 1,
             "filter": {"channels": [0], "include_global": False}},
            {"name": "IN1", "uart": 2, "rx_pin": 3,
             "filter": {"channels": [1], "include_global": False}},
        ],
        "outputs": [{"name": "OUT1", "uart": 1, "tx_pin": 4,
                     "filter": {}, "tempo_handler": None}],
    }
    system, uarts = build(cfg)

    uarts[0].send([0x90, 60, 100])  # ch0 from IN0 — passes IN0 filter
    system.inputs[0].poll()
    uarts[2].send([0x91, 60, 100])  # ch1 from IN1 — passes IN1 filter
    system.inputs[1].poll()
    uarts[0].send([0x91, 60, 100])  # ch1 from IN0 — blocked by IN0 filter
    system.inputs[0].poll()

    assert len(uarts[1].written) == 2
