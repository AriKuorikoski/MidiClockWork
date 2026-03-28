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
    def __init__(self, uart_factory=None):
        self._uart_factory = uart_factory or _default_uart_factory

    def build(self, config):
        bus = EventBus()
        clock = MidiClockTracker(bus)

        MidiRouter(bus, clock)

        inputs = []
        for inp in config.inputs:
            uart = self._uart_factory(inp["uart"], 31250, rx_pin=inp["rx_pin"])
            inputs.append(MidiInput(inp["name"], uart, bus, inp["filter"]))

        outputs = []
        for out in config.outputs:
            uart = self._uart_factory(out["uart"], 31250, tx_pin=out["tx_pin"])
            f = out["filter"]
            msg_filter = MessageFilter(
                types=f["types"],
                channels=f["channels"],
                cc_numbers=f["cc_numbers"],
            )
            tempo_handler = _make_tempo_handler(out["tempo_handler"])
            writer = UartWriter(uart, msg_filter)
            outputs.append(MidiOutput(out["name"], bus, writer, tempo_handler))

        return BuiltSystem(bus, inputs, outputs)


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
