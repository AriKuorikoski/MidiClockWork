# MIDI status types (upper nibble)
NOTE_OFF = 0x80
NOTE_ON = 0x90
AFTERTOUCH = 0xA0
CC = 0xB0
PC = 0xC0
CHANNEL_PRESSURE = 0xD0
PITCH_BEND = 0xE0

# System messages
SYSEX_START = 0xF0
SYSEX_END = 0xF7
CLOCK = 0xF8
START = 0xFA
CONTINUE = 0xFB
STOP = 0xFC

# Message sizes by type (upper nibble) — data bytes only, not counting status
_CHANNEL_MSG_SIZES = {
    NOTE_OFF: 2,
    NOTE_ON: 2,
    AFTERTOUCH: 2,
    CC: 2,
    PC: 1,
    CHANNEL_PRESSURE: 1,
    PITCH_BEND: 2,
}

# System real-time messages (single byte, no data)
_SYSTEM_RT = {CLOCK, START, CONTINUE, STOP}


class MidiMessage:
    def __init__(self, msg_type, channel=None, data1=None, data2=None):
        self.type = msg_type
        self.channel = channel
        self.data1 = data1
        self.data2 = data2

    def serialize(self):
        if self.type in _SYSTEM_RT:
            return bytes([self.type])

        if self.channel is not None:
            status = self.type | self.channel
        else:
            return bytes([self.type])

        size = _CHANNEL_MSG_SIZES.get(self.type, 0)
        if size == 2:
            return bytes([status, self.data1, self.data2])
        elif size == 1:
            return bytes([status, self.data1])
        return bytes([status])


def parse(data):
    """Parse raw bytes into a MidiMessage. Returns None if invalid."""
    if not data:
        return None

    status = data[0]

    # System real-time (single byte)
    if status in _SYSTEM_RT:
        return MidiMessage(status)

    # Channel messages
    msg_type = status & 0xF0
    channel = status & 0x0F
    size = _CHANNEL_MSG_SIZES.get(msg_type)

    if size is None:
        return None
    if len(data) < size + 1:
        return None

    data1 = data[1] if size >= 1 else None
    data2 = data[2] if size >= 2 else None

    return MidiMessage(msg_type, channel, data1, data2)
