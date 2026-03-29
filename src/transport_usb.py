"""
USB MIDI transport for CircuitPython.

Uses the built-in usb_midi module which handles all USB MIDI 1.0
protocol framing (CIN bytes, 4-byte packets) internally.

Requires boot.py to enable USB MIDI:
    import usb_midi
    usb_midi.enable()
"""
try:
    import usb_midi
    _USB_AVAILABLE = True
except ImportError:
    _USB_AVAILABLE = False


class UsbMidiTransport:
    def __init__(self):
        if not _USB_AVAILABLE:
            raise ImportError(
                "usb_midi module not available. "
                "Ensure CircuitPython firmware is installed."
            )
        # usb_midi.ports[0] = input (host -> device)
        # usb_midi.ports[1] = output (device -> host)
        self._in = usb_midi.ports[0]
        self._out = usb_midi.ports[1]

    def read(self):
        """Non-blocking read of available MIDI bytes from USB host."""
        data = self._in.read(64)
        if data:
            return data
        return None

    def write(self, data):
        """Send raw MIDI bytes to the USB host."""
        self._out.write(data)
