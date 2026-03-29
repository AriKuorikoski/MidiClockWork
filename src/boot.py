"""CircuitPython boot configuration — runs once before code.py on every boot."""
import usb_cdc
import usb_midi
import usb_hid

# Disable HID to free USB endpoints for MIDI + dual CDC
usb_hid.disable()

# Enable USB MIDI device
usb_midi.enable()

# Enable a second USB CDC serial port for data (used by SerialTransport).
# Port 0 = REPL console (always enabled)
# Port 1 = raw data port (for tools/send_midi_clock.py)
usb_cdc.enable(console=True, data=True)
