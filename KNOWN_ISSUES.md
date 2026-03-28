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

## 4. Clock jitter from fixed poll delay

**Status:** Present in `main.py`
**Impact:** Medium — degrades tempo accuracy

`time.sleep_ms(1)` in the main loop adds up to 1ms of latency per iteration. At 120 BPM the CLOCK tick interval is ~20.8ms, so each sleep can add ~5% jitter per tick. This worsens at higher BPM.

**Fix:** Remove the sleep and poll as fast as possible, or switch to interrupt-driven UART reading (if supported by MicroPython on RP2040) to decouple timing from the poll loop.
