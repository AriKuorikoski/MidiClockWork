"""
Serial transport — reads raw MIDI bytes from the USB CDC data port.

Used for testing: a PC script sends MIDI bytes over the secondary COM port,
and this transport feeds them into the normal MidiInput pipeline.
The REPL console stays on the primary COM port.

Requires boot.py to enable the data port:
    import usb_cdc
    usb_cdc.enable(console=True, data=True)
"""
try:
    import usb_cdc
    _serial = usb_cdc.data
except (ImportError, AttributeError):
    _serial = None


class SerialTransport:
    def read(self):
        """Non-blocking read of available bytes from USB CDC data port."""
        if _serial is None:
            return None
        n = _serial.in_waiting
        if n > 0:
            return _serial.read(n)
        return None

    def write(self, data):
        """Write raw bytes to USB CDC data port."""
        if _serial is not None:
            _serial.write(data)
