"""
USB MIDI transport.

Implements USB MIDI 1.0 class device using MicroPython's 'usb' module,
available on RP2040 from MicroPython v1.22+.

USB MIDI event packet format (4 bytes per message):
  [CIN | cable_number] [status] [data1] [data2]

  CIN (Code Index Number) is derived from the MIDI status byte:
    0x8 = Note Off
    0x9 = Note On
    0xA = Poly KeyPress
    0xB = Control Change
    0xC = Program Change  (3 bytes: CIN, status, prog, 0x00)
    0xD = Channel Pressure (3 bytes: CIN, status, pressure, 0x00)
    0xE = Pitch Bend
    0xF = System messages (0xF8 clock, 0xFA start, etc. → single-byte 0x0F)

Single-byte system real-time messages (CLOCK, START, STOP, CONTINUE)
use CIN=0x0F and pad with two zero bytes.

Cable number is always 0 (single virtual cable).
"""

try:
    import usb.device
    import usb.device.midi
    _USB_AVAILABLE = True
except ImportError:
    _USB_AVAILABLE = False

# CIN lookup for channel messages (upper nibble of status → CIN)
_STATUS_TO_CIN = {
    0x80: 0x08,  # Note Off
    0x90: 0x09,  # Note On
    0xA0: 0x0A,  # Poly KeyPress
    0xB0: 0x0B,  # Control Change
    0xC0: 0x0C,  # Program Change
    0xD0: 0x0D,  # Channel Pressure
    0xE0: 0x0E,  # Pitch Bend
}

# Single-byte system real-time messages → CIN 0x0F
_SINGLE_BYTE_SYSTEM = {0xF8, 0xFA, 0xFB, 0xFC, 0xFF}


class UsbMidiTransport:
    """
    USB MIDI 1.0 device transport. Presents the Pico as a USB MIDI
    interface to the connected host. Implements read() and write()
    so it can be used as a transport in MidiInput and UartWriter.

    Requires MicroPython v1.22+ with the 'usb' module for RP2040.
    Raises ImportError on older firmware.
    """

    def __init__(self):
        if not _USB_AVAILABLE:
            raise ImportError(
                "USB MIDI requires MicroPython v1.22+ with the 'usb' module. "
                "Download firmware from https://micropython.org/download/RPI_PICO_W/"
            )
        self._midi = usb.device.midi.MIDIInterface()
        usb.device.get().init(self._midi, builtin_driver=True)

    def read(self):
        """
        Poll for incoming USB MIDI event packets from the host.
        Returns raw MIDI bytes (status + data) or None.
        """
        buf = bytearray(4)
        result = bytearray()
        while self._midi.readinto(buf):
            midi = usb_unwrap(bytes(buf))
            if midi:
                result += midi
        return bytes(result) if result else None

    def write(self, data):
        """Send raw MIDI bytes to the host as USB MIDI event packets."""
        packet = usb_wrap(bytes(data))
        if packet:
            self._midi.write(packet)


# ---------------------------------------------------------------------------
# Packet framing — module-level for easy unit testing
# ---------------------------------------------------------------------------

def usb_wrap(midi_bytes):
    """
    Wrap a single raw MIDI message in a 4-byte USB MIDI event packet.
    Returns bytes or empty bytes if the message cannot be encoded.
    """
    if not midi_bytes:
        return b''

    status = midi_bytes[0]

    if status in _SINGLE_BYTE_SYSTEM:
        return bytes([0x0F, status, 0x00, 0x00])

    upper = status & 0xF0
    cin = _STATUS_TO_CIN.get(upper)
    if cin is None:
        return b''  # unsupported status byte

    # Pad to 3 data bytes (some messages are 2 bytes: status + 1 data)
    padded = list(midi_bytes)
    while len(padded) < 3:
        padded.append(0x00)

    return bytes([cin, padded[0], padded[1], padded[2]])


def usb_unwrap(packet):
    """
    Extract raw MIDI bytes from a 4-byte USB MIDI event packet.
    Returns bytes or empty bytes if the packet cannot be decoded.
    """
    if len(packet) < 4:
        return b''

    cin = packet[0] & 0x0F

    if cin == 0x0F:
        # Single-byte system real-time
        return bytes([packet[1]])

    if cin in (0x08, 0x09, 0x0A, 0x0B, 0x0E):
        # Three-byte messages
        return bytes(packet[1:4])

    if cin in (0x0C, 0x0D):
        # Two-byte messages (status + 1 data, last byte is padding)
        return bytes(packet[1:3])

    return b''
