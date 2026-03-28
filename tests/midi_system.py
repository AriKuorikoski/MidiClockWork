"""
Integration test helpers for MidiClockWork.

Provides MockUart, MockTime and MidiSystem — a full pipeline harness
that wires up all components with mock hardware.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import time as _time_module


class MockUart:
    """Serves as both an input UART (send/read) and output UART (write)."""

    def __init__(self):
        self._in_buffer = b''
        self.written = []

    def send(self, data):
        """Feed raw bytes as if arriving from external hardware."""
        self._in_buffer += bytes(data)

    def read(self):
        """Called by MidiInput.poll(). Returns and clears the buffer."""
        if self._in_buffer:
            result = self._in_buffer
            self._in_buffer = b''
            return result
        return None

    def write(self, data):
        """Called by UartWriter. Captures bytes written to this output."""
        self.written.append(bytes(data))

    def written_flat(self):
        """All written bytes as one flat bytes object."""
        result = b''
        for chunk in self.written:
            result += chunk
        return result


class MockTime:
    """Controls time for MidiClockTracker's BPM calculations."""

    def __init__(self):
        self._us = 0

    def ticks_us(self):
        return self._us

    def ticks_diff(self, a, b):
        return a - b

    def advance_us(self, us):
        self._us += us

    def advance_for_bpm(self, bpm, ticks=1):
        """Advance time by the interval for <ticks> MIDI clock ticks at <bpm>."""
        tick_us = int(60_000_000 // (bpm * 24))
        self._us += tick_us * ticks

    def install(self):
        """Patch the time module used by MidiClockTracker."""
        _time_module.ticks_us = self.ticks_us
        _time_module.ticks_diff = self.ticks_diff


class MidiSystem:
    """Full pipeline harness. Wires all components with MockUart instances."""

    def __init__(self):
        self.mock_time = MockTime()
        self.mock_time.install()
        self._uarts = {}
        self._system = None

    def build_from_config(self, config, transport_overrides=None):
        from system_builder import SystemBuilder

        def uart_factory(uart_id, baudrate, tx_pin=None, rx_pin=None):
            uart = MockUart()
            self._uarts[uart_id] = uart
            return uart

        # Wrap transport overrides so their mock instances are also registered
        # in self._uarts under a string key (e.g. "ble_midi", "usb_midi")
        wrapped_overrides = {}
        if transport_overrides:
            for key, factory in transport_overrides.items():
                def _wrap(k=key, f=factory):
                    mock = f()
                    self._uarts[k] = mock
                    return mock
                wrapped_overrides[key] = _wrap

        self._system = SystemBuilder(
            uart_factory=uart_factory,
            transport_overrides=wrapped_overrides,
        ).build(config)
        return self

    def send_bytes(self, uart_id, data):
        """Inject raw bytes into an input UART and poll all inputs."""
        self._uarts[uart_id].send(data)
        self._poll()

    def send_clocks(self, uart_id, count, bpm=120):
        """Send <count> CLOCK bytes, advancing mock time between each."""
        for _ in range(count):
            self.mock_time.advance_for_bpm(bpm, ticks=1)
            self._uarts[uart_id].send([0xF8])
            self._poll()

    def input_uart(self, uart_id):
        return self._uarts[uart_id]

    def output_uart(self, uart_id):
        return self._uarts[uart_id]

    @property
    def bus(self):
        return self._system.bus

    def _poll(self):
        for midi_in in self._system.inputs:
            midi_in.poll()
