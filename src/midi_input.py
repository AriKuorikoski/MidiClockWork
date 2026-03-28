from midi_message import parse, _CHANNEL_MSG_SIZES, _SYSTEM_RT


class MidiInput:
    def __init__(self, name, uart, bus):
        self.name = name
        self.uart = uart
        self.bus = bus
        self._buffer = []

    def poll(self):
        """Read available bytes from UART and emit parsed messages."""
        available = self.uart.read()
        if available:
            for byte in available:
                self._process_byte(byte)

    def _process_byte(self, byte):
        # Status byte (bit 7 set)
        if byte & 0x80:
            # System real-time messages — single byte, don't interrupt buffer
            if byte in _SYSTEM_RT:
                msg = parse(bytes([byte]))
                if msg:
                    self.bus.emit("midi_in", msg)
                return

            # New status byte — start fresh buffer
            self._buffer = [byte]
        elif self._buffer:
            # Data byte — append to current message
            self._buffer.append(byte)
        else:
            # Data byte with no status — ignore
            return

        # Check if message is complete
        if len(self._buffer) > 0:
            status = self._buffer[0]
            msg_type = status & 0xF0
            expected = _CHANNEL_MSG_SIZES.get(msg_type)
            if expected is not None and len(self._buffer) >= expected + 1:
                msg = parse(bytes(self._buffer))
                if msg:
                    self.bus.emit("midi_in", msg)
                self._buffer = []
