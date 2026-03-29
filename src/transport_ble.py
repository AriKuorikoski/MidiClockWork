"""
BLE MIDI transport for CircuitPython.

Uses adafruit_ble and adafruit_ble_midi which handle GATT service
registration, BLE MIDI packet framing, advertising, and iOS pairing
automatically.

Requires these libraries in CIRCUITPY/lib/:
    adafruit_ble, adafruit_ble_midi

Install via: circup install adafruit_ble adafruit_ble_midi
"""
import wifi  # activates the CYW43 chip (required before BLE on Pico W)
wifi.radio.enabled = False  # we only need BLE, not Wi-Fi

import adafruit_ble
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble_midi import MIDIService

_DEVICE_NAME = "MidiClockWork"


class BleMidiTransport:
    """
    BLE MIDI peripheral. Advertises as a BLE MIDI device and accepts
    one central connection. Implements read() and write() so it can be
    used directly as a transport in MidiInput and UartWriter.
    """

    def __init__(self):
        self._ble = adafruit_ble.BLERadio()
        self._ble.name = _DEVICE_NAME
        self._midi_service = MIDIService()
        self._advertisement = ProvideServicesAdvertisement(self._midi_service)
        self._advertisement.complete_name = _DEVICE_NAME
        self._ble.start_advertising(self._advertisement)
        print("BLE: advertising as", _DEVICE_NAME)

    def read(self):
        """Return buffered raw MIDI bytes received from BLE peer, or None."""
        if not self._ble.connected:
            if not self._ble.advertising:
                self._ble.start_advertising(self._advertisement)
            return None
        n = self._midi_service.in_waiting
        if n > 0:
            return self._midi_service.read(n)
        return None

    def write(self, data):
        """Send raw MIDI bytes to the connected BLE peer."""
        if self._ble.connected:
            self._midi_service.write(data)
