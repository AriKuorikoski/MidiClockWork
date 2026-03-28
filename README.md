# MidiClockWork

A MIDI router and event processor built on Raspberry Pi Pico WH (RP2040 + WLAN), using MicroPython.

## Purpose

MidiClockWork sits between a MIDI source and one or more MIDI outputs. It:

- **Routes** all incoming MIDI data to one or more outputs in parallel
- **Filters** MIDI messages per output — each output can independently pass or block messages by type (clock, CC, PC), channel, or other criteria
- **Processes events** via an event handler system — register callbacks for MIDI events such as tempo changes

The original use case: translate MIDI clock from a Boss MS-3 into tempo CC commands for a Valeton GP-50, which doesn't understand MIDI clock natively.

## Hardware

- Raspberry Pi Pico WH (RP2040 + WiFi/Bluetooth)
- MIDI source (e.g. Boss MS-3)
- One or more MIDI targets (e.g. Valeton GP-50)
- 3.5mm TRS MIDI cables

## Development

- **Language:** MicroPython
- **IDE:** VS Code with Wokwi extension (emulator)
- **Debug:** Serial console (REPL)
- **Emulator:** Wokwi (for development without hardware)

## Quick start

```
python -m pip install pytest
python -m pytest tests/ -v
```

## Documentation

- [Architecture & message flow](docs/architecture.md)
- [Development setup](docs/setup.md)
- [Circuit schematic](docs/schematic.md)
- [Bill of materials](docs/bom.md)
- [Known issues](KNOWN_ISSUES.md)
