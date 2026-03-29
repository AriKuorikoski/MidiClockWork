# Known Issues

These are confirmed bugs considered show-stoppers for production use.

---

## 1. SYSEX messages corrupt the parser

**Status:** Not implemented
**Impact:** High — corrupts parse state

System Exclusive messages (`0xF0 ... 0xF7`) are variable-length with no fixed size. The MIDI parser does not handle them. When a SYSEX blob arrives, its data bytes are misread as status bytes, corrupting parse state until the parser re-syncs on a real status byte.

**Fix:** On `0xF0`, read and discard bytes until `0xF7`, then resume normal parsing.

---

## 2. Running Status not handled

**Status:** Not implemented
**Impact:** High — silently drops messages

The MIDI spec allows omitting the status byte when it is the same as the previous message (commonly used for NOTE_ON streams from hardware controllers). The parser requires a status byte on every message, so running-status data bytes are silently misinterpreted or dropped.

**Fix:** Track the last seen status byte. If the first byte of a new message is a data byte (< `0x80`), reuse the previous status.

---

## 3. Active Sensing (0xFE) floods the bus

**Status:** Not filtered
**Impact:** Medium — unnecessary bus traffic

Active Sensing (`0xFE`) is a system real-time byte sent every ~300ms by some devices as a keep-alive heartbeat. Like CLOCK, it does not disrupt parsing, but it passes through to all outputs. At 300ms intervals this adds significant noise to the event bus.

**Fix:** Filter `0xFE` in `MidiInput` by default, or add `active_sensing` to the message type filter vocabulary in `config.json`.

---

## 4. BPM jitter over USB MIDI at high tempos

**Status:** Present
**Impact:** Low — ±1 BPM oscillation in some cases

USB MIDI batches clock bytes into USB bulk transfers. At high BPM (>180), the batching can cause small timing variations that show up as ±1 BPM oscillation in the smoothed reading. A 10-reading moving average reduces this but doesn't eliminate it entirely.

This does not affect UART input (hardware-accurate timing) and is only visible when using USB MIDI input from a PC.

**Fix:** Increase the smoothing window, or accept ±1 BPM as within tolerance for the Valeton GP-50.

---

## 5. ConsoleWriter slows main loop at high BPM

**Status:** Present (test/debug only)
**Impact:** Low — affects console debug output, not production

Printing MIDI messages to the USB CDC serial console takes ~5ms per print. At high BPM (>180), this delays the main loop enough to miss some clock bytes, causing inaccurate BPM readings in console output mode.

Does not affect UART output (production path) which writes at 31250 baud (~1ms per message).

**Fix:** Use `"writer": "uart"` (default) for accurate timing. ConsoleWriter is for debugging at moderate tempos only.

---

## Resolved

### BLE MIDI on Pico W (partially resolved)

MicroPython's BTstack could not pair with iOS (security manager not exposed). Ported to CircuitPython which has `adafruit_ble_midi` with iOS pairing support, but CircuitPython's `_bleio` module does not yet support the Pico W's CYW43 chip (`_bleio.adapter` is `None`). BLE MIDI works on CircuitPython boards with native BLE (nRF52840).

**Status:** BLE MIDI on Pico W requires either CircuitPython CYW43 BLE support (open feature request) or a Rust rewrite using Embassy + TrouBLE.

### USB MIDI module missing (resolved by CircuitPython port)

MicroPython's standard Pico W firmware did not include the `usb.device.midi` module needed for USB MIDI.

**Resolution:** CircuitPython includes the `usb_midi` module built-in. Verified working with REAPER at 120-240 BPM.
