"""
BLE MIDI transport.

Implements the BLE MIDI 1.0 service spec (Bluetooth SIG):
  Service UUID:        03B80E5A-EDE8-4B33-A751-6CE34EC4C700
  Characteristic UUID: 7772E5DB-3868-4112-A1A9-F2669D106D3D
  Properties:          READ | WRITE_NO_RESPONSE | NOTIFY

BLE MIDI packet format:
  [packet_header] ([timestamp_lsb] [status] [data...])+

  packet_header = 0x80 | (ms_timestamp >> 7 & 0x3F)   -- always has bit 7 set
  timestamp_lsb = 0x80 | (ms_timestamp & 0x7F)         -- always has bit 7 set
  status/data   = standard MIDI bytes

This implementation uses a fixed timestamp of 0 (header=0x80, ts_lsb=0x80),
which is valid per spec and sufficient for routing purposes.

Running status and SysEx are not handled (see KNOWN_ISSUES.md).
"""

import bluetooth

_SERVICE_UUID = bluetooth.UUID("03B80E5A-EDE8-4B33-A751-6CE34EC4C700")
_CHAR_UUID    = bluetooth.UUID("7772E5DB-3868-4112-A1A9-F2669D106D3D")

_FLAGS = bluetooth.FLAG_READ | bluetooth.FLAG_WRITE_NO_RESPONSE | bluetooth.FLAG_NOTIFY

_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE        = 3

_DEVICE_NAME = b"MidiClockWork"

# Fixed timestamp=0: header byte, timestamp LSB byte
_HEADER = 0x80
_TS_LSB = 0x80


class BleMidiTransport:
    """
    BLE MIDI peripheral. Advertises as a BLE MIDI device and accepts
    one central connection. Implements read() and write() so it can be
    used directly as a transport in MidiInput and UartWriter.
    """

    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)

        ((self._char_handle,),) = self._ble.gatts_register_services((
            (_SERVICE_UUID, (
                (_CHAR_UUID, _FLAGS),
            )),
        ))

        self._conn_handle = None
        self._rx_buf = bytearray()
        self._advertise()

    def _advertise(self):
        adv_data = (
            b'\x02\x01\x06'
            + bytes([len(_DEVICE_NAME) + 1, 0x09])
            + _DEVICE_NAME
        )
        self._ble.gap_advertise(100_000, adv_data=adv_data)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._conn_handle = conn_handle
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self._conn_handle = None
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            _, value_handle = data
            if value_handle == self._char_handle:
                raw = bytes(self._ble.gatts_read(self._char_handle))
                midi = ble_unwrap(raw)
                if midi:
                    self._rx_buf += midi

    def read(self):
        """Return buffered raw MIDI bytes received from BLE peer, or None."""
        if not self._rx_buf:
            return None
        data = bytes(self._rx_buf)
        self._rx_buf = bytearray()
        return data

    def write(self, data):
        """Send raw MIDI bytes to the connected BLE peer."""
        if self._conn_handle is None:
            return
        self._ble.gatts_notify(
            self._conn_handle,
            self._char_handle,
            ble_wrap(bytes(data)),
        )


# ---------------------------------------------------------------------------
# Packet framing — module-level for easy unit testing
# ---------------------------------------------------------------------------

def ble_wrap(midi_bytes):
    """
    Wrap raw MIDI bytes in a BLE MIDI packet.
    Produces: [header, timestamp_lsb, <midi_bytes>]
    Fixed timestamp = 0.
    """
    return bytes([_HEADER, _TS_LSB]) + midi_bytes


def ble_unwrap(packet):
    """
    Strip BLE MIDI framing, returning raw MIDI bytes.

    Packet body (after the header byte) is a sequence of:
      [timestamp_lsb] [status] [data...]
    Both header and timestamp bytes have bit 7 set.
    Status bytes also have bit 7 set; data bytes do not.

    Running status and SysEx are not handled.
    """
    if len(packet) < 3:
        return b''

    result = bytearray()
    i = 1  # skip packet header byte

    while i < len(packet):
        # Timestamp LSB — must have bit 7 set
        if not (packet[i] & 0x80):
            break  # malformed packet
        i += 1  # skip timestamp

        # MIDI status byte — must have bit 7 set
        if i >= len(packet) or not (packet[i] & 0x80):
            break  # malformed or unsupported running status
        result.append(packet[i])
        i += 1

        # MIDI data bytes — bit 7 clear
        while i < len(packet) and not (packet[i] & 0x80):
            result.append(packet[i])
            i += 1

    return bytes(result)
