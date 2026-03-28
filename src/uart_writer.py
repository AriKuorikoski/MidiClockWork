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
