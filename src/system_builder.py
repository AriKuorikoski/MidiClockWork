from event_bus import EventBus
from midi_clock_tracker import MidiClockTracker
from midi_input import MidiInput
from midi_output import MidiOutput
from midi_router import MidiRouter
from uart_writer import MessageFilter, UartWriter
from tempo_to_cc import ValetonTempoHandler


class BuiltSystem:
    def __init__(self, bus, inputs, outputs):
        self.bus = bus
        self.inputs = inputs
        self.outputs = outputs


class SystemBuilder:
    def __init__(self, uart_factory=None, transport_overrides=None):
        # uart_factory(uart_id, baudrate, tx_pin=None, rx_pin=None) -> transport
        # None = use machine.UART (hardware path)
        # transport_overrides: {"ble_midi": callable, "usb_midi": callable}
        #   Each callable takes no arguments and returns a transport object.
        #   Used in tests to inject mock transports for non-UART types.
        self._uart_factory = uart_factory or _default_uart_factory
        self._transport_overrides = transport_overrides or {}

    def build(self, config):
        bus = EventBus()
        clock = MidiClockTracker(bus)
        MidiRouter(bus, clock)

        # BLE transport is shared: one connection used for both input and output
        _ble_transport = None

        inputs = []
        for inp in config.inputs:
            transport = self._make_transport(inp, role="input", ble=_ble_transport)
            if inp["type"] == "ble_midi" and _ble_transport is None:
                _ble_transport = transport
            inputs.append(MidiInput(inp["name"], transport, bus, inp["filter"]))

        outputs = []
        for out in config.outputs:
            transport = self._make_transport(out, role="output", ble=_ble_transport)
            if out["type"] == "ble_midi" and _ble_transport is None:
                _ble_transport = transport
            f = out["filter"]
            msg_filter = MessageFilter(
                types=f["types"],
                channels=f["channels"],
                cc_numbers=f["cc_numbers"],
            )
            tempo_handler = _make_tempo_handler(out["tempo_handler"])
            writer = UartWriter(transport, msg_filter)
            outputs.append(MidiOutput(out["name"], bus, writer, tempo_handler))

        return BuiltSystem(bus, inputs, outputs)

    def _make_transport(self, cfg, role, ble=None):
        t = cfg["type"]

        if t == "uart":
            if role == "input":
                return self._uart_factory(cfg["uart"], 31250, rx_pin=cfg["rx_pin"])
            else:
                return self._uart_factory(cfg["uart"], 31250, tx_pin=cfg["tx_pin"])

        if t == "ble_midi":
            if ble is not None:
                return ble  # reuse existing BLE connection (singleton)
            if t in self._transport_overrides:
                return self._transport_overrides[t]()
            from transport_ble import BleMidiTransport
            return BleMidiTransport()

        if t == "usb_midi":
            if t in self._transport_overrides:
                return self._transport_overrides[t]()
            from transport_usb import UsbMidiTransport
            return UsbMidiTransport()

        raise ValueError("unknown transport type: " + t)


def _make_tempo_handler(handler_cfg):
    if handler_cfg is None:
        return None
    if handler_cfg["type"] == "valeton":
        return ValetonTempoHandler(channels=handler_cfg["channels"])
    return None


def _default_uart_factory(uart_id, baudrate, tx_pin=None, rx_pin=None):
    from machine import UART, Pin
    kwargs = {"baudrate": baudrate}
    if tx_pin is not None:
        kwargs["tx"] = Pin(tx_pin)
    if rx_pin is not None:
        kwargs["rx"] = Pin(rx_pin)
    return UART(uart_id, **kwargs)
