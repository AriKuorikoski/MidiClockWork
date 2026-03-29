class MessageFilter:
    def __init__(self, types=None, channels=None, cc_numbers=None):
        self.types = types          # set of msg types, or None for all
        self.channels = channels    # set of channels (0-15), or None for all
        self.cc_numbers = cc_numbers  # set of CC numbers, or None for all

    def matches(self, msg):
        if self.types is not None and msg.type not in self.types:
            return False
        if self.channels is not None:
            if msg.channel is None or msg.channel not in self.channels:
                return False
        if self.cc_numbers is not None:
            if msg.data1 is None or msg.data1 not in self.cc_numbers:
                return False
        return True


_TYPE_NAMES = {
    0x80: "NOTE_OFF", 0x90: "NOTE_ON",  0xA0: "AFTERTOUCH",
    0xB0: "CC",       0xC0: "PC",       0xD0: "CHAN_PRESSURE",
    0xE0: "PITCH_BEND",
    0xF8: "CLOCK",    0xFA: "START",    0xFB: "CONTINUE",   0xFC: "STOP",
}


class ConsoleWriter:
    """Drop-in replacement for UartWriter that prints MIDI messages to stdout.
    Useful for testing on hardware without the target device connected."""

    def __init__(self):
        self.filter = MessageFilter()

    def process(self, msg):
        if msg.type == 0xF8:  # skip CLOCK — too noisy for console
            return
        name = _TYPE_NAMES.get(msg.type, "0x{:02X}".format(msg.type))
        if msg.channel is not None:
            print("{:<14} ch={} data1={} data2={}".format(
                name, msg.channel, msg.data1, msg.data2))
        else:
            print(name)


class UartWriter:
    def __init__(self, uart, msg_filter, generate=None):
        self.uart = uart
        self.filter = msg_filter
        self.generate = generate

    def process(self, msg):
        if self.generate is not None:
            result = self.generate(msg)
            if result:
                for m in result:
                    self.uart.write(m.serialize())
        else:
            self.uart.write(msg.serialize())
